# Solution Design Framework Analysis — Reinsurance Reconciliation Platform

**Type:** AI-assisted Framework Analysis
**Author:** Tomasz Mosur
**Date:** 2026-04-26
**Subject:** Structured review of the solution design across seven established frameworks

---

## Framework 1: AWS Well-Architected Review

### Operational Excellence

**What the design does well.** Phase gates with explicit pass/fail criteria are a strong operational discipline — the Phase 2→3 gate requires a full staging cycle end-to-end before any counterparty UAT. The counterparty onboarding runbook (7-step procedure) is one of the few procedural artefacts that approaches runbook quality. The weekly `audit-verify` Lambda and monthly full-chain sweep are defined operational rhythms.

**What is missing.** No alerting matrix exists anywhere in the design. CloudWatch is listed as an OPEX line item but no metrics, alarm names, or thresholds are defined. The deployment strategy is entirely absent — neither the artefact pipeline, nor the deployment mechanism for Lambda functions and infrastructure, nor a rollback procedure appears in the document. The Aurora Serverless v2 minimum ACU floor (0.5 ACU) is justified for cold-start mitigation but is never connected to a concrete pre-warming schedule: the Risks table mentions "pre-warming Lambda 1 hour before month-end" as a mitigation, but no operational procedure defines who triggers it, via what mechanism, and on what calendar.

The five RBAC roles are named ("spanning reinsurer, counterparty, compliance, and platform administration") but never defined. There is no table mapping role → permission → API endpoint. Operationally, this means the team has no specification to test against.

**Recommendation.** Define a component-to-alert matrix: for each named component (API Lambda, Eligibility Lambda, Aurora, Step Functions, `audit-verify` Lambda, SES), list the failure mode, the specific CloudWatch metric or log filter, the alarm threshold, and the on-call action. Example: Eligibility Lambda `Errors > 0` in a 5-minute window → alert → check Step Functions execution for `AWAITING_ELIGIBILITY` states older than 30 minutes → page on-call engineer. Without this matrix, the observability section is aspirational infrastructure, not an operational capability.

---

### Security

**What the design does well.** The INSERT-only DB role for the audit schema is correctly implemented and explicitly documented. The `SET LOCAL` approach for RLS context (ADR-002) correctly names and mitigates the connection-pool session variable leakage risk. Three-layer audit logging (CloudTrail, database statement logging, application audit ledger) is a sound defence-in-depth posture. KMS CMK dedication to audit-critical data is mentioned.

**What is missing.** The IAM role scope for the Eligibility Engine Lambda is unspecified. The design states the Lambda reads contract rules and cycle files — which means it needs at minimum: `aurora:Connect`, S3 `GetObject` on the file store bucket, and `kms:Decrypt` on the audit CMK. Whether it also has `s3:PutObject` write access (to write results back) is not specified. An overly permissive Lambda execution role on the eligibility engine is a realistic IAM misconfiguration at build time.

The break-glass mechanism is documented at a one-sentence level ("superuser access requires documented procedure with alerting; all access logged") but the mechanism is not specified. There are two materially different options — AWS Systems Manager Session Manager with an SSM document that logs to CloudWatch, or a direct psql connection via an EC2 bastion. The operational and security properties differ substantially. SSM Session Manager leaves a session audit trail in CloudTrail and can be revoked via IAM; a bastion host can have its SSH key cached on an engineer's laptop. The design should specify which mechanism is used.

No data classification table exists. The design references PII handling in the GDPR compliance gap section (actor names stored in `users`, UUIDs in audit events) but there is no table mapping each data entity to a classification tier (PII / sensitive financial / non-sensitive operational), the encryption approach for that tier, access logging requirements, and the applicable retention policy. Without this table, the security engineer building the KMS key policies and S3 bucket policies has no specification.

**Recommendation.** Add a data classification table covering at minimum: `users.email`, `users.name` (PII — anonymise on erasure request), `eligibility_results.compensation_amount` (sensitive financial — encrypted at rest, access logged), `audit.events.payload` (sensitive financial + potential PII reference — INSERT-only role, no direct SELECT by API Lambda), S3 file objects (PII-containing — KMS SSE, access logging enabled). This table drives encryption granularity decisions, S3 bucket policies, and the break-glass access boundary.

---

### Reliability

**What the design does well.** Aurora Serverless v2 Multi-AZ is correctly specified for RPO = 0 on AZ failure. The idempotent file ingestion design (unique constraint on `(cycle_id, file_type)`, HTTP 409 on duplicate) prevents duplicate audit events. The 72-hour escalation timer on approval steps is documented.

**What is missing.** There is no retry or backoff policy on any Lambda invocation in the design. Step Functions Standard Workflows have configurable `Retry` fields on task states — these are not specified. If the Eligibility Engine Lambda fails transiently (Aurora connection timeout, ENI attachment delay), the Step Functions state transitions to `FAILED` with no retry. This is a silent failure: the cycle stays in `AWAITING_ELIGIBILITY` indefinitely. The design mentions "alert on any cross-tenant query" but there is no alert defined for a cycle stuck in `AWAITING_ELIGIBILITY` for more than N hours.

There is no Dead Letter Queue defined for any Lambda function. If the `audit-verify` Lambda fails silently (Lambda service error, not a chain integrity error), the compliance team receives no alert and the weekly sweep silently does not run.

The ALB health check configuration is not applicable here (API Gateway → Lambda, not ALB). But the equivalent question — what is the Lambda health check? — has no answer. API Gateway has no equivalent to an ALB target group health check. If the API Lambda is broken (bad deployment, missing environment variable), API Gateway returns 502/503. There is no pre-traffic check in the deployment strategy to catch this — because the deployment strategy is unspecified.

