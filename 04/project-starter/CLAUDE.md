# Chat Server — Project Conventions

## API Contract

See `api-definition.yaml` at project root for exact field names, types, required flags, and error codes for every REST endpoint.

**Do NOT use code generation from this file.** Read it as the authoritative reference when writing DTOs and controllers by hand. Field names are camelCase. Error responses always use `{ "error": "ERROR_CODE" }`.

STOMP event schemas (MessageEvent, MemberEvent, RoomEvent, PresenceEvent, NotificationEvent) are also defined there as `Stomp*` schemas — use them as the Kotlin class contracts.

---

## Stack

- **Backend:** Kotlin + Spring Boot 3.x, Gradle (Kotlin DSL), Spring WebSocket (STOMP), Spring Security 6, Spring Data JPA, Flyway
- **Frontend:** React 18 + Vite + TypeScript + TailwindCSS + `@stomp/stompjs` + SockJS
- **Database:** PostgreSQL 16
- **Email:** MailHog (SMTP on :1025, web UI on :8025)
- **Deployment:** Docker Compose — four services: `frontend`, `backend`, `postgres`, `mailhog`

## Build and Run Commands

```bash
# Backend
./gradlew build -x test        # compile only
./gradlew test                  # run all integration tests
./gradlew bootRun               # run backend locally (port 8080)

# Frontend
npm install                     # install dependencies
npm run dev                     # dev server (port 5173)
npm run build                   # production build

# Docker
docker compose up -d            # start all services
docker compose ps               # check status
docker compose logs -f backend  # tail backend logs
docker compose down             # stop all services
docker compose down -v          # stop and delete volumes (wipes DB)
```

## Vertical Slice Rule

**Never start a new slice until all tests for the current slice pass.**

Each slice delivers:
1. Flyway migration (new file, never edit existing ones)
2. Kotlin JPA entity + repository
3. Spring Boot endpoint (REST or STOMP handler)
4. Integration tests (Testcontainers + real PostgreSQL)
5. React component or page (Slice 11 only: all UI)

Run `/test-slice` after implementing each slice. If any test fails — **stop, do not write more code, do not move to the next slice**. Fix failures and re-run `/test-slice`. Only `git commit` after the gate clears.

> **Note:** `./gradlew` requires the Gradle wrapper to be initialized. In Slice 1 (project scaffold), run `gradle wrapper` first to generate the `gradlew` script before any other Gradle commands.

## Testing Conventions

- All backend tests: `@SpringBootTest(webEnvironment = RANDOM_PORT)` + Testcontainers
- Shared `PostgreSQLContainer` via `@TestConfiguration` + `DynamicPropertySource` — started once per suite
- **Never use `@Transactional` rollback in integration tests.** In `@SpringBootTest(webEnvironment = RANDOM_PORT)`, the test client runs in a different thread from the server. Transactions commit before the test sees the response — `@Transactional` does not roll back. Use explicit `@AfterEach` cleanup instead:
  ```kotlin
  @AfterEach
  fun cleanup() {
      messageRepository.deleteAll()
      roomRepository.deleteAll()
      userRepository.deleteAll()
  }
  ```
- WebSocket tests: use `StompClient` with a real STOMP connection to `localhost:{port}/ws`

## Key Gotchas (Captured During Design)

### Spring Security + STOMP
Use `ChannelInterceptor` (not `HandshakeInterceptor`) to validate JWT for `@MessageMapping` handlers.
`HandshakeInterceptor` sets the principal at HTTP upgrade time but does NOT bind it to `SecurityContextHolder` used by the message handling thread in Spring Security 6.

### Presence Map Concurrency
The presence map is written from the WebSocket event thread and read by the heartbeat scheduler on a separate thread. Must be:
```kotlin
ConcurrentHashMap<Long, ConcurrentHashMap<String, Instant>>()
```
Plain `HashMap` produces data races.

### React STOMP — Stale Closure
Always use the functional update form when appending messages:
```typescript
setMessages(prev => [...prev, event.message])  // correct
setMessages([...messages, event.message])       // WRONG — stale closure
```

### React STOMP — Client Lifecycle
```typescript
const clientRef = useRef<Client | null>(null)
useEffect(() => {
  const client = new Client({ ... onConnect: () => {
    // ALL subscriptions must be inside onConnect — fires on every reconnect
    client.subscribe('/user/queue/presence', handler)
  }})
  clientRef.current = client
  client.activate()
  return () => { client.deactivate() }
}, [])  // empty deps — create once
```
Subscriptions registered outside `onConnect` are silently dropped after reconnect.

### React STOMP — Subscription Scoping
- Presence (`/user/queue/presence`) and notifications (`/user/queue/notifications`) → `StompProvider` context at app root level, subscribed once at login
- Room messages (`/topic/room.{id}`) → inside the room component, subscribed on mount

If subscribed per room navigation, changing rooms accumulates duplicate subscriptions → double event delivery.

### Flyway Migrations
Never edit a migration file after first `docker compose up`. Flyway detects checksum mismatches and refuses to start. Schema changes during development always require a new numbered file (`V002__`, `V003__`, etc.).

