# Solution Architecture Questionnaire

Please fill out this questionnaire to help prepare the solution architecture document. Answer all questions that are relevant to your application.

## 1. Business Context

### 1.1 Project Overview
- **Project Name:** Tourist Mobile Application
- **Business Domain:** Tourist Application
- **Primary Business Objective:**  Show users information about nearby attraction using AI

### 1.2 Business Drivers
- **What business problem does this solution solve?** It helps users discover and learn about nearby attractions using AI-powered photo recognition, replacing the manual flow of taking photos and searching on ChatGPT/Wikipedia. It also connects tourists with partner businesses for enhanced experiences and monetization.
  
- **What are the key business goals?**
  - Generate revenue through partner commissions (when users redeem discounts or purchase items)
  - Generate revenue through partner advertising fees
  - Scale globally from famous attractions (Eiffel Tower) to small local venues (Spanish vineyards)
  - Build a partnership ecosystem that benefits both tourists and local businesses
  - Achieve 95% accuracy in attraction information
  - Prepare for scale comparable to Klook/Viator (50M+ users potential)

## 2. Functional Requirements

### 2.1 Core Features
- **List the main features/functionalities:**
  1. Show AI based descriptions of nearby attractions.
  2. AI recognition of object
  3. Suggestions from partner object owners about their businesses (ads). Working ours, descriptions, menu etc

- **What are the primary user personas and their use cases?**
  - Persona 1: Tourist
  - Persona 2: Partner object owner

Other features:
- recommendation systems
- credit cards support
- loyality programs
- personal invormations in applicaiton
- translation for main languages

### 2.2 User Interactions
- **How will users interact with the system?** Mobile application only (iOS and Android). Live camera feed for real-time recognition or photo upload from gallery.
  
- **What are the main user workflows?** 
  - Primary workflow: Open app → Point camera at attraction (or upload photo) → AI recognizes attraction → View text/audio description → See nearby partner recommendations → Redeem discounts or purchase items (tickets, tours)
  - Secondary workflow: Browse nearby attractions → View details → Save to favorites → Build trip story from captured photos with geolocation
  - Partner workflow: Sign up via portal → Submit business information → Await admin approval → Manage offers/products → View analytics
  
- **Are there any batch processing requirements?**
  - Daily cache refresh for popular attractions by region
  - Nightly partner commission calculations
  - Weekly analytics reports for partners
  - Monthly loyalty points reconciliation
  - Batch processing of flagged content for moderation review

## 3. Non-Functional Requirements

### 3.1 Performance
- **Expected number of concurrent users:** We start small, but we want to be prepared for large scale
  
 
- **Response time requirements:**
  - API response time: 3 seconds
  - App load time: 3 seconds 
  - AI generation desctiption: 3 seconds 

- **Peak load expectations:** We want to be prepared for large scale

- **Another NFR**
- Application should always have some benefits for clients
- it should provide offline, cache mode
- it should contain some small LLM in phones that support it to provide some capabilities even offine
- use cloud infrastructure
- you don't need to have second infrastructure hot, it just need to be prepared to spin up
- low latency in US and in China etc.
- we don't expect much traffic from the start but we want to be ready to scale when they come
- AI should be able to has around 95% correctness of informations

### 3.2 Scalability
- **Expected growth over time:**
  - Year 1: 1000
  - Year 2: 10000
  - Year 3: 100000

- **Scaling strategy preference:** Auto scaling, Horizontal
  
- **Geographic distribution requirements:** US, China first but we want to have option then to scale for other regions
  

### 3.3 Availability & Reliability
- **Required uptime (SLA):** 99.9% (~43 minutes downtime per month)
  
- **Maximum acceptable downtime:** 1 hour per incident (tourists can use cached/offline mode during downtime)
  
- **Recovery Time Objective (RTO):** 1 hour (time to restore service after failure)
  
- **Recovery Point Objective (RPO):** 15 minutes (acceptable data loss window). Upgrade to 5 minutes in Phase 2 when payment volumes increase.
  

### 3.4 Security
- **Authentication requirements:** 
  - OAuth 2.0 / OpenID Connect for social login (Google, Apple, Facebook)
  - Email/password authentication with bcrypt password hashing
  - Multi-factor authentication (SMS-based 2FA) for sensitive operations
  - JWT tokens for API authentication
  - Account required for all features (no anonymous access)
  
- **Authorization model:** RBAC (Role-Based Access Control) with 4 primary roles:
  - Tourist: View attractions, save favorites, rate descriptions, redeem discounts, purchase items
  - Partner: Manage business profile, create offers/products, view own analytics only
  - Admin: Approve partners, manage users, view platform-wide analytics, handle disputes
  - Content Moderator: Review flagged descriptions, handle misinformation reports
  
- **Data classification:**
  - Public: Attraction descriptions, partner business information (hours, menu, location)
  - Internal: User analytics, platform metrics, partner performance data
  - Confidential: User personal information, payment details, loyalty points, location history
  - Restricted: Authentication credentials, API keys, encryption keys
  