**Recommendation.** Add Step Functions retry configuration on the eligibility task state: `MaxAttempts: 3`, `IntervalSeconds: 30`, `BackoffRate: 2`, catching `Lambda.ServiceException`, `Lambda.AWSLambdaException`, and `Lambda.TooManyRequestsException`. Add a DLQ on the `audit-verify` Lambda with an SNS notification on message arrival. Add a CloudWatch alarm on cycles where `workflow_status = 'AWAITING_ELIGIBILITY'` for more than 60 minutes.

---

### Performance Efficiency

**What the design does well.** Aurora Serverless v2 auto-scaling with a defined ACU range (0.5–8 ACU) matches the monthly-peak workload. Lambda pay-per-invocation aligns cost with actual usage. The pre-signed URL approach for file uploads offloads S3 throughput from the API Lambda correctly.

**What is missing.** Peak load — 20 concurrent counterparties, each submitting multiple file types — is documented as a requirement but the system's response to this load is not modelled. At 20 concurrent submissions each triggering eligibility calculations: how many concurrent Lambda invocations does the eligibility engine produce? How many Aurora connections does that require? At 8 ACU maximum, Aurora PostgreSQL-compatible supports approximately 90 connections per ACU = 720 connections. With 20 concurrent eligibility Lambda invocations plus concurrent API Lambda invocations plus portal sessions, the connection count under peak load is not modelled. The architecture review noted this gap; the solution design has not addressed it.

Lambda memory sizing for the eligibility engine is not specified. Lambda memory controls both RAM and CPU allocation — for a compute-intensive expression tree evaluation over 100K individual records, the difference between 512MB and 3008MB Lambda allocation is a 6x throughput difference and a significant cost difference.

**Recommendation.** Add a peak load model: 20 concurrent eligibility Lambdas x N connections per Lambda = X connections against Aurora at 8 ACU. If X approaches the 720-connection ceiling, specify RDS Proxy with transaction-pinning mode (compatible with `SET LOCAL` RLS as documented in the architecture review). Run the month-end load test (already listed in the testing approach) before Phase 3 go-live and define pass/fail criteria — currently the test is listed but has no acceptance threshold.

---

### Cost Optimization

**What the design does well.** `financials.py` as the single source of truth for all cost figures is the right approach. Aurora Serverless v2 scaling to 0.5 ACU between peaks is an appropriate cost floor for a monthly-peak workload.

**What is missing.** The cost model in `financials.py` is calibrated to 15 counterparties. S3 10-year raw file storage cost appears nowhere in the OPEX table. If each counterparty submits 5 file types per month averaging 10MB each, that is 15 × 5 × 12 × 10 = 9,000 files × 10MB = 90GB after Year 1. S3 Standard at $0.023/GB = ~$2/month; S3 Glacier Deep Archive at $0.00099/GB after tiering = negligible. Neither figure appears in the OPEX table.

The Aurora Serverless v2 ACU floor between monthly cycles (0.5 ACU, ~$50/month) is justified but not validated. Aurora Serverless v2 does not scale to zero — the actual consumption at idle may be higher than 0.5 ACU if pgaudit, RLS, and background vacuum processes hold connections. This should be measured in staging, not assumed.

**Recommendation.** Add S3 long-term file storage as a line item in `financials.py`. Model three tiers: S3 Standard (0–90 days), S3-IA (90 days–1 year), S3 Glacier Deep Archive (1–10 years). Validate the Aurora idle ACU floor empirically in staging before committing to the OPEX estimate.

---

### Sustainability

**What the design does well.** Aurora Serverless v2 scales to 0.5 ACU between peaks. Lambda scales to zero between invocations. Monthly-batch cadence minimises always-on compute.

**What is missing.** S3 Intelligent-Tiering is not mentioned for the file store. The design mentions "records >3 years old migrated to S3 Glacier" as a lifecycle policy but the mechanism (S3 lifecycle rule vs. manual job) is not specified.

**Recommendation.** Define the S3 lifecycle rule explicitly in Terraform: transition to S3-IA at 90 days, Glacier Instant Retrieval at 1 year, Glacier Deep Archive at 3 years. This is a one-line Terraform resource with no operational overhead and a meaningful long-term storage cost reduction.

---

## Framework 2: STRIDE Threat Model

### Counterparty File Upload Boundary (S3 Pre-Signed URL)

| Threat | Current mitigation | Gap |
|---|---|---|
| **Spoofing** — counterparty A obtains a pre-signed URL intended for counterparty B | Pre-signed URL scoped to a tenant-specific S3 prefix; generated after JWT validation | Pre-signed URL expiry window is not specified. A URL with a 24-hour expiry leaks far more than one with a 15-minute expiry. Specify a maximum expiry of 15 minutes for upload URLs. |
| **Tampering** — counterparty alters the file after S3 write but before eligibility is triggered | SHA-256 checksum stored in `cycle_files` at ingestion | Raw received file is stored in S3 but it is unclear whether it is stored under Object Lock. The `cycle_files.sha256_checksum` is stored in mutable PostgreSQL — a superuser could alter both the checksum and the file pointer. Raw files should be stored in an Object Lock-protected bucket or at minimum with versioning and deletion protection, so the counterparty cannot later claim the system altered their submission. |
| **Repudiation** — counterparty denies having uploaded a specific file | `FileReceived` audit event with file SHA-256 and `cycle_id` | The `FileReceived` event must link to the Cognito `sub` claim (not just the internal `actor_id`). If the `users` record is anonymised under a GDPR erasure request, the audit event loses its non-repudiation link. Store the Cognito `sub` as an immutable field in the audit event payload alongside `actor_id`. |
| **Information Disclosure** — pre-signed URL intercepted by a third party | TLS in transit; URL is time-limited | No mitigation for URL interception via browser history or proxy logs. The pre-signed URL should not be embedded in notification emails; it should be generated and immediately consumed within the portal session. |
| **DoS** — counterparty submits a large malformed file designed to consume maximum eligibility engine CPU | WAF rate limiting at CloudFront | No per-tenant processing time limit is specified for the eligibility Lambda. A malformed file triggering pathological expression tree evaluation could hold a Lambda invocation for the full 15-minute timeout. At 20 concurrent submissions this could exhaust the Lambda concurrency limit. Specify a maximum file size threshold rejected at the API layer before S3 write, and a per-invocation timeout on the eligibility task state in Step Functions (distinct from the Lambda function timeout). |
| **Elevation of Privilege** — counterparty manipulates file type tag to inject into a different contract's cycle | File type validated at API layer before S3 write | Validation is described but not schema-enforced. Confirm the API Lambda rejects a file type not listed in `contract_file_types` for that `contract_id`, not just any valid enum value. |

