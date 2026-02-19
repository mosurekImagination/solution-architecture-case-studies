# Discovery Questions — Case Study 02 — Data Ingestion

> Follow-up questions triggered by **ADR-002: Data Ingestion Strategy**.
> Reduced to **essential questions only** — professional assumptions are documented in ADR-002 § Professional Assumptions for items the SA can reasonably infer.
>
> **Priority:**
> - 🔴 **Blocker** — blocks implementation; no reasonable assumption possible
> - 🟡 **Important** — shapes the solution significantly; we can assume a default temporarily
> - 🟢 **Nice to have** — improves design quality; we proceed without it

---

**Project:** Data-Driven Customer Engagement Platform
**From:** Solution Architect
**To:** Client Representative
**Date sent:** 2026-02-19
**Date answered:**
**Triggered by:** ADR-002 — Data Ingestion Strategy

---

## 1 — WordPress Database Access

| # | Priority | Question | Why We Need This | Our Assumption (if unanswered) | Answer |
|---|----------|----------|------------------|-------------------------------|--------|
| Q1 | 🔴 | Can we get **read-only access to the WordPress MySQL database** to inventory the tables — specifically a list of tables with approximate row counts? We do NOT need the data itself at this stage, only the schema structure. | We need to determine which tables are analytically relevant and estimate extraction pipeline runtime. This decides whether direct SQL extraction (our recommendation) or full RDS replication is more cost-effective. If we need >80% of the schema, replication wins; if 10-30%, direct SQL wins. | We assume ~10-30% of tables are analytically relevant (standard for e-commerce). We size the PoC for direct SQL extraction and revisit if inventory shows otherwise. | |
| Q2 | 🟡 | Is there an **existing VPN or AWS Direct Connect** between the on-prem data center and your AWS account? | If yes, we skip 2-4 weeks of network setup. If no, we budget for it. Does not change the architecture — just the timeline. | No existing connection. We budget for VPN/Direct Connect setup (2-4 weeks, ~$5K-10K). | |
| Q3 | 🟡 | Does your infrastructure team have capacity to set up a **MySQL read replica** of the WordPress database? This is a standard MySQL feature — we would use it to isolate analytical reads from production traffic. | Read replica is our recommended approach to avoid any production impact. If not feasible, we proceed with a read-only user on production with query limits. | Read replica is feasible. We include it in the implementation plan. Fallback: read-only user with query governor (statement timeout, connection limit). | |

## 2 — Mobile App Vendor

| # | Priority | Question | Why We Need This | Our Assumption (if unanswered) | Answer |
|---|----------|----------|------------------|-------------------------------|--------|
| Q4 | 🔴 | Can we get the **mobile vendor's API documentation** — endpoints, authentication method, rate limits, and available data entities? | Without API docs, we cannot design the mobile ingestion DAGs. We need to understand what data the API exposes to determine if it's sufficient for the recommendation engine or if we need the DB export supplement. No reasonable assumption possible — this is vendor-specific. | None — this is a true blocker. We cannot design the mobile ingestion path without knowing what the API offers. | |
| Q5 | 🔴 | You mentioned the vendor's database is **"available on request."** Can you clarify: would the vendor agree to provide **periodic database exports** (e.g., weekly SQL dump or CSV to an S3 bucket)? This is lighter than granting us DB access — it's a script they run on their side. | Our recommended approach is API for ongoing data + periodic DB export for initial backfill and data the API doesn't expose. If the vendor won't provide exports, we fall back to API-only (which may limit the data available for recommendations). | Vendor is willing to provide periodic exports — they've been in a 3-year maintenance contract and this is a low-effort request. If refused, we proceed API-only and accept the data coverage limitation. | |

## 3 — Wholesaler Data

| # | Priority | Question | Why We Need This | Our Assumption (if unanswered) | Answer |
|---|----------|----------|------------------|-------------------------------|--------|
| Q6 | 🔴 | **How many wholesalers** currently provide data, and can we get **2-3 sample files** from different suppliers? We need to see the actual formats (CSV, Excel, XML, PDF, etc.) to design the file processing pipeline. | You described wholesaler data as "everything, no standard." We've designed a flexible landing zone that accepts any format — but we need sample files to build the first transformation models and validate our approach. The number of suppliers determines operational scaling. | 5-15 suppliers, mostly CSV and Excel files. We design the landing zone for this scale and adjust after seeing real samples. | |

---

## Questions NOT Asked (Covered by Professional Assumptions)

The following areas are **intentionally not asked** — they are covered by assumptions A1–A6 in ADR-002 and will be verified during the Proof of Concept phase:

- **WordPress `updated_at` columns** — assumed to exist on key tables (standard e-commerce practice). Verified during Q1 schema inventory.
- **WordPress schema change frequency** — assumed stable (15-year-old system). Mitigated by dbt tests regardless of answer.
- **Priority WordPress tables** — assumed standard e-commerce entities (orders, products, customers). Determined from Q1 inventory.
- **Mobile API authentication method** — covered by Q4 (API docs). Any auth method is implementable.
- **Mobile API rate limits** — covered by Q4 (API docs). Assumed manageable for daily batch.
- **WordPress schema documentation** — not expected to exist for heavily-customized system. We reverse-engineer from the schema inventory (Q1).
- **Existing background job tooling** — useful but not blocking. We're building new pipelines regardless.
- **AWS SES email volume/configuration** — belongs in a separate ADR for the email delivery system, not data ingestion.