- **Compliance requirements:**
  - PCI-DSS Level 2 (handling credit card transactions for ticket purchases)
  - Prepare for GDPR (EU expansion in Phase 2/3) - data export, right to deletion
  - Prepare for CCPA (California users)
  - China data residency requirements (data stored in China for Chinese users)
  - App Store compliance (Apple App Store, Google Play Store guidelines)
  
- **Data encryption requirements:**
  - At rest: AES-256 encryption for database (RDS encryption), S3 bucket encryption for photos, encrypted Redis for cached sensitive data
  - In transit: TLS 1.3 for all API communications, HTTPS only (no HTTP), certificate pinning for mobile app 

### 3.5 Data Requirements
- **Data volume:** (Current and projected)
  - Year 1 (1k users): ~10-50 GB total (user data, photos metadata, transactions)
  - Year 2 (10k users): ~100-500 GB total
  - Year 3 (100k users): ~1-5 TB total (primarily user photos and transaction history)
  - Photos: ~5MB per photo, expect 10-50 photos per active user per trip
  - Transactions: ~100 bytes per record, expect 500k transactions/month at scale
  
- **Data retention policies:**
  - User photos: Retained indefinitely (for trip story feature) unless user deletes account
  - Transaction records: 7 years (financial compliance requirements)
  - User session logs: 90 days
  - Application logs: 30 days (hot), 1 year (archived)
  - Analytics data: 2 years
  - Cached attraction descriptions: Refresh daily, retain for offline use
  - User account data: Retained until account deletion request (GDPR compliance)
  
- **Data backup requirements:**
  - Database backups: Continuous automated backups with 15-minute RPO
  - Point-in-time recovery: 35 days retention
  - Photo storage (S3): Versioning enabled to protect against accidental deletes/overwrites; cross-region replication. Lifecycle rule: expire non-current versions after 30–90 days to control cost while keeping a recovery window.
  - Daily snapshots retained for 7 days
  - Weekly snapshots retained for 4 weeks
  - Monthly snapshots retained for 12 months
  
- **Data archival requirements:**
  - Transaction records older than 2 years: Move to S3 Glacier (compliance archive)
  - Application logs older than 1 year: Archive to S3 Glacier Deep Archive
  - User photos from deleted accounts: Permanent deletion after 30-day grace period
  - Partner business data for inactive partners: Archive after 1 year of inactivity

## 4. Technical Requirements

### 4.1 Technology Stack Preferences
- **Programming languages:** 
  - Backend: flexibility based on team expertise
  - Mobile: Swift (iOS), Kotlin (Android), or React Native/Flutter for cross-platform -based on team expertice
  - AI/ML: Python for model integration
  
- **Frameworks:** 
  - Backend: FastAPI (Python), Express/NestJS (Node.js), or Gin (Go)
  - Mobile: Native (Swift/Kotlin) preferred for performance, React Native/Flutter acceptable
  - Database ORM: SQLAlchemy (Python), TypeORM (Node.js), or GORM (Go)
  
- **Database preferences:** 
  - Primary: PostgreSQL (AWS RDS) with PostGIS extension for geolocation queries
  - Cache: Redis (AWS ElastiCache) for sessions, rate limiting, frequently accessed data
  - Object Storage: AWS S3 for user photos and static assets
  - Search (Phase 2+): OpenSearch for advanced geo-location and full-text search
  - Optional: DynamoDB for AR recognition results (time-series data)
  - **Rationale:** PostgreSQL gives strong ACID guarantees for payments, supports geospatial queries via PostGIS, and offers JSONB flexibility for partner profiles. Redis offloads hot reads and rate limiting. S3 is durable and cheap for photos. OpenSearch can be added later when geosearch/query volume grows. DynamoDB remains optional for very high-volume, write-heavy AR logs.
  
- **Cloud provider preference:** AWS (US + China regions)
  - AWS US regions (us-east-1 primary, us-west-2 secondary)
  - AWS China regions (cn-north-1 for Chinese users - data residency compliance)
  
- **Containerization:** Docker + ECS/Fargate (or Kubernetes for Phase 3+)
  - Container orchestration: AWS ECS for initial launch
  - Migration path to EKS (Kubernetes) when microservices scale

### 4.2 Integration Requirements
- **External systems to integrate with:**
  1. System: OpenAI API (GPT-4 Vision) | Protocol: REST/HTTPS | Purpose: Primary LLM for attraction description generation and image recognition
  2. System: Google Gemini API | Protocol: REST/HTTPS | Purpose: Secondary LLM fallback when OpenAI fails
  3. System: Google Vision API | Protocol: REST/HTTPS | Purpose: Fast landmark detection before LLM call (cost optimization)
  4. System: Stripe Payment Gateway | Protocol: REST/HTTPS | Purpose: Process credit card payments for museum tickets, tours, etc.
  5. System: Auth0 or AWS Cognito | Protocol: OAuth 2.0/OIDC | Purpose: User authentication (social login + email/password)
  6. System: SendGrid or AWS SES | Protocol: SMTP/REST | Purpose: Transactional emails (welcome, receipts, notifications)
  7. System: Twilio | Protocol: REST/HTTPS | Purpose: SMS notifications and 2FA
  8. System: Apple App Store / Google Play Store | Protocol: REST/HTTPS | Purpose: In-app purchase validation and app distribution