---

### Portal Authentication (Cognito)

| Threat | Current mitigation | Gap |
|---|---|---|
| **Spoofing** — attacker impersonates a counterparty admin | Cognito MFA enforced for all users | MFA enforcement can be `OPTIONAL`, `REQUIRED` (pool policy), or enforced via a Pre-Authentication Lambda trigger. `REQUIRED` at pool level is the correct Terraform setting; confirm this is how it is configured. |
| **Repudiation** — internal user denies approving a cycle | `ApprovalGranted` audit event with `actor_id` | For SAML-federated internal users, the Cognito `sub` is a federated identifier that may change if the corporate IdP is migrated. The audit event should capture the `email` claim from the JWT at the time of approval — stored in the immutable audit payload, not only resolvable via the mutable `users.email`. |
| **Elevation of Privilege** — a counterparty user self-assigns `INTERNAL` role claim | `custom:user_type` claim in JWT; internal users are SAML-federated | The API Lambda should additionally validate that `INTERNAL` claim holders have a SAML-federated token (visible via the `identities` attribute in the Cognito JWT) and not a Cognito-native credential. A Cognito admin error could misconfigure a native user with an `INTERNAL` claim. |

---

### Eligibility Engine (Lambda)

| Threat | Current mitigation | Gap |
|---|---|---|
| **Information Disclosure** — engine error response leaks contract rule structure to counterparty | Error handling not specified | If the eligibility engine returns a stack trace or error containing the contract rule JSONB, and this propagates to the portal API response, commercially sensitive contract terms are exposed. Define a policy: eligibility engine errors produce a generic `ELIGIBILITY_FAILED` event; detailed context goes to CloudWatch only. |
| **Tampering** — attacker with contract registry write access modifies rules to alter eligibility outcomes | Contract upload validated against versioned JSON Schema | If the API Lambda execution role can both write eligibility results and write contract rule updates, a compromised Lambda could alter contract rules and trigger a recalculation within the same IAM identity. Separate contract registry write permission into a dedicated IAM role requiring explicit assumption. |
| **Repudiation** — vendor claims a different engine version was used for a calculation | `eligibility_results` records `engine_version` | Correctly addressed. No gap. |

---

### Approval Workflow (Step Functions)

| Threat | Current mitigation | Gap |
|---|---|---|
| **Repudiation** on approval action | Audit event per approval step | The approval callback endpoint calls `SendTaskSuccess` with the task token from the request body. Confirm the endpoint re-validates the caller's JWT and checks that the caller's `tenant_id` and `role` match the expected approver *before* calling `SendTaskSuccess`. A leaked task token (e.g. from CloudWatch logs) could trigger approval without authentication. |
| **Elevation of Privilege** — L1 approver skips L2 threshold requirement | L2 threshold check in Step Functions state machine | Confirm the threshold check is a Step Functions `Choice` state reading the `compensation_amount` directly from the state input, not from an API-provided flag. If the check lives in application code that generates Step Functions input, an application bug can bypass L2. |

---

### Audit Ledger

| Threat | Current mitigation | Gap |
|---|---|---|
| **Tampering** — superuser modifies audit rows and recomputes hash chain | Weekly `audit-verify` Lambda; KMS genesis anchor | A motivated insider with superuser access and knowledge of the SHA-256 algorithm (documented in the solution design) can modify post-genesis events and recompute the chain forward without detection. The `audit-verify` Lambda can be disabled by an IAM-privileged operator. This is the unresolved core gap from prior reviews. |
| **Repudiation** — compliance team cannot confirm when the last verification sweep ran | `audit-verify` Lambda alerts on violation | Clean sweep runs are not recorded as audit events. An auditor asking "when was the last successful verification?" must search CloudWatch logs, not query the audit ledger. Write a `CHAIN_VERIFIED` audit event on every clean sweep run, including a timestamp and event count verified. |

---

### Break-Glass Access

| Threat | Current mitigation | Gap |
|---|---|---|
| **Elevation of Privilege** | "Documented procedure with alerting; all access logged" | CloudTrail logs AWS API calls but not SQL statements issued during a direct DB session. Confirm pgaudit is enabled on Aurora for `write` and `ddl` operations and that the CloudWatch log group has deletion protection (via a resource policy preventing the operational team from deleting it). |
| **Tampering** during break-glass | Hash chain violation within 7 days | No procedure exists to distinguish a legitimate break-glass correction from a malicious modification. Define: (a) break-glass writes to `audit` schema are explicitly prohibited — corrections go to operational tables only; (b) if an audit schema correction is unavoidable, it requires sign-off from two senior officers, and the `audit-verify` Lambda is run immediately with the result archived as evidence. |

---

## Framework 3: FMEA — Failure Mode and Effects Analysis