### File Upload Security
Use Apache Tika to validate MIME type from magic bytes — do not trust `Content-Type` header from client. Store files at `uploads/{roomId}/{uuid}` only — no original filename in the storage path.

### Unread Count Upsert
Use a single `INSERT ... ON CONFLICT DO UPDATE` with a `MAX(id)` subquery — never read then write:
```sql
INSERT INTO room_read_cursors (room_id, user_id, last_read_message_id, updated_at)
VALUES (:roomId, :userId,
        (SELECT MAX(id) FROM messages WHERE room_id = :roomId AND deleted_at IS NULL), NOW())
ON CONFLICT (room_id, user_id)
DO UPDATE SET last_read_message_id = EXCLUDED.last_read_message_id, updated_at = NOW()
```

### nginx WebSocket Proxy
nginx requires explicit headers for WebSocket upgrades — without them connections are silently dropped:
```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
proxy_read_timeout 3600s;
```

### Docker Compose Startup Order
Backend must declare a health-check dependency on postgres — Docker Compose does not wait for readiness otherwise and Flyway crashes:
```yaml
depends_on:
  postgres:
    condition: service_healthy
```

### MailHog Port
Spring Boot defaults to SMTP port 25. Must set explicitly:
```yaml
spring.mail.host: mailhog
spring.mail.port: 1025
```

## Troubleshooting

**Backend fails to start with Flyway checksum mismatch:**
A migration file was edited after first run. Reset and re-run:
```bash
docker compose down -v && docker compose up -d
```

**WebSocket connections drop after 60 seconds:**
nginx `proxy_read_timeout` is too low. Must be set to `3600s` in the nginx WS location block (see nginx gotcha above).

**Tests fail with "connection refused" in Testcontainers:**
Testcontainers is slow to start on first run. Increase the wait timeout in the shared container configuration, or run `docker pull postgres:16` before the first test run to pre-cache the image.

**`./gradlew` not found:**
Run `gradle wrapper` in the project root to generate the wrapper. Requires Gradle installed locally, or use `docker run --rm -v "$(pwd)":/project -w /project gradle:8 gradle wrapper`.

**MailHog not receiving emails:**
Check `spring.mail.host=mailhog` and `spring.mail.port=1025` are set in `application.yml`. Default port is 25, which will fail silently.

## Discovered Gotchas

### STOMP Principal Is Bound at CONNECT Time — No Per-Message Re-validation
Spring's `ChannelInterceptor` runs only on the `CONNECT` frame. The principal set there is stored in the STOMP session and reused for every subsequent `@MessageMapping` call — the JWT is NOT re-read on each message. This means:
- If the access token expires during an active session, `@MessageMapping` handlers continue executing with the original principal (the session is still "authenticated" from Spring's view).
- The server-side `sessions` table is NOT checked per STOMP message — only on CONNECT.
- **Mitigation:** The React client proactively refreshes before expiry (see JWT polling gotcha below). The 15-minute access token window is intentionally short to limit exposure.
- **Do NOT add per-message token validation** — it would require re-reading cookies on every STOMP frame, which STOMP's transport does not support cleanly.

### JWT Access Token Refresh — React Polling Pattern
The React client must proactively refresh the access token before it expires. Parse the `exp` claim from the JWT (decode without verify — it's in a cookie, not JS-accessible directly; use a `/api/auth/me` endpoint or embed expiry in the login response body). Schedule a `setTimeout` to call `POST /api/auth/refresh` ~30 s before expiry. On success, reschedule for the new token's expiry. On failure, call `client.deactivate()` and redirect to login.

Do NOT rely on intercepting 401 responses to trigger refresh — by the time a 401 arrives on a STOMP `@MessageMapping` handler, the WS session is already unauthenticated and cannot be silently recovered.

### DM Ban → Read-only UI
When the server pushes `NotificationEvent { type: DM_BANNED }` to `/user/queue/notifications`, the React client must:
1. Unsubscribe from the DM room's `/topic/room.{id}` topic
2. Disable the message compose input and send button for that room
3. Keep the message history visible (both parties retain read access per spec)

The ban enforcement is also server-side (403 on `chat.send`), but the UI must handle it without waiting for a rejected message attempt.

### Room Deletion — File Cleanup Order
Delete files from disk **before** deleting the room row. If disk deletion throws, do NOT delete the room row — abort and return 500. This prevents DB references with no corresponding files.

```kotlin
// Correct order:
attachmentRepository.findAllStoragePathsByRoomId(roomId).forEach { path ->
    Files.deleteIfExists(uploadsDir.resolve(path))  // throws on error — do NOT catch silently
}
roomRepository.deleteById(roomId)  // cascade removes all child rows
```

Orphaned files on disk (DB row deleted but file remains) are preferable to orphaned DB references. A background scan can clean disk orphans later.

### Multi-tab Logout — Intentional Per-Session Invalidation
`POST /api/auth/logout` invalidates only the session token in the current request's cookie. Other browser tabs remain valid. This is correct per Requirement 2.2.4 ("logout from current browser only; other sessions remain valid"). Do not attempt to push a disconnect event to other tabs on logout — this is by design.