- **Third-party services/APIs:**
  - CDN: AWS CloudFront (global), Alibaba Cloud CDN (China)
  - Monitoring: DataDog or New Relic for APM and distributed tracing
  - Error tracking: Sentry for real-time error monitoring
  - Analytics: Mixpanel or Amplitude for user behavior tracking
  - Maps: Google Maps API or Mapbox for location services
  - Translation: Google Translate API for multi-language support
  - On-device ML: TensorFlow Lite or Core ML for offline AI capabilities
  - **Rationale:** CloudFront/Alibaba CDN reduce latency globally, especially across the Great Firewall. DataDog/New Relic plus Sentry provide deep visibility and fast triage. Mixpanel/Amplitude give product analytics without building in-house. Google Maps/Mapbox provide reliable POI and routing data. Translation API accelerates multilingual rollout. On-device ML frameworks enable offline capability on capable devices.
  
- **Message queue/event streaming requirements:**
  - AWS SQS: For asynchronous photo processing (recognition queue)
  - AWS SNS: For push notifications to mobile devices
  - AWS EventBridge: For event-driven architecture (partner offers, user actions)
  - Consider: Apache Kafka or AWS Kinesis for real-time analytics at scale (Phase 3+)
  - **Rationale:** SQS decouples photo uploads from AI processing to smooth spikes and retry safely. SNS fan-outs mobile/push/email without tight coupling. EventBridge coordinates cross-service events cleanly. Kafka/Kinesis reserved for later when real-time analytics or high-throughput streams justify the extra ops overhead.

### 4.3 Data Flow
- **Describe the data flow through the system:**
  1. **Photo Recognition Flow:** User captures photo → Upload to S3 → Google Vision API detects landmark → If recognized, generate description via OpenAI → If fails, fallback to Gemini → If fails, fallback to on-device model → Cache result → Return to user
  2. **Partner Recommendation Flow:** User views attraction → Query PostgreSQL for nearby partners (PostGIS geo-query) → Filter by distance and offers → Rank by relevance → Cache top results in Redis → Return to mobile app
  3. **Payment Flow:** User purchases ticket → Validate user session → Send to Stripe API → Record transaction in PostgreSQL → Update loyalty points → Send confirmation email via SendGrid → Return receipt
  4. **Offline Mode Flow:** App launches → Check last cache update → If >24 hours, fetch popular attractions for current region → Store in local SQLite → User can browse cached data without internet
  5. **Partner Portal Flow:** Partner logs in → Auth0 validates token → Partner updates offer → Write to PostgreSQL → Invalidate Redis cache → Sync to mobile app via push notification
  
  **Indicative Latencies (p95 targets):**
  - Photo Recognition Flow: End-to-end <3s; Google Vision ~300-800ms; LLM (OpenAI/Gemini) ~1-2s; cache hit path <200ms
  - Partner Recommendation Flow: <400ms (cache hit); <800ms (cache miss + DB geo-query)
  - Payment Flow: <2s (Stripe round-trip and DB writes)
  - Offline Mode Flow: <500ms to serve cached content; background refresh not blocking
  - Partner Portal Flow: <800ms for read operations; <1.2s for write/update with cache invalidation
  
- **Data sources:**
  - User-generated: Photos (from camera/gallery), location data (GPS), user accounts, ratings/feedback
  - Partner-generated: Business profiles, offers, product inventory, pricing
  - AI-generated: Attraction descriptions, recommendations
  - External: OpenAI/Google APIs, payment processor data, map data
  
- **Data destinations:**
  - Mobile app: Attraction descriptions, partner recommendations, user profile
  - PostgreSQL: User accounts, transactions, partner data, loyalty points
  - S3: User photos with metadata, static assets
  - Redis: Session tokens, cached descriptions, rate limiting data
  - Analytics platform: User behavior, conversion metrics, partner performance
  - Partner dashboards: Sales analytics, redemption rates
  
- **Real-time vs batch processing:**
  - **Real-time:** Photo recognition (user expects <3 sec response), payment processing, authentication, partner recommendations — rationale: user-facing flows must be instant to avoid drop-off and payment abandonment.
  - **Near real-time:** Push notifications, cache invalidation, user location updates — rationale: slight delay is acceptable while keeping content fresh and relevant without blocking UX.
  - **Batch (daily):** Cache refresh for popular attractions, partner analytics aggregation, daily reports — rationale: daily cadence balances data freshness with cost/compute efficiency.
  - **Batch (nightly):** Commission calculations, loyalty points reconciliation, data archival — rationale: heavy joins/settlements run off-peak after gateways post settlements, reducing load during user traffic.
  - **Batch (weekly/monthly):** Partner payout processing, compliance reports, long-term analytics — rationale: aligns with financial cutoffs and reporting cycles; not user-facing so can run during lowest demand.

## 5. Architecture Patterns

### 5.1 Architecture Style
- **Preferred architecture pattern:** Modular Monolith with separate Attraction Recognition microservice (Hybrid approach)
  
- **Reason for choice:**
  - **Modular Monolith** for core application (user management, partner management, payments, loyalty)
    - Simpler deployment and operations initially
    - Clear module boundaries allow future extraction to microservices
    - Lower operational complexity for small team
    - Easier debugging and testing
  - **Separate AR Microservice** for Attraction Recognition
    - High computational load (AI/ML processing)
    - Needs independent scaling from rest of application
    - Can scale horizontally based on photo upload volume
    - Isolates expensive AI API calls
  - **Migration Path:** Can extract other modules to microservices as traffic grows (Phase 3+)
  - **Built to scale:** Architecture ready for microservices but deployed efficiently
  
### 5.2 Components
- **Main application components:**
  1. **Mobile App Module** (iOS/Android) - User interface, camera integration, offline caching, local ML model
  2. **API Gateway Module** - Request routing, rate limiting, authentication validation, API versioning
  3. **User Management Module** - Authentication, user profiles, favorites, trip history
  4. **Attraction Recognition Service** (Separate Microservice) - Photo processing, Google Vision API, LLM integration, caching
  5. **Partner Management Module** - Partner portal, business profiles, offer management, product catalog
  6. **Payment & Loyalty Module** - Stripe integration, transaction processing, loyalty points, QR code generation
  7. **Recommendation Engine Module** - Geo-location queries, partner ranking, personalized suggestions
  8. **Content Moderation Module** - User feedback review, description quality control, flagged content
  9. **Analytics Module** - User behavior tracking, partner performance metrics, business intelligence
  10. **Notification Module** - Push notifications, email, SMS

- **Shared services needed:**
  - **Authentication Service:** JWT token validation, session management (Auth0/Cognito)
  - **Logging Service:** Centralized logging (CloudWatch Logs, DataDog)
  - **Monitoring Service:** Application performance monitoring, error tracking (Sentry, DataDog APM)
  - **Caching Service:** Redis for distributed caching
  - **File Storage Service:** S3 for photos and static assets
  - **Message Queue:** SQS for async processing
  - **CDN:** CloudFront for content delivery
  - **Database Service:** PostgreSQL (shared, but separate schemas per module)

## 6. Infrastructure & Deployment

### 6.1 Deployment Model
- **Deployment environment:** Cloud (AWS US + China regions)
  - Primary: AWS us-east-1 (US East)
  - Secondary: AWS cn-north-1 (China North)
  - Prepared for expansion: EU, APAC, Latin America (Phase 3+)
  
- **Deployment strategy:** Canary deployment
  - Deploy to 5% of traffic first
  - Monitor error rates, latency, user feedback for 2-4 hours
  - Gradually increase to 25%, 50%, 100% over 24-48 hours
  - Automatic rollback if error rate exceeds threshold
  - Separate canary strategy for each region
  - Alternative strategy is: Blue-green - Works for stateless ECS services in a single region, but duplicating stacks in both US and China plus handling DB migrations doubles cost/complexity. We keep canary for production to reduce blast radius and capacity needs; blue-green remains useful for staging smoke tests and infra changes.
  
- **CI/CD requirements:**
  - Source control: GitHub with protected main branch
  - CI Pipeline: GitHub Actions or AWS CodePipeline
  - Automated testing: Unit tests, integration tests, E2E tests (must pass before deployment)
  - Automated security scanning: Dependency vulnerability checks, SAST/DAST
  - Automated builds: Docker image builds on every commit
  - CD Pipeline: Automatic deployment to staging, manual approval for production
  - Infrastructure as Code: Terraform or AWS CloudFormation for reproducible infrastructure
  - Blue-green environments for staging/production
  
### 6.2 Infrastructure Components
- **Compute requirements:**
  - Web/API servers: AWS ECS Fargate (2-4 tasks initially, auto-scaling to 20+ at peak)
  - AR microservice: AWS Lambda or Fargate (on-demand scaling, process photos asynchronously)
  - Background workers: ECS tasks for batch jobs (cache refresh, analytics, commission calculation)

- **Storage requirements:**
  - Database storage: AWS RDS PostgreSQL
    - Phase 1: 100GB SSD (db.t4g.large)
    - Phase 2: 500GB SSD (db.t4g.xlarge with read replicas)
    - Phase 3: 2TB+ with sharding
  - File storage: AWS S3
    - Standard tier for recent photos (90 days): ~100GB Year 1, 1TB Year 3
    - Infrequent Access tier for older photos: ~500GB Year 3
    - Glacier for archived data: ~1TB Year 3
  - Cache storage: AWS ElastiCache Redis (5-20GB depending on phase)