| # | Failure mode | Effect | Detection | Current mitigation | Residual risk |
|---|---|---|---|---|---|
| 1 | **Partial file transfer** — S3 multipart upload completes but file is internally truncated (e.g. truncated CSV); eligibility triggered on partial data | Eligibility computed against fewer individuals than submitted; wrong compensation amount approved and signed off | None at eligibility trigger time; manifest only in post-hoc comparison with counterparty records | SHA-256 checksum on received bytes; cycle readiness check on file types | The SHA-256 matches the truncated file — the checksum cannot detect truncation against an expected record count. The eligibility engine must validate record counts against a prior-month baseline. No such validation is specified. **High residual risk.** |
| 2 | **Aurora connection exhaustion at month-end** — 20 concurrent eligibility Lambda invocations each holding a connection; ACU ceiling reached | All subsequent eligibility tasks fail with connection timeout; cycles stuck in `AWAITING_ELIGIBILITY`; no month-end processing completes | CloudWatch `DatabaseConnections` metric (if alarmed) | Lambda provisioned concurrency (API function only); Aurora Serverless v2 auto-scales ACU | Connection ceiling at 8 ACU = ~720 connections. Peak load connection count not modelled. No RDS Proxy specified. No alarm on `DatabaseConnections > 600`. **Medium residual risk** — unlikely at 15 counterparties but triggered at 30+. |
| 3 | **S3 Object Lock misconfiguration** — audit bucket configured with Governance mode instead of Compliance mode, or no Object Lock at all | A superuser or root account can delete objects within retention period; Solvency II Art. 259 compliance guarantee breaks silently | Discovered only at regulatory examination or an explicit config audit | Not mitigated — no S3 Object Lock is specified in the current design; the audit ledger relies entirely on the PostgreSQL hash chain | **High residual risk** — a one-time setup error with 10-year compliance implications. No S3 Object Lock = no tamper-impossible guarantee. |
| 4 | **Eligibility engine silent wrong result** — a date edge case (leap year, fiscal year boundary, timezone) miscategorises an individual | Wrong compensation amount approved and counter-signed; financial loss; regulatory exposure if discovered in audit | Not detectable within the platform; manifest only in external actuarial review | Regression tests against 12 months of historical Excel output | Regression tests cover historical cases, not unrepresented edge cases. No anomaly detection on compensation amounts (e.g. deviation from prior month). **Medium residual risk.** |
| 5 | **Approval escalation timer fires but SES delivery fails** — 72-hour escalation email bounces or is rejected | Cycle stuck in `REINSURER_REVIEW` or `COUNTERPARTY_SIGN` state indefinitely; no human is aware; month-end deadline missed | None within the current Phase 2–3 design | SES is the only notification path; bounce handling is not specified | The Step Functions timer fires regardless of SES delivery. No second notification path exists until the Phase 4 in-app notification feed. No CloudWatch alarm on cycles in a single state for more than 72 hours. **High residual risk** at go-live. |
| 6 | **Superuser break-glass write to audit table** — corrective SQL UPDATE on `audit.events` during incident response | Hash chain break detected by `audit-verify` Lambda within 7 days; compliance alert triggered | Weekly `audit-verify` Lambda (up to 7-day window) | INSERT-only application role; break-glass procedure documented | 7 days is sufficient time to complete a month-end cycle and submit a regulatory filing based on tampered records. The mitigation is detective, not preventive. Without S3 Object Lock there is no independent copy. **High residual risk.** |
| 7 | **KMS CMK rotation breaks genesis anchor verification** — `audit-verify` Lambda calls KMS `Verify` against the current key version; tenants provisioned before last rotation have genesis anchors signed by an older key version | Verification Lambda reports `CHAIN_VIOLATION_DETECTED` for all pre-rotation tenants; compliance alert floods; team cannot distinguish false positive from genuine tampering | `audit-verify` SNS alert | KMS automatic rotation retains old key versions for decryption | AWS KMS `Verify` does not automatically try previous key versions (unlike `Decrypt`). Unless the verification Lambda stores and passes the explicit key version ARN from the genesis event payload, it will fail after any rotation. The solution design does not address this. **High residual risk** — first CMK rotation after go-live triggers false positive chain violations for all tenants. |
| 8 | **Cognito outage during month-end submission window** — Cognito User Pool unavailable for 30–60 minutes | All portal logins fail; counterparties cannot upload files; reconciliation managers cannot approve; month-end processing halts | Cognito service health dashboard | Single Cognito User Pool; no documented fallback authentication path | Cognito SLA is ~99.9%. A 1-hour outage in a month = 0.14% downtime. No manual fallback exists for portal-dependent workflows. SFTP fallback covers file submission only for Tier 3 counterparties. **Medium residual risk** — contradicts the 99.9% monthly uptime NFR during peak windows. |

---

## Framework 4: Production Readiness Review

| Area | Status | Gap |
|---|---|---|
| **Metrics defined** | Fail | No CloudWatch metrics are named anywhere in the design. CloudWatch appears as an OPEX line item but no metric names, dimensions, or custom metrics (e.g. `cycles_in_awaiting_eligibility`, `audit_events_written_per_tenant`) are defined. |
| **Structured JSON logs** | Partial | Three audit logging layers are specified but the application log format is not. Without structured JSON with a mandatory `cycle_id` field on every log line, CloudWatch Logs Insights queries against concurrent month-end cycles are impractical. The YAGNI analysis correctly identifies correlation ID propagation as non-negotiable, but the log format specification that makes it queryable is absent. |
| **X-Ray tracing** | Fail | Not mentioned. For Lambda + Step Functions + Aurora, X-Ray is the standard mechanism for identifying latency contributors. Without it, debugging a slow month-end eligibility cycle at 2am requires correlating Lambda logs with CloudWatch metrics by hand. |
| **Dashboards** | Fail | None defined. A minimum month-end operations dashboard should show: active cycles by state, eligibility Lambda error rate, Aurora connection count, Step Functions execution success/failure rate, SES delivery success rate. |
| **Every SLA metric covered by an alert** | Fail | Three SLA metrics exist: 99.9% monthly uptime, RTO < 1 hour, eligibility < 15 minutes. None has a named CloudWatch alarm. The 15-minute eligibility SLA has no corresponding Lambda duration alarm or Step Functions wait-time alarm. |
| **Alerts are actionable** | Fail | No alerts are defined. Cannot be evaluated. |
| **On-call rotation defined** | Partial | The Hypercare section specifies a 24/7 on-call rota for the first month-end window. No on-call structure exists for steady-state operation. No escalation path, no on-call tooling reference, no rotation cadence. |
| **Runbooks for each alert** | Fail | No runbooks exist. The counterparty onboarding runbook is the only procedural document in the design. There is no runbook for: Lambda error spike, Aurora connection exhaustion, hash chain violation, SES delivery failure, Cognito outage, Step Functions execution failure, break-glass access request. |
| **Zero-downtime deployment** | Fail | The deployment strategy is entirely absent. Lambda aliases and weighted traffic shifting, Aurora schema migration procedure, CI/CD pipeline tooling (SAM / CDK / Terraform) — none specified. |
| **Rollback under 10 minutes** | Fail | No rollback procedure is defined. Lambda alias-based rollback can be under 30 seconds if aliases are used, but alias configuration is not specified. |
| **DB migration strategy** | Partial | Phase 1 database migration scripts are listed as a deliverable. No migration strategy is defined: how are migrations applied against a production Aurora instance with live connections? Is there a maintenance window? Are migrations tested against a staging instance at production data scale? |
| **Load test plan** | Partial | The month-end load test is listed in the testing approach and Phase 4 scope but has no pass/fail criteria. A load test without acceptance thresholds is an observation, not a phase gate. Define: P95 eligibility duration < 10 minutes (within the 15-minute SLA with margin), Aurora `DatabaseConnections` peak < 600, zero Lambda throttle errors during the 20-concurrent-submission test. |
| **Performance targets defined** | Partial | The NFR table defines P95 portal < 2s, P95 API reads < 500ms, eligibility < 15 minutes. These are defined but not connected to specific load test scenarios or CloudWatch alarms. |
| **Cognito outage fallback** | Fail | Not documented. No fallback path for portal-authenticated workflows (approval, counter-signing) if Cognito is unavailable. |
| **SES outage fallback** | Fail | Not addressed. Approval escalation timers fire regardless of SES delivery. The in-app notification feed is a Phase 4 enhancement — not present at go-live. |
| **KMS outage fallback** | Fail | Not addressed. KMS unavailability affects: new tenant genesis anchor creation, audit chain verification on sealed-cycle read, and potentially S3 SSE-KMS file decryption. The design should specify which operations degrade gracefully (read-only mode with a cached key) vs. which require KMS availability. |
| **Secrets Manager DB credential rotation** | Fail | Not specified. Neither Aurora IAM authentication (no long-lived credential) nor Secrets Manager automatic rotation is documented. No rotation procedure under an incident scenario exists. |

---

## Framework 5: Evolutionary Architecture — Fitness Functions

These are automated checks that fail if the architecture drifts from its intended properties. Each is defined as a concrete, runnable test.

| Property | Measurement | Implementation | When it runs |
|---|---|---|---|
| **Tenant isolation** | Integration test authenticates as Tenant A JWT, then attempts GET on cycle IDs, eligibility results, and audit events belonging to Tenant B (pre-seeded). Test fails if any 200 response is returned. | JUnit/pytest integration test hitting the staging API with two pre-provisioned synthetic tenants. Covers API-layer check and DB-layer RLS. | Every PR against `main`; must pass before merge. |
| **Modular boundary integrity** | ArchUnit (JVM) or `import-linter` (Python) rule: no class/module in `ingestion` imports from `eligibility.internal`; no class in `audit` imports from `approval`. Only published module interfaces may be used across module boundaries. | ArchUnit test suite in the main build. Violations fail the build. | Every PR; part of the standard test run. |
| **Audit completeness** | For every `reconciliation_cycles` row where `workflow_status = 'CYCLE_SEALED'`, verify that `audit.events` contains: `FILE_RECEIVED` (≥1 per required file type), `ELIGIBILITY_COMPUTED`, `APPROVAL_GRANTED` (≥1), `CYCLE_SEALED`. Any sealed cycle missing a required event type is a compliance gap. | Nightly SQL query against production Aurora (read-only role); result posted to CloudWatch custom metric `audit_completeness_violations`. Alarm if metric > 0. | Nightly in production; weekly in staging. |
| **Hash chain integrity** | Extend the existing `audit-verify` Lambda to: (a) recompute each row's `event_hash`; (b) verify the genesis anchor `previous_hash` using the key version ARN stored in the genesis event payload (multi-version KMS `Verify`). Write a `CHAIN_VERIFIED` audit event on every clean sweep. | Extend the `audit-verify` Lambda. Add a CloudWatch alarm if no `CHAIN_VERIFIED` event appears within 8 days (missed sweep). | Weekly in production; on every sealed-cycle read. |
| **Object Lock on audit bucket** | AWS Config managed rule `s3-bucket-object-lock-enabled` evaluates the audit bucket. Custom Config rule verifies mode = `COMPLIANCE` and retention period ≥ 3,650 days. Non-compliant result raises a finding in Security Hub and SNS alert to compliance team. | AWS Config continuous evaluation + custom Lambda evaluator rule. | Continuous; evaluated on every bucket config change and on a 24-hour scheduled basis. |
| **No hardcoded tenant IDs in application code** | Regex/AST scan for UUIDs matching the production tenant ID format in `src/` outside designated fixture directories. Fail if any match found. | Pre-commit hook and CI lint step. Pattern: `[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}`. Exempt: `src/test/fixtures/`, migration seed scripts. | Every commit (pre-commit); every PR (CI). |
| **Correlation ID present on all log lines** | CloudWatch Logs Insights query against the API Lambda and Eligibility Lambda log groups: count log lines where the structured JSON field `cycle_id` is absent and log level is not `DEBUG`. | Scheduled CloudWatch Logs Insights query running daily; result posted to custom metric `uncorrelated_log_lines`. Alarm if metric > 0. | Daily in production. |
| **No direct cross-module DB writes** | ArchUnit rule: `eligibilityResultRepository` may only be called from within `com.example.eligibility`; `auditEventRepository` may only be called from within `com.example.audit`. Direct INSERT from another module's code path fails the test. | ArchUnit rule in the main test build. | Every PR. |

