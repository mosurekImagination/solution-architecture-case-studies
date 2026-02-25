# Assignment 01 — Retrospective & Gap Analysis

> Post-review analysis following mentor feedback session.
> Captures gaps in the solution design documents, maps them to template sections, and identifies lessons for future assignments.

---

## Context

After completing the solution design for TourLens (Tourist Mobile Application), a mentor review surfaced 4 key feedback points. This retrospective expands on those points and identifies additional gaps by comparing the delivered documents against the template suite and industry best practices.

**Documents reviewed:**
- `01/docs/solution-design.adoc` — Options comparison & recommendation (1795 lines)
- `01/docs/architecture-design-option-2.adoc` — Deep architecture for recommended option (1383 lines)
- `template/solution-design-template.adoc` — Full template (25 sections, 16 diagrams)
- `template/solution-design-compact-template.adoc` — Compact template (8 sections, 4 diagrams)

---

## Section 1: Mentor Feedback

### 1.1 No Revenue Projections / ROI / Break-Even

**What the mentor said:** "When will we start earning these millions?"

**What's in the docs:**
- Business Model described in 3 bullet points at `solution-design.adoc` L104–L110:
  - Partner commissions: 10–20% on transactions
  - Partner advertising: promoted placement
  - Scale ambition: Klook/Viator level (50M+ users) over 3–5 years
- Costs are meticulously detailed: CAPEX tables per phase, monthly OPEX line items, Year 1 TCO of ~$792k (L838–L851)
- Scalability & Growth Roadmap (L1030–L1094) shows OPEX at different MAU tiers but **never mentions revenue at those tiers**

**What's missing:**
- Revenue projections at each MAU tier (e.g., 1k → 10k → 25k → 100k MAU)
- ROI / payback period calculation
- Break-even analysis: when does cumulative revenue exceed cumulative cost?
- Revenue-per-user economics (conversion rate × average transaction × commission)
- When monetization actually starts (Stripe comes at Month 5+ per timeline, but no financial projection)

**Template gap:** The full template has `== Business Value & ROI` (L1512) with payback period and value driver tables. This section was **completely omitted** from the 01 solution design.

**Verdict:** High severity. An executive reading this doc sees $543k going out and nothing coming back. The business case is incomplete.

---

### 1.2 Different Types of Solution Designs

**What the mentor said:** There are different "solution designs" — a proposal (short), this one (middle), and a full technical one.

**What's in the docs:**
- The template suite explicitly defines this hierarchy in `template/README.md`:
  - **Compact** (`solution-design-compact-template.adoc`): 8 sections, 4 diagrams, ~15 min client meeting
  - **Full** (`solution-design-template.adoc`): 25 sections, 16 diagrams, full technical document
- The compact template header says: *"Decision-oriented document for stakeholder meetings. Covers WHAT we recommend, WHY, HOW MUCH, and WHEN. Omits deep technical sections."*

**What's missing:**
- No compact/proposal version was created for 01. Only the mid-length `solution-design.adoc` and the deep `architecture-design-option-2.adoc` exist.
- `solution-design.adoc` is a hybrid: executive-level content (options, costs) mixed with deep technical content (AI pipeline, scaling diagrams) — not clearly layered for different audiences.
- No document in `01/docs/` is explicitly marked "this is for the client meeting" vs "this is for the dev team."

**How to address:**
- Create a `solution-design-compact.adoc` extracting: Executive Summary, Problem, Options Comparison, Recommended Option cost/timeline, Risks, Next Steps
- Add audience markers at the top of existing docs

**Verdict:** Medium severity. The work exists but isn't packaged for the right audiences.

---

### 1.3 IP / Commercial Protection

**What the mentor said:** Someone could take this work and go to another vendor to implement it.

**What's in the docs:**
- The document is fully self-contained and vendor-neutral:
  - Complete architecture diagrams with specific AWS services
  - Exact technology stack (Swift, Kotlin, Python, PostgreSQL)
  - Developer rates ($600/day) and team composition
  - Full Gantt charts with task-level breakdown
  - Complete data model (ER diagram)
  - AI pipeline strategy with provider names and costs

**What's missing:**
- No confidentiality notice or IP ownership statement
- No tiered deliverable strategy (proposal reveals everything upfront)
- No "Why Us" section explaining what the proposing team brings beyond the document
- No engagement terms or document ownership clause

**How to address:**
- Tier deliverables: compact version for pre-engagement, full technical detail only post-contract
- Add a confidentiality header to detailed documents
- Add a "Why This Team" section: domain expertise, team continuity, operational support

**Verdict:** Medium severity. This is a commercial/contractual gap, not a technical one, but it directly impacts the architect's/company's business.

---

### 1.4 No Post-Launch Plan

**What the mentor said:** There is no information about "what next" when the app is deployed.

**What's in the docs:**
- `== Recommended Next Steps` (L1750) covers only pre-launch activities:
  1. Approve Option 2
  2. Confirm technology stack
  3. ...
  9. MVP Launch: July 15, 2026
  10. Full Release: October 20, 2026
- It stops at "Full Release." There is **nothing after October 20, 2026**.
- Year 1 TCO mentions "4 months maintenance" cost ($240k at L848) but no plan for what happens in that time.

**What's missing:**
- **Hypercare / warranty period** — who supports the app in the first 2–4 weeks after launch?
- **Post-launch operations plan** — monitoring, on-call, incident response. The architecture doc has SLOs (L1009) but no operational plan.
- **Maintenance & iteration roadmap** — what does the retained team do after the build phase?
- **User growth strategy** — how to get from 0 to 1k MAU?
- **Partner onboarding plan** — MVP gate says "≥10 partners" (L1030) but no plan for how to acquire them.
- **App Store optimization (ASO)** — no strategy for reviews, ratings, user acquisition.
- **Feature iteration loop** — how does user feedback get incorporated?

**Verdict:** High severity. A solution design that ends at "deploy" leaves the client asking "and then what?"

---