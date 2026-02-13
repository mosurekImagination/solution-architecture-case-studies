# Discovery Questions — Case Study 02

> Based on initial client meeting (VTT transcription, 2026-02-13).
> Questions grouped by topic for easy navigation. Please fill in the **Answer** column.
> Answers will update: architecture questionnaire, solution design, and ADRs.
>
> **Priority:**
> - 🔴 **Blocker** — blocks architecture decisions; answer needed before design work
> - 🟡 **Important** — shapes the solution significantly; can assume a default temporarily
> - 🟢 **Nice to have** — improves design quality; can proceed without it

---

**Project:** Data-Driven Customer Engagement Platform
**From:** Solution Architect
**To:** Client Representative
**Date sent:** 2026-02-13
**Date answered:**

---

## Questions

### Budget & Timeline

| # | Priority | Question | Context / Why I'm Asking | My Assumption | Answer |
|---|----------|----------|--------------------------|---------------|--------|
| 1 | 🔴 | What is the budget envelope or target range for this initiative? | Need to scope solution options realistically. Three options prepared range from ~$80K to ~$1.5M — knowing the budget band avoids wasting time on options outside range. | Enterprise-scale, $200K–$1M range | |
| 2 | 🟡 | Is there a target go-live date or hard deadline? | Phased delivery proposed (3–10 months depending on option). Need to know if there's a board presentation date, seasonal deadline, or external commitment driving timing. | No hard deadline; phased delivery acceptable | |

### Data Access — Mobile App Vendor

| # | Priority | Question | Context / Why I'm Asking | My Assumption | Answer |
|---|----------|----------|--------------------------|---------------|--------|
| 3 | 🔴 | What data does the mobile app vendor store? Can they export it? In what format? | Mobile data is one of three key data sources. Without it, the suggestion engine covers only web customers and we lose visibility into mobile buying patterns. | Batch CSV/JSON export is negotiable via contract amendment | |
| 4 | 🟡 | How many customers have the mobile app installed? | Determines whether mobile push is a viable delivery channel and how much data we're missing by not having mobile data in Phase 1. | < 30% of total customer base | |
| 5 | 🟡 | Does the mobile vendor have an API, or is data access database-level only? | Impacts integration architecture — API is cleaner and more sustainable; direct DB access is fragile and vendor-dependent. | No API; vendor operates as black box | |

### Data Access — WordPress & Wholesalers

| # | Priority | Question | Context / Why I'm Asking | My Assumption | Answer |
|---|----------|----------|--------------------------|---------------|--------|
| 6 | 🔴 | What is the WordPress DB size and schema? Is it standard WooCommerce or heavily customized? | Determines replication strategy, ETL complexity, and storage sizing. A heavily customized schema requires more transformation work. | Standard WooCommerce schema, < 1TB | |
| 7 | 🟡 | How do wholesalers share data today? (APIs, file drops, email, EDI?) | Multiple wholesalers = multiple connectors. If standardized APIs exist, pipeline is simpler. If manual/email-based, we need a different ingestion pattern. | Manual/email-based, no APIs | |
| 8 | 🟡 | What background jobs currently exist and what do they do? | You mentioned background jobs that "handle data." If any existing ETL or data sync exists, we should reuse rather than rebuild. Also need to avoid conflicts. | Basic WordPress cron jobs (order processing, inventory sync) | |

### GDPR & Email Marketing

| # | Priority | Question | Context / Why I'm Asking | My Assumption | Answer |
|---|----------|----------|--------------------------|---------------|--------|
| 9 | 🔴 | Is there GDPR marketing consent on file for customer emails? What percentage of customers have opted in? | EU email marketing requires explicit consent (not just having an email address). If consent is missing, we must build a consent collection flow before launching any email campaigns — this could delay Phase 2 by months. | Consent exists for transactional emails but not all marketing; partial opt-in | |
| 10 | 🟡 | What is the desired frequency of product suggestions? (Weekly? Daily? Event-triggered?) | Drives pipeline architecture: weekly = simple batch ETL. Daily or event-triggered = more complex streaming architecture with higher infrastructure cost. | Weekly batch emails | |

### Infrastructure & Team

| # | Priority | Question | Context / Why I'm Asking | My Assumption | Answer |
|---|----------|----------|--------------------------|---------------|--------|
| 11 | 🟡 | What cloud provider does the company use, if any? (AWS, Azure, GCP, on-prem?) | Snowflake deployment, data residency, and infrastructure costs all depend on cloud provider. Snowflake on AWS was mentioned in our meeting — confirming this. | AWS | |
| 12 | 🟡 | Does the company have an existing email marketing platform? (Mailchimp, HubSpot, SendGrid, etc.) | If a platform exists, we integrate with it rather than build from scratch — significantly changes architecture and reduces cost. | No existing platform | |
| 13 | 🟢 | Is there a data analytics team or plan to hire one? | Determines how advanced the data platform can be. If no team exists and no hiring is planned, the solution must be simple enough for the current internal team to operate. | No dedicated team; will need training | |
| 14 | 🟢 | Are there any existing data warehousing or BI tools in use? (Tableau, Power BI, Looker, etc.) | If BI tools exist, the analytical data store should integrate with them. May influence the choice of Snowflake vs. Databricks. | None currently in use | |

---

## Follow-Up Questions

> Will be added after receiving answers above.

| # | Priority | Question | Triggered By | Answer |
|---|----------|----------|--------------|--------|
|   |          |          |              |        |

---

## Summary of Decisions

> Will be filled after answers are received.

| # | Decision | Based on Answer(s) | Updated In |
|---|----------|---------------------|------------|
|   |          |                     |            |

---

**Version:** 1.0