---

## Framework 6: Data Governance Review

### Data Lineage

The design provides enough to trace a cycle from file receipt to sealed audit event: S3 raw file → `cycle_files` row (SHA-256, S3 key) → `eligibility_results` row (engine version, compensation amount, result JSONB) → `audit.events` row (`ELIGIBILITY_COMPUTED` with input file SHA-256 and contract rule version).

The lineage breaks at two specific points.

**Break 1 — Raw file to individual eligibility decision.** The `eligibility_results` table stores an aggregate `compensation_amount` and a result JSONB. Whether the result JSONB contains per-individual eligibility flags is not specified in the data model description. The Solvency II compliance gap section states the `ELIGIBILITY_COMPUTED` payload must include "per-individual eligibility flags" — but this is a proposed future requirement, not a confirmed current design. If the result JSONB stores only aggregate figures, an auditor cannot trace "why was individual X not eligible in cycle C-2026-04?" without re-running the eligibility engine. Re-running requires the engine version, contract version, and raw file to all be available and compatible — an operational capability that is not specified.

**Break 2 — File normalisation step.** The per-counterparty normalisation mapping translates native formats to the platform canonical schema. The normalisation mapping version is not recorded in `cycle_files` or in the `ELIGIBILITY_COMPUTED` audit event. If a mapping is updated because the counterparty changed their file format, historical cycles processed under the old mapping are not reproducible using the current mapping. The `normalisation_mapping_version` must be recorded in `cycle_files` and in the `ELIGIBILITY_COMPUTED` audit event payload.

---

### Data Minimisation (GDPR Art. 5)

The system processes alive/dead status for named insured individuals. Whether this constitutes health data under Art. 9 (special category) is a jurisdiction-specific legal question — mortality status for longevity/pension purposes is arguably financial data about a pension position, not clinical health data. However, the individual-level data in the raw people table files (names, dates of birth, national insurance numbers, alive/dead status) is sensitive PII regardless of classification.

The design does not specify the legal basis for processing this data under GDPR Art. 6. The most likely basis is Art. 6(1)(b) (performance of contract) or Art. 6(1)(c) (legal obligation under Solvency II). The data minimisation question is whether the platform needs to retain raw people table files for 10 years, or only the anonymised eligibility results. The individual-level data in the raw files is far richer than what is needed for actuarial audit purposes. A DPIA addressing this question is not currently in scope for the engagement.

---

### Right to Erasure vs. Solvency II Conflict

The design's resolution — personal identifiers stored in the mutable `users` table, UUIDs in audit events, anonymise `users` on erasure request — correctly handles *platform user* PII (reconciliation managers, counterparty admins).

It does not address the PII of the *insured individuals* in the counterparty files. If an insured individual exercises their GDPR Art. 17 right to erasure, the platform cannot delete their data from a sealed hash-chain-protected audit event or from a 10-year Object Lock-protected S3 archive.

The correct resolution is that Art. 17(3)(b) (where erasure conflicts with a legal obligation) means the 10-year Solvency II retention obligation likely prevails over individual erasure requests for data used in actuarial computations. This must be confirmed by legal counsel and documented in a DPIA. The current design does not acknowledge this conflict for insured individuals.

---

### Data Residency

The primary deployment is eu-west-2 (London) — UK GDPR. The DR region is eu-west-1 (Ireland) — EU GDPR. S3 Cross-Region Replication from eu-west-2 to eu-west-1 transfers data from UK GDPR jurisdiction to EU GDPR jurisdiction.

The UK-EU adequacy decision (in force as of the document date) covers this transfer under Art. 45 UK GDPR. However, the adequacy decision is a political instrument that can be revoked. The design should acknowledge this dependency. If the decision lapses, the eu-west-1 DR replication requires Standard Contractual Clauses or equivalent.

For counterparties with EU-domiciled insured individuals, their PII replicated to eu-west-1 is processed under EU GDPR (not UK GDPR). The Data Processing Agreement with each counterparty must explicitly address this cross-border transfer and the applicable legal mechanism.

---

### Data Classification Table

No data classification table exists in the design. Minimum required:

| Data entity | Classification | Retention | Erasure possible? | Notes |
|---|---|---|---|---|
| `users.email`, `users.name` | PII (platform user) | Duration of engagement + legal minimum | Yes — anonymise on erasure request; UUID remains | Erasure does not break hash chain |
| Raw counterparty people table files (S3) | PII + sensitive financial (insured individuals) | 10 years (Solvency II) | No — Art. 17(3)(b) likely applies; confirm via DPIA | Highest sensitivity; S3 access logging mandatory |
| `eligibility_results.compensation_amount` | Sensitive financial | 10 years | No | Commercial in confidence |
| `audit.events.payload` | Sensitive financial (may include compensation figures) | 10 years | No | INSERT-only; no direct API Lambda SELECT |
| `contracts.rule_json` | Commercially confidential | Duration of contract + 10 years | No | Contains negotiated contract terms |
| CloudWatch logs | Operational (may contain UUIDs cross-referenceable to PII) | 90 days | Via log group retention | Should not contain PII directly |