- **Networking requirements:**
  - CDN needed: Yes
    - AWS CloudFront for global distribution (US, EU, APAC)
    - Alibaba Cloud CDN for China (Great Firewall compliance)
    - Cache static assets, attraction images, popular descriptions
  - Load balancer: Yes
    - Application Load Balancer (ALB) in each region
    - HTTPS termination, path-based routing
    - Health checks for auto-scaling
  - VPN requirements: No VPN for users. VPN for admin access to databases (AWS VPN or bastion host) 

## 7. Observability & Monitoring

### 7.1 Logging
- **Log aggregation requirements:**
  - Centralized logging with AWS CloudWatch Logs
  - Structured JSON logging for easy parsing
  - Correlation IDs for tracing requests across services
  - Separate log groups for: API requests, AR service, background jobs, errors
  - Integration with DataDog for advanced log analysis (Phase 2+)
  
- **Log retention period:** Rationale: short hot retention keeps query costs low and speeds triage; longer cold retention satisfies compliance/forensics (payments, auth) without inflating hot storage.
  - Application logs: 30 days in CloudWatch (hot), 1 year archived in S3
    - Rationale: keep short hot window for fast search and low cost; archive for trend analysis and postmortems.
  - Error logs: 180 days (for debugging and analysis)
    - Rationale: more time to catch intermittent bugs and correlate with releases.
  - Audit logs (authentication, payments): 7 years (compliance)
    - Rationale: required for PCI/legal disputes and fraud investigations.
  - Access logs (ALB): 90 days
    - Rationale: support traffic forensics, WAF tuning, and abuse investigations without excessive storage cost.
  
- **Log analysis needs:**
  - Real-time error detection and alerting
  - User journey tracking (photo upload → recognition → partner view → conversion)
  - API performance analysis (slow queries, high latency endpoints)
  - Security monitoring (failed auth attempts, suspicious activity)
  - Cost analysis (AI API usage per user/region)
  
### 7.2 Monitoring
- **Key metrics to monitor:**
  - **Application metrics:**
    - API response times (p50, p95, p99)
    - Photo recognition success rate (target: 95%)
    - Photo recognition latency (target: <3 seconds)
    - User session duration
    - Cache hit/miss ratio (target: >80%)
    - Authentication success/failure rates
    - Payment transaction success rates
    - Error rates by endpoint
  - **Infrastructure metrics:**
    - ECS task CPU/memory utilization
    - RDS database connections, CPU, IOPS
    - Redis cache memory usage, eviction rate
    - ALB active connections, request count
    - S3 request rates, data transfer
    - Lambda invocations, duration, errors
  - **Business metrics:**
    - Daily/Monthly Active Users (DAU/MAU)
    - Photo uploads per day
    - Partner recommendation click-through rate
    - Discount redemption rate
    - Purchase conversion rate (ticket sales)
    - Revenue per user
    - Partner acquisition rate
    - User retention (Day 1, Day 7, Day 30)

- **Alerting requirements:**
  - **Critical (PagerDuty, immediate response):**
    - API error rate >5%
    - Database connection failures
    - Payment processing failures
    - Service unavailable (health check failures)
  - **High (Slack, 15-min response):**
    - API latency p99 >5 seconds
    - Photo recognition latency >5 seconds
    - Database CPU >80%
    - Cache memory >90%
  - **Medium (Email, 1-hour response):**
    - Photo recognition accuracy <90%
    - Cache hit ratio <70%
    - Unusual traffic patterns
  - **Low (Dashboard, daily review):**
    - User retention trends
    - Partner performance metrics
  
### 7.3 Tracing
- **Distributed tracing needed:** Yes
  - AWS X-Ray or DataDog APM for end-to-end request tracing
  - Track: Mobile app → API Gateway → Backend services → Database → External APIs (OpenAI, Stripe)
  - Identify bottlenecks in multi-service calls
  - Critical for debugging AR microservice performance
  
- **Performance profiling requirements:**
  - Database query profiling (identify slow queries with pg_stat_statements)
  - API endpoint profiling (identify hot paths)
  - Memory profiling for ECS tasks
  - Mobile app performance monitoring (Firebase Performance or similar)
  - AI API cost profiling (track OpenAI token usage per request)

## 8. Disaster Recovery & Business Continuity

### 8.1 Backup Strategy
- **Backup frequency:**
  - Database: Continuous automated backups (15-minute RPO)
  - Database snapshots: Daily at 2 AM UTC
  - S3 photos: Cross-region replication (real-time)
  - Redis cache: Daily snapshots (for warm cache restoration)
  - Infrastructure configuration: Version controlled in Git (Terraform state backed up)
  
- **Backup retention:**
  - Continuous backups: 35 days (RDS point-in-time recovery)
  - Daily snapshots: 7 days
  - Weekly snapshots: 4 weeks
  - Monthly snapshots: 12 months
  - S3 photos: Indefinite (user data) with versioning
  - Archived transaction data: 7 years (compliance)
  