---

### Retention Enforcement

Object Lock retention period is set at object write time. If the application code calculates retention as `current_date + 10 years` and there is a bug that writes `current_date + 1 year`, the object expires and is automatically deleted after 1 year — with a 1-year latency before discovery.

Mitigation: the AWS Config custom rule (defined in Framework 5) must also verify that the minimum retention period on any object in the audit bucket is ≥ 3,650 days. Objects with a shorter retention window trigger an immediate Security Hub finding.

---

## Framework 7: Integration Contract Review

### Counterparty File Contract

No formal file schema specification exists for any counterparty file type. The Anti-Corruption Layer (per-counterparty normaliser) is correctly named as a pattern in the YAGNI analysis. Its output — the canonical internal format — is never defined or versioned.

Without a versioned canonical schema, the eligibility engine's expected input is implicit in its code. When the engine is updated (new node types, decimal precision changes), there is no contract that defines what the normaliser must produce. Define a versioned JSON Schema for each canonical file type (e.g. `canonical-people-v1.json`). The normaliser validates its output against this schema before handing off to the eligibility engine. The eligibility engine declares which canonical schema versions it accepts in its configuration. Breaking changes require a new version number, not a silent in-place modification.

---

### Counterparty Onboarding Duration

The onboarding runbook has 7 steps. Steps 2–3 (configure normalisation mapping, validate against canonical schema) require a sample file and developer effort to write the mapping. No per-counterparty time estimate appears in the project plan.

Phase 4 shows "Second Counterparty Batch Onboarding" as a 3-week task. If the batch is 5 counterparties, that is 3 days per counterparty for normalisation mapping development, UAT, and sign-off. For a counterparty with a non-standard file format (multi-sheet Excel, fixed-width, nested XML), 3 days is not achievable. The project plan should include a range: simple CSV (2 days), complex format (5–10 days), custom SFTP integration (10–15 days). This affects Phase 4 scope and budget directly.

---

### Silent Format Changes

A counterparty who silently changes their file format produces a `FILE_NORMALISATION_FAILED` error at ingestion — the normaliser cannot map their new columns to the canonical schema. The response process is not specified:

- Who is notified (counterparty, platform admin, both)?
- What is the notification SLA (target: < 15 minutes for platform admin alert, < 1 hour for counterparty notification)?
- Is the file held in a failed state pending mapping remediation, or rejected?
- If the month-end deadline is 24 hours away and the file fails normalisation at 11pm, what is the escalation path?

Define a normalisation failure SLA and a response runbook. This is an operational procedure gap, not an architectural one — but it is precisely the failure mode that causes a month-end crisis.

---

### SES Notification Contract

Approval workflow emails are sent via SES but the email format is not versioned or specified. If a counterparty builds an automated email parser to trigger their internal approval workflow (common in B2B integrations), an unannounced change to the email template breaks their integration without any API version signal.

Define the notification email format as a versioned contract: include a template version identifier in the email subject or as a machine-readable header. Specify bounce and rejection handling: SES provides SNS bounce notifications — confirm a bounce handler is implemented and that bounced addresses are surfaced in the portal's notification feed or as a platform admin alert.

---

### Regulatory Reporting Format

Phase 4 delivers a "Regulatory Export Service" with no specified output format. Solvency II Pillar III reporting uses XBRL QRT taxonomy. Art. 259 actuarial audit trail data is different from QRT reporting — it is typically produced on demand in whatever format the regulator specifies.

The compliance workshop planned for Phase 1 must produce a written answer to two questions: (a) is the regulatory export for internal audit purposes (any queryable format acceptable) or for direct FCA/PRA submission (specific format required)? (b) Does the FCA supervisory data submission framework require a specific format for Solvency II Art. 259 records? Without this answer, Phase 4 scope is undefined. Make it an explicit Phase 1→2 gate item alongside the existing compliance deliverables.

---

### Consumer-Driven Contract Testing

The React SPA consumes the API Service REST API. No contract testing is specified. The testing approach lists unit tests, integration tests, RLS penetration tests, hash-chain integrity tests, and load tests — but not API contract tests.

Without consumer-driven contract testing (Pact or equivalent), a backend refactor that renames a JSON field or changes a response shape is not caught until manual testing in staging. With a small team where the same engineers likely work on both frontend and backend, this is a realistic drift scenario.

Implement Pact contract tests: the React SPA publishes its expected API contract to a Pact Broker; the API Lambda verifies against that contract in the provider verification CI step. This catches contract drift on every PR. Implementation cost: 2–3 days of setup for the first contract; incremental per new endpoint thereafter.

---

## Priority Matrix

Findings below are not duplicates of findings in `architecture-review.md` or `event-architecture-analysis.md`.