- **Backup testing requirements:**
  - Quarterly: Restore database from backup to staging environment (verify data integrity)
  - Bi-annually: Full disaster recovery drill (simulate region failure, restore to secondary region)
  - Monthly: Verify backup completion and integrity checks
  - Automated: Daily backup validation scripts
  
### 8.2 Disaster Recovery
- **Disaster recovery plan requirements:**
  - Documented runbook for region failure scenarios
  - Automated failover procedures where possible
  - Manual escalation procedures for data center outages
  - Communication plan for users and partners during outages
  - RTO: 1 hour (service restored within 1 hour)
  - RPO: 15 minutes (max 15 minutes of data loss)
  - Post-incident review process (within 48 hours)
  
- **Failover strategy:**
  - **Database:** Multi-AZ deployment in primary region (automatic failover within 2 minutes)
  - **Application:** Auto-scaling replaces failed containers automatically
  - **Region failure:** Manual failover to secondary region (cn-north-1 ↔ us-east-1)
  - **CDN:** Automatic failover to origin if CDN fails
  - **External APIs:** Proxy with automatic fallback (OpenAI → Google Gemini → Local model)
  - **DNS:** Route 53 health checks with automatic traffic routing
  
- **Multi-region deployment:** Yes (US + China from day 1)
  - Active-Active: Both regions serve traffic for their geographic users
  - Data synchronization: Near real-time replication for read-heavy data
  - Write operations: Region-specific with eventual consistency
  - China compliance: Data residency (Chinese user data stays in China)
  - Prepared for expansion: Architecture supports adding EU, APAC regions (Phase 3+)
  - How it works: Each region runs its own stack (API, DB, cache). Read-mostly data (attraction content, partner catalog, configs) is replicated asynchronously to keep regional copies fresh. User/PII/payment data stays in-region for compliance.
  - Eventual consistency: Cross-region sync is async; conflicts resolved via last-writer-wins or idempotent events. In practice, each record carries an updated_at/vector clock-style marker so the newer version wins for non-critical data, and replicated events are designed to be idempotent (safe to reapply without duplication) so retries do not corrupt state. Expect seconds-to-minutes lag for non-critical data (e.g., offers, analytics).
  - Data loss window: In a region loss, unsynced writes since last replication can be lost for cross-region data; bounded by RPO (15 minutes). Region-local PII/payments are not replicated across US↔China by policy.

## 9. Constraints & Assumptions

### 9.1 Constraints
- **Budget constraints:**
  - Presenting 4 budget options (see detailed breakdown in Additional Notes):
    - Option 1: $224k CAPEX, $835/mo OPEX (MVP, US only, 4 months)
    - Option 2: $719k CAPEX, $2,260/mo OPEX (Progressive build, US+China, 7 months) **RECOMMENDED**
    - Option 3: $2.17M CAPEX, $4,665/mo OPEX (All features, 10 months)
    - Option 4: $1.22M migration + $130k/mo OPEX (Target scale: 50M users)
  - Infrastructure OPEX scales with user growth (not fixed)
  - Must balance cost optimization with scale readiness
  
- **Time constraints:**
  - Market pressure: Need MVP within 6 months to compete with existing travel apps
  - Seasonal opportunity: Launch before summer tourist season for maximum impact
  - Option 2 recommended: MVP in 4 months, full features in 7 months
  
- **Technical constraints:**
  - China Great Firewall: Requires separate infrastructure in China, limits some APIs (OpenAI may be blocked)
  - Mobile app stores: Apple App Store and Google Play review process (2-4 weeks)
  - AI API rate limits: OpenAI has rate limits; need fallback strategy
  - On-device ML model size: Limited to ~500MB-1GB for mobile apps
  - Offline functionality: Core features must work without internet connection
  - Mobile device limitations: Older phones can't run on-device AI models
  
- **Regulatory constraints:**
  - PCI-DSS compliance for payment processing (required for Stripe integration)
  - China data residency laws (user data must stay in China)
  - App Store policies: Content moderation, user privacy, in-app purchase rules
  - Photo privacy: User consent required for storing photos with geolocation
  - Partner business verification: Must validate business legitimacy before approval
  