| Framework | Finding | Priority | Recommended action |
|---|---|---|---|
| FMEA | KMS CMK rotation breaks genesis anchor verification (FM-7): `Verify` API requires explicit key version ARN; AWS does not auto-try previous key versions on `Verify` (unlike `Decrypt`) | High | Extend `audit-verify` Lambda to store the key version ARN from the genesis event payload and use it explicitly when calling KMS `Verify`. Test by rotating the CMK in staging and running the verification sweep immediately after. |
| STRIDE | Raw counterparty files not stored under Object Lock — counterparty can dispute that the system altered their submission; SHA-256 checksum in mutable PostgreSQL is insufficient non-repudiation | High | Store raw received files in an Object Lock-protected S3 prefix (or alongside audit events in the same WORM bucket). The Object Lock object is the non-repudiation anchor; `cycle_files.sha256_checksum` remains the query index. |
| PRR | No runbooks exist for any failure mode | High | Author five runbooks before Phase 3 go-live (not Phase 4): Lambda error spike, hash chain violation, SES delivery failure, Cognito outage, Aurora connection exhaustion. Each runbook: symptom → diagnosis steps → resolution → escalation path. |
| STRIDE | Approval callback endpoint does not re-validate JWT before calling `SendTaskSuccess` — a leaked task token allows unauthenticated approval | High | In the Step Functions approval callback handler: re-validate the caller's JWT, confirm `role` and `tenant_id` match the expected approver, then call `SendTaskSuccess`. Add an integration test asserting a valid task token with an invalid JWT returns HTTP 401. |
| Data Governance | Normalisation mapping version not recorded in `cycle_files` — historical cycles not reproducible after a mapping update | High | Add `normalisation_mapping_version` (FK to a versioned `normalisation_mappings` table) to `cycle_files`. Include it in the `ELIGIBILITY_COMPUTED` audit event payload. |
| FMEA | SES failure leaves cycles stuck with no human-visible indicator (FM-5) — in-app notification feed is Phase 4, not present at go-live | High | Either move the in-app notification feed to Phase 3 scope, or implement a CloudWatch alarm on cycles in a single approval state for more than 4 hours as a minimum fallback visible to the platform operator before in-app notifications exist. |
| PRR | Lambda deployment strategy absent — no rollback procedure, no zero-downtime deployment, no pre-traffic health check | High | Specify Lambda deployment via aliases with weighted traffic shifting (10% canary → 100% after clean CloudWatch alarm period). Define rollback as: point alias to previous version (< 30 seconds). Add a pre-traffic hook Lambda running the RLS integration test suite before traffic shifts. |
| Integration Contract | Canonical internal file schema not versioned or published — eligibility engine's expected input is implicit in code | High | Define a versioned JSON Schema for each canonical file type. Store in version control. Normaliser validates output against schema before handing off to the eligibility engine. |
| Data Governance | DPIA not in scope — system processes alive/dead status of insured individuals; right to erasure vs. Solvency II conflict for insured individuals is unresolved | High | Commission a DPIA covering insured individual PII in counterparty files as a Phase 1 deliverable alongside the compliance workshop. The DPIA output determines whether data minimisation changes (store only anonymised aggregates, not raw people tables) are required. |
| STRIDE | Audit ledger verification sweep (clean runs) not written as audit events — auditor cannot confirm when the last successful sweep ran via a ledger query | Medium | Write a `CHAIN_VERIFIED` audit event on every clean sweep run, including event count verified and key version ARN used. Add a CloudWatch alarm if no `CHAIN_VERIFIED` event appears within 8 days. |
| AWS Well-Architected | No data classification table — encryption granularity, access logging, and retention policy for each data entity are undefined | Medium | Author the data classification table (skeleton in Framework 6) as a Phase 1 security deliverable. Map each entity to KMS key, S3 bucket policy, CloudWatch log exclusion rule, and retention period. |
| STRIDE | Break-glass SQL statements not captured by CloudTrail — pgaudit configuration unconfirmed | Medium | Confirm pgaudit is enabled in Aurora parameter group with `pgaudit.log = 'write,ddl'` and that the CloudWatch log group has deletion protection via a resource policy preventing the operational IAM roles from deleting it. |
| Evolutionary Architecture | Audit completeness fitness function not implemented — sealed cycles with missing audit events undetected until regulatory examination | Medium | Implement the nightly SQL completeness check as specified in Framework 5. One-day implementation task with direct regulatory impact. |
| FMEA | Partial file truncation not detected before eligibility (FM-1) — SHA-256 matches a truncated file; record count not validated against prior month | Medium | Add a record count field to normalised file metadata. Compare against prior month's count for the same counterparty with a configurable tolerance (e.g. ±20%). Flag for manual review if outside tolerance before triggering eligibility. |
| Integration Contract | SES bounce handling not specified — counterparty misses approval notification; cycle stalls silently | Medium | Implement SES SNS bounce notification handler: log as a `NOTIFICATION_BOUNCED` audit event, alert platform admin via CloudWatch alarm, surface to in-app notification backlog. |
| PRR | Secrets Manager DB credential rotation not specified — no rotation procedure under an incident scenario | Medium | Use Aurora IAM authentication for Lambda execution roles (no long-lived credential) and Secrets Manager with 30-day automatic rotation for any service account credentials. Test rotation in staging with live connections to confirm no application restart is required. |
| Integration Contract | Regulatory reporting format not confirmed with compliance team — Phase 4 scope undefined | Medium | Make this an explicit output of the Phase 1 compliance workshop: written confirmation of export format (internal audit vs. FCA/PRA submission) and applicable format standard. Document as a Phase 1→2 gate item. |
| AWS Well-Architected | S3 long-term file storage cost not modelled in `financials.py` | Low | Add raw counterparty file storage to `financials.py` with lifecycle tier costs: S3 Standard (0–90 days), S3-IA (90 days–1 year), Glacier Deep Archive (1–10 years) per the retention policy. |
| Evolutionary Architecture | Consumer-driven contract testing absent — portal/API contract drift undetected until staging | Low | Implement Pact contract tests between the React SPA and the API Lambda. Priority is lower given the small team, but should be in place before a second frontend developer joins. |
| AWS Well-Architected | S3 lifecycle rules not specified in Terraform — long-term storage cost savings not realised | Low | Add a single Terraform `aws_s3_bucket_lifecycle_configuration` resource: IA at 90 days, Glacier Instant at 1 year, Glacier Deep Archive at 3 years. No operational overhead. |

---

*This document is an AI-assisted internal analysis and is not a client-facing deliverable.*