### 9.2 Assumptions
- **Technical assumptions:**
  - OpenAI API remains available and affordable (pricing doesn't increase dramatically)
  - Google Vision API maintains 95%+ accuracy for famous landmarks
  - PostgreSQL can handle geospatial queries at scale (PostGIS extension)
  - Mobile devices support live camera feed processing (iOS 13+, Android 8+)
  - AWS infrastructure in China remains accessible and compliant
  - On-device ML models (TensorFlow Lite/Core ML) can achieve 70-80% accuracy
  - Redis cache provides sufficient performance for 80%+ hit ratio
  - CloudFront CDN provides acceptable latency globally (<200ms)
  
- **Business assumptions:**
  - Partners willing to pay 10-20% commission on sales + advertising fees
  - Users willing to create accounts (not anonymous usage)
  - Tourist users have smartphones with cameras and GPS
  - Market size: 1k users Year 1, 10k Year 2, 100k Year 3 (conservative estimates)
  - Photo upload rate: 10-50 photos per user per trip
  - Conversion rate: 10-20% of users redeem partner offers
  - Ticket/tour purchase rate: 5-10% of users make in-app purchases
  - Partner acquisition: 100 partners Year 1, 1,000 Year 2, 10,000 Year 3
  - Dataset creation: Will build 95% accuracy test dataset during development (Wikipedia, partner-provided content)
  - User retention: 30% Day 7, 20% Day 30 (typical for travel apps)
  - Seasonal traffic: 3-5x spike during summer and holidays

## 10. Future Considerations

### 10.1 Roadmap
- **Planned features for future releases:**
  - **Phase 1 (Months 1-4 - MVP):**
    - Photo recognition with AI descriptions (text + audio)
    - Basic partner recommendations
    - User accounts (social login + email/password)
    - Favorites and history
    - Offline caching
    - US + China deployment
  - **Phase 2 (Months 5-7 - Full Features):**
    - Payment integration (Stripe) for tickets/tours
    - Loyalty program with QR codes
    - Partner self-service portal
    - User ratings/feedback system (thumbs up/down)
    - Trip story feature (photo timeline with geolocation)
    - Multi-language support (translation API)
  - **Phase 3 (Year 2):**
    - Advanced recommendation engine (ML-based personalization)
    - OpenSearch for better geolocation search
    - Real-time analytics dashboard for partners
    - Social features (share trips with friends)
    - EU region deployment (GDPR compliance)
  - **Phase 4 (Year 3+):**
    - Full microservices architecture
    - Database sharding by geography
    - White-label solution for tourism boards
    - Augmented Reality (AR) overlay for attractions
    - Voice-guided tours
    - Integration with booking platforms (hotels, flights)
  
- **Technology migration plans:**
  - **Year 1:** Modular monolith + AR microservice (current plan)
  - **Year 2:** Extract high-load modules to microservices (payments, recommendations)
  - **Year 2:** Migrate from ECS to EKS (Kubernetes) for better orchestration — rationale: as we extract services into microservices, Kubernetes provides superior service mesh capabilities (Istio/Linkerd), advanced traffic management (canary, A/B testing per service), better resource bin-packing to reduce costs, declarative configuration that scales with team growth, and portable infrastructure that eases future multi-cloud expansion. ECS works well for 2-5 services; EKS pays off when managing 10+ microservices with complex inter-service communication.
  - **Year 3:** Implement database sharding (by geography or user ID)
  - **Year 3:** Add OpenSearch for advanced search capabilities
  - **Year 3:** Upgrade RPO from 15 minutes to 5 minutes (stricter data protection)
  - **Year 4+:** Consider serverless architecture for cost optimization
  
- **Scaling plans:**
  - **Year 1 (1k-10k users):** db.t4g.large, single instance per region, minimal infrastructure
  - **Year 2 (10k-100k users):** Upgrade to db.t4g.xlarge, add read replicas, scale ECS tasks
  - **Year 3 (100k-1M users):** Database sharding, OpenSearch, microservices extraction, multi-region expansion (EU, APAC)
  - **Year 4+ (1M-50M users):** Full microservices, ML-based features, global CDN, advanced caching
  - **Geographic expansion:** US+China (Year 1) → EU (Year 2) → APAC+LatAm (Year 3) → Global (Year 4+)
  
### 10.2 Technical Debt
- **Known technical debt:**
  - Modular monolith will need refactoring to microservices as traffic grows (planned for Year 2)
  - PostgreSQL geolocation queries may become slow at scale (plan to add OpenSearch in Phase 3)
  - Manual partner approval process doesn't scale (automate with ML-based verification in Phase 3)
  - Basic recommendation engine (distance-based) needs ML-powered personalization (Phase 3)
  - Limited offline functionality in MVP (improve cache strategy and on-device ML in Phase 2)
  - Single database instance bottleneck (add read replicas Year 2, sharding Year 3)
  
- **Refactoring plans:**
  - **Quarter 4 Year 1:** Extract authentication to shared service (if needed)
  - **Quarter 2 Year 2:** Extract payment module to microservice
  - **Quarter 4 Year 2:** Extract recommendation engine to microservice
  - **Quarter 2 Year 3:** Implement database sharding
  - **Quarter 4 Year 3:** Full microservices migration
  - **Continuous:** Code quality improvements, test coverage increase, security hardening

---

## Additional Notes

**Any other information that would be helpful for the architecture design:**

### Budget Options Summary

We present 4 options for client consideration:

#### **OPTION 1: Start Small - MVP Focus**
- **CAPEX:** $224,000
- **OPEX:** $835/mo infrastructure only ($8,835/mo with staff)
- **Timeline:** 4 months to MVP
- **Features:** Basic photo recognition, simple partner recommendations, US only
- **Team:** 3 developers + 1 designer + 1 PM (part-time)
- **Risk:** High (need to prove concept quickly)
- **Best for:** Testing market, minimal initial investment

#### **OPTION 2: Middle Ground - Progressive Build ⭐ RECOMMENDED**
- **CAPEX:** $719,000 (Phase 1: $478k, Phase 2: $240k)
- **OPEX:** $1,810/mo Phase 1, $2,260/mo Phase 2 infrastructure only ($24,260/mo with staff)
- **Timeline:** MVP in 4 months, full features in 7 months
- **Features:** MVP + payments + loyalty + partner portal, US + China from day 1
- **Team:** 5 developers + 1 designer + 1 PM + 1 DevOps
- **Risk:** Medium (iterative approach, can pivot)
- **Best for:** Balanced approach - scale ready but cost conscious
- **Why recommended:** US+China from launch, architecture built to scale, reasonable cost, market validation before full investment

#### **OPTION 3: Start Big - All Features Day 1**
- **CAPEX:** $2,168,400
- **OPEX:** $4,665/mo infrastructure only ($66,665/mo with full staff)
- **Timeline:** 10 months to full launch
- **Features:** Complete platform with all features, multi-region ready, built to scale
- **Team:** 10 developers + 2 designers + 1 PM + 2 DevOps + 1 QA
- **Risk:** Low (fully featured from start)
- **Best for:** Well-funded project, minimize future refactoring

#### **OPTION 4: Target Infrastructure (Klook/Viator Scale)**
- **Migration CAPEX:** $1,218,000 (from Option 3)
- **OPEX:** $130,100/mo infrastructure ($670,100/mo with full team)
- **Timeline:** Year 4-5 to reach this scale
- **Features:** 50M+ users, 10k+ QPS, full microservices, global multi-region
- **Best for:** Understanding long-term infrastructure needs and costs

### AI Strategy Details

**Primary AI Flow (Hybrid Approach):**
1. **Google Vision API** (landmark detection) - Fast, cost-effective for famous landmarks
2. If not recognized or needs description → **OpenAI GPT-4 Vision** (primary LLM)
3. If OpenAI fails → **Google Gemini** (secondary LLM fallback)
4. If both fail or offline → **On-device ML model** (TensorFlow Lite/Core ML, 70-80% accuracy)

**Why this hybrid approach:**
- Google Vision API provides quick "Yes/No" landmark detection (~$1/1000 images)
- Saves expensive LLM calls for obvious landmarks
- Better UX: Show "Detected: Eiffel Tower" instantly while generating full description
- Multi-provider resilience: Don't depend on single AI provider
- Offline capability: On-device model for users without internet

**AI Accuracy Target: 95%**
- Will create test dataset during development (Wikipedia + partner content)
- User feedback system (thumbs up/down) to track actual accuracy
- Content moderation review for flagged incorrect descriptions
- Continuous improvement through user feedback loop

### Offline/Caching Strategy

**What to cache:**
- Recently viewed attractions (last 50)
- Popular attractions by region (top 100 per region)
- Partner business information (hours, descriptions, offers)
- User favorites and trip history

**Cache limits:**
- Maximum 500MB on-device storage
- User can manually download specific regions before trips
- Daily automatic refresh when on WiFi
- User controls: View usage, clear cache, manage downloads

**On-device ML model:**
- Small model size: 200-500MB
- User must explicitly download (not automatic)
- Only on high-end devices (latest iPhone, flagship Android)
- 70-80% accuracy acceptable (vs 95% cloud)

### Security Considerations

**Rate Limiting:**
- Per user: 100 photo recognitions per day
- Per IP: 1000 requests per hour
- Partner API: 10,000 requests per hour
- Prevents abuse and controls AI API costs

**Data Privacy:**
- Photos stored with user consent only (when user captures, not live feed)
- Geolocation stored for trip story feature
- User can delete photos anytime (30-day grace period before permanent deletion)
- China users: Data stays in China (compliance)
- GDPR ready: Data export, right to deletion (Phase 2)

**Content Moderation:**
- AI-generated descriptions reviewed by content moderators
- User feedback (thumbs down) triggers review
- Misinformation reports handled within 24 hours
- Partner business information verified before approval

### Payment Integration

**Stripe Integration:**
- Credit card processing for ticket/tour purchases
- Partner can sell in-app products (museum tickets, guided tours, merchandise)
- Commission model: 10-20% platform fee on transactions
- Payout schedule: Monthly to partners (Net-30)
- Fraud detection: Stripe Radar enabled

**Loyalty Program:**
- Points earned: 1 point per $1 spent
- Points redeemed: 100 points = $1 discount
- QR code at partner locations for bonus points
- Gamification: Badges for visiting attractions in different categories

---

**Questionnaire completed by:** Solution Architect  
**Date:** January 22, 2026  
**Version:** 1.0
