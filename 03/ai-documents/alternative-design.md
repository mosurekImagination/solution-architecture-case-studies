# Exercise 03 — Alternative Architecture Analysis (AI-Assisted)

**Exercise:** Reinsurance Reconciliation Platform — B2B Trust Infrastructure
**Author:** Tomasz Mosur
**Date:** 2026-04-16
**Type:** AI-assisted alternative architecture analysis — produced as part of the mentorship exercise simulation

> This report re-reads only `key-informations.md` as the input and evaluates the solution in `solution-design.adoc` from first principles, identifying structural gaps and proposing an alternative architecture where the requirements justify a different approach.

---

## Executive Summary

The solution in `solution-design.adoc` is professionally structured and makes the right core call: PostgreSQL hash chain over blockchain, Step Functions for the approval state machine, and RLS for multi-tenancy. These decisions are sound.

However, a close re-read of `key-informations.md` against the design reveals three structural gaps that go beyond polish:

1. **The file ingestion model is wrong.** The requirements explicitly describe five distinct file types per reconciliation cycle (people tables, money movement tables, special condition tables, adjustment records, contract exceptions). The design treats all of these as a single generic `data_files` upload. This is not a minor oversight — it changes the ingestion API, the eligibility engine inputs, the state machine trigger conditions, and the data model.

2. **The approval state machine is too linear.** The requirements describe "parties exchange files, proposals, and adjustments multiple times" with "chain of 2–4+ people per cycle." The design models a single adjustment round with a single reconciliation manager. It does not allow the counterparty to submit a revised data file after a dispute, and it does not model multi-approver sign-off within the reinsurer.

3. **The infrastructure cost profile is inverted.** The workload is monthly peaks with near-zero baseline between cycles. ECS Fargate with always-running containers is optimised for sustained traffic, not monthly bursts. Lambda + Aurora Serverless v2 would cost approximately 60% less in OPEX and require no capacity planning.

The remaining gaps are moderate: the contract rule model is too simple for real longevity contracts, the technology stack (Node.js) is atypical for a financial compliance domain, and international data residency is unaddressed despite the explicit requirement for multi-country counterparties.

---

## Critical Analysis of the Current Design

| Gap | Severity | Requirement Source | What Was Missed |
|-----|----------|-------------------|-----------------|
| Single-file ingestion model | **High** | "File Content Types" table — 5 distinct types listed | All file types flattened into one `data_files` row; partial submissions not modelled; eligibility engine receives a single input instead of a typed file set |
| Linear approval state machine | **High** | "multi-round reconciliation… chain of 2–4+ people" | Only one adjustment round supported; no counterparty counter-proposal flow; no multi-person reinsurer sign-off chain |
| Always-on compute for monthly workload | **Medium** | "monthly data file received" | ECS Fargate cost is dominated by idle time between month-end peaks; Lambda would match the actual usage pattern |
| Node.js for financial domain | **Medium** | "calculate who is eligible… how much" — compensation amounts are financial records | JavaScript floating-point; weaker typing; less mature financial audit library ecosystem compared to JVM stack |
| Contract rule schema too simple | **Medium** | "different formulas, different eligible populations, different percentage structures" | Example JSON covers flat-rate, age-banded contracts only; mortality tables, annuity factors, stepped rates, and multi-condition eligibility cannot be expressed in the proposed schema |
| Data residency not addressed | **Medium** | "international counterparties across multiple countries (Europe and beyond)" | Design deploys everything to eu-west-2 and eu-west-1; no mechanism to honour APAC or Americas data residency for future counterparties |
| Adjustment ledger not cross-cycle | **Low** | "Backtracks and adjustments — corrections from prior months are folded into subsequent cycles" | `adjustments` table has a `prior_cycle_id` FK but the design does not show how multi-generation adjustment chains are audited or reported |

---

## Alternative Architecture

### 1. Multi-File-Type Ingestion Model

**Current:** A single `data_files` table with one row per upload. The eligibility engine receives one S3 key. The state machine transitions to `ELIGIBILITY_RUNNING` immediately on file receipt.

**Alternative:** A typed file ingestion model where each cycle tracks the arrival status of every required file type. The eligibility engine is only triggered once all required file types for a cycle are present.

**Rationale:** In practice, a counterparty sends a people table early in the month and adjustment records from the previous month separately. The current design has no way to handle this — every upload would either trigger an incomplete calculation or require the counterparty to bundle all file types into one upload (which is not how they work today). A typed model matches the domain.

**Data model change:**

```sql
-- File type registry (per contract, which file types are required)
CREATE TABLE contract_file_types (
    id              UUID PRIMARY KEY,
    contract_id     UUID NOT NULL REFERENCES contracts(id),
    file_type       TEXT NOT NULL,  -- PEOPLE_TABLE | MONEY_MOVEMENT | SPECIAL_CONDITIONS | ADJUSTMENT_RECORDS | CONTRACT_EXCEPTIONS
    required        BOOLEAN NOT NULL DEFAULT true,
    validation_schema JSONB  -- JSON Schema for structure validation of this file type
);

-- Typed file submissions (replaces current data_files table)
CREATE TABLE cycle_files (
    id              UUID PRIMARY KEY,
    cycle_id        UUID NOT NULL REFERENCES reconciliation_cycles(id),
    file_type       TEXT NOT NULL,
    s3_key          TEXT NOT NULL,
    sha256_checksum TEXT NOT NULL,
    uploaded_by     UUID NOT NULL REFERENCES users(id),
    uploaded_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (cycle_id, file_type)  -- one submission per file type per cycle
);

-- Cycle readiness view: is the cycle ready to trigger eligibility?
-- A cycle is ready when all required file types for its contract have been submitted.
CREATE VIEW cycle_readiness AS
SELECT
    rc.id AS cycle_id,
    rc.contract_id,
    COUNT(cft.id) FILTER (WHERE cft.required = true) AS required_count,
    COUNT(cf.id) FILTER (WHERE cft.required = true AND cf.id IS NOT NULL) AS received_count,
    COUNT(cft.id) FILTER (WHERE cft.required = true) =
    COUNT(cf.id) FILTER (WHERE cft.required = true AND cf.id IS NOT NULL) AS is_ready
FROM reconciliation_cycles rc
JOIN contract_file_types cft ON cft.contract_id = rc.contract_id
LEFT JOIN cycle_files cf ON cf.cycle_id = rc.id AND cf.file_type = cft.file_type
GROUP BY rc.id, rc.contract_id;
```

**State machine change:** The workflow pauses at `AWAITING_FILES` until `cycle_readiness.is_ready = true`. A Lambda function polling this view (triggered by each S3 upload via EventBridge) starts the eligibility execution only when the cycle is complete. Individual file uploads each produce `FILE_UPLOADED` audit events; a separate `CYCLE_FILES_COMPLETE` event triggers the eligibility engine.

---

### 2. Richer Approval State Machine

**Current:** `REINSURER_REVIEW` → `REINSURER_APPROVED` or `ADJUSTMENT_REQUESTED` → `COUNTERPARTY_REVIEW` → `CYCLE_SIGNED`. One adjustment round. One reinsurer approver.

**Alternative:** A multi-round negotiation model where:
- The counterparty can submit a revised data file at any point before the cycle is sealed (re-triggering eligibility)
- Multiple reinsurer approvers must sign off in sequence (minimum: reconciliation manager + senior manager for cycles above a threshold amount)
- The counterparty can issue a formal counter-proposal (their own eligibility calculation) rather than just accepting or rejecting the reinsurer's proposal

**Rationale:** The requirements explicitly state "chain of 2–4+ people per cycle" and "parties exchange files… multiple times." The current state machine models one person and one exchange. This would fail to capture the actual approval process for any non-trivial cycle.

**Revised state machine:**

```
AWAITING_FILES
  └─► FILES_COMPLETE (all required file types received)
        └─► ELIGIBILITY_RUNNING
              └─► PROPOSAL_READY
                    └─► REINSURER_REVIEW_L1 (Reconciliation Manager)
                          ├─► [approved] REINSURER_REVIEW_L2 (if amount > threshold)
                          │     ├─► [approved] COUNTERPARTY_REVIEW
                          │     └─► [adjusted] REINSURER_REVIEW_L1 (loop back)
                          ├─► [adjusted] REINSURER_REVIEW_L1 (adjustment note sent to counterparty)
                          │     └─► COUNTERPARTY_RESPONDING
                          │           ├─► [revised file] ELIGIBILITY_RUNNING (re-compute)
                          │           ├─► [counter-proposal] REINSURER_COUNTER_REVIEW
                          │           └─► [accepted] REINSURER_REVIEW_L1
                          └─► [escalated] ESCALATED
                                └─► REINSURER_REVIEW_L1

COUNTERPARTY_REVIEW
  ├─► [counter-signed] CYCLE_SIGNED (sealed)
  ├─► [counter-proposal submitted] REINSURER_COUNTER_REVIEW
  └─► [revised file submitted] ELIGIBILITY_RUNNING (full re-compute)
```

**Step Functions impact:** Use a sub-workflow for each approval level (L1, L2) so the number of levels is configurable per contract tier — the Step Functions definition does not change when a new approval level is added.

---

### 3. Serverless Infrastructure

**Current:** ECS Fargate (API service, 2+ always-running tasks) + RDS PostgreSQL Multi-AZ (db.r6g.large, ~$480/month).

**Alternative:** Lambda + API Gateway for the API layer; Aurora Serverless v2 for the database.

**Rationale:** This is a monthly-cycle platform. Between month-end peaks, API traffic is near zero (a few portal logins per week). ECS Fargate charges for reserved capacity regardless of utilisation. Lambda charges only for invocations. Aurora Serverless v2 scales to near-zero ACUs between peaks.

**OPEX comparison:**

| Service | Current Design | Alternative |
|---------|---------------|-------------|
| API compute | ECS Fargate (2 tasks, always-on): ~$380/month | Lambda + API Gateway: ~$30–50/month (at this request volume) |
| Database | RDS db.r6g.large Multi-AZ: ~$480/month | Aurora Serverless v2 (0.5–8 ACU): ~$150–280/month |
| Eligibility Engine | ECS Fargate on-demand tasks: ~$40/month (triggered ~20×/month) | Lambda (15-min max, sufficient for most files): ~$5/month |
| Everything else | ~$740/month | ~$740/month (same) |
| **Total OPEX** | **~$1,640/month** | **~$925–1,075/month** |
| **Saving** | — | **~$600/month (~36% reduction)** |

**Caveat:** Lambda has a 15-minute execution timeout. If a counterparty's people table is very large (>500K individuals), eligibility processing could exceed this limit. The mitigation is a chunked processing pattern: the eligibility engine splits the input file into batches, processes each as a separate Lambda invocation, and the Step Functions state machine fans out and joins the results. This adds complexity; at initial scale (10–30 counterparties, typical portfolio size) a single Lambda invocation will suffice.

**Aurora Serverless v2 note:** RLS, pgaudit, and the hash-chain audit ledger all work identically on Aurora PostgreSQL-compatible. The minimum ACU (0.5 ACU ≈ 1 GB RAM) means the database is never completely off, but scales automatically during month-end processing without any configuration change.

---

### 4. Java/Kotlin API Service

**Current:** Node.js (ECS Fargate) for the API service.

**Alternative:** Kotlin + Spring Boot for the API service (Lambda-compatible via AWS Lambda Web Adapter or GraalVM native compilation).

**Rationale:** Three domain-specific concerns favour the JVM stack:

- **Decimal arithmetic:** Compensation amounts are financial records. JavaScript's `Number` type uses IEEE 754 double precision, which cannot represent all decimal fractions exactly. A calculation of `120.00 × 1,234 = 148,080.0000000001` is a compliance risk. Java's `BigDecimal` provides exact decimal arithmetic as a first-class type. Node.js can work around this with libraries (`decimal.js`), but it requires discipline and code review for every calculation.
- **Spring Audit:** Spring Data JPA's `@Audited` annotation + Hibernate Envers provides entity-level change history out of the box — useful as a secondary audit layer alongside the hash-chain ledger for operational debugging.
- **Enterprise compliance ecosystem:** Libraries for SWIFT message formatting, actuarial calculations, and Solvency II report generation are predominantly available on the JVM. If the platform later needs to generate standardised regulatory output formats, the library choices are narrower on Node.

**GraalVM tradeoff:** Kotlin compiled to GraalVM native image achieves Lambda-compatible cold-start times (~150ms) comparable to Node.js. Without GraalVM, JVM Lambda cold starts are 2–5 seconds — acceptable for background processing but noticeable for the portal API. The alternative architecture assumes GraalVM compilation in CI; if that complexity is not acceptable, keep Node.js and enforce `BigDecimal` discipline via linting rules.

---

### 5. Contract Rule Evaluator

**Current:** Contract rules stored as JSON; a custom Python eligibility engine parses the JSON and applies the rules. The engine code must be updated whenever a new rule type is introduced.

**Alternative:** Contract rules stored as a structured expression tree; the eligibility engine uses an embedded expression evaluator (e.g., Spring Expression Language (SpEL) or MVEL for JVM, or a simple AST interpreter for Python) to evaluate rule conditions without code changes.

**Rationale:** The requirements state the system "must accept a contract definition as structured metadata… must not constrain contract authors to a rigid schema that breaks when a new contract type is introduced." The current JSON schema (`min_age`, `base_rate_per_individual`) is a flat structure that breaks the moment a contract has stepped rates by age band, multi-condition eligibility, or annuity factor tables. Every new contract type requires a Python code change and a deployment.

**Expression tree approach:**

```json
{
  "schema_version": "2.0",
  "contract_ref": "CP-042-LR",
  "eligibility_rule": {
    "type": "AND",
    "conditions": [
      { "type": "range", "field": "age", "min": 60, "max": 90 },
      { "type": "in", "field": "policy_type", "values": ["annuity", "pension"] },
      { "type": "not", "condition": { "type": "in", "field": "policy_type", "values": ["term_life"] } }
    ]
  },
  "compensation_rule": {
    "type": "tiered",
    "tiers": [
      { "age_max": 70, "rate_per_individual": 100.00 },
      { "age_max": 80, "rate_per_individual": 120.00 },
      { "age_max": 90, "rate_per_individual": 150.00 }
    ],
    "currency": "GBP"
  }
}
```

The engine evaluates `eligibility_rule` as a boolean expression tree and evaluates `compensation_rule` as a computation tree — both without any case-specific code. New field types (mortality rate lookup, annuity factor table) are added once to the evaluator, then usable across all contracts without per-contract changes.

**Validation:** The eligibility engine validates the rule JSON against a versioned JSON Schema at contract upload time. Unknown node types are rejected immediately. The `schema_version` field ensures older rule sets continue to work even as the evaluator gains new capabilities.

---

### 6. Data Residency Strategy

**Current:** All data in eu-west-2 (London) with DR to eu-west-1 (Ireland). No mechanism for counterparties in other jurisdictions.

**Alternative:** Tenant-tagged residency zones with a documented partitioning path.

**Rationale:** The requirements state "international counterparties across multiple countries (Europe and beyond)." GDPR applies to EU counterparties but not to UK, APAC, or Americas counterparties. Some jurisdictions (Australia, Canada, some US states) have their own data localisation requirements that may prohibit storing personal data in UK/EU regions.

**Approach:**
1. Add a `data_residency_zone` field to the `tenants` table (`EU`, `UK`, `APAC`, `NA` — initially all `UK`).
2. For Phase 1, all tenants use the single eu-west-2 deployment. The field is purely documentary.
3. When a counterparty requires a different zone, the architecture supports deploying an additional regional stack (same Terraform module, different AWS region). The central RLS-based DB remains for UK/EU tenants; non-EU tenants are provisioned on the appropriate regional stack.
4. Contract and audit data for a tenant are stored exclusively in their residency zone — no cross-zone copies.

This adds no operational cost in Phase 1 and gives the platform a credible answer to a question that will arise as counterparty count grows internationally.

---

## Cost Comparison

### CAPEX

The alternative architecture has a higher CAPEX than the current design: Kotlin + Spring Boot requires senior JVM engineers (typical rate premium: ~10–15% vs. Node.js); GraalVM native compilation adds CI configuration effort (estimated +2 weeks); the multi-file-type ingestion model and richer state machine add approximately 4–6 weeks of development versus the current design.

| Cost Component | Current Design | Alternative |
|----------------|---------------|-------------|
| Development team (same roles) | ~$534K | ~$580K (+$46K for JVM premium + complexity) |
| Contingency (20%) | ~$107K | ~$116K |
| **Total CAPEX** | **~$640K** | **~$700K** |
| Premium | — | +~$60K (+9%) |

### OPEX

| Service | Current | Alternative | Delta |
|---------|---------|-------------|-------|
| API compute | ~$380/month (ECS Fargate) | ~$40/month (Lambda) | -$340 |
| Database | ~$480/month (RDS fixed) | ~$200/month (Aurora Serverless v2) | -$280 |
| Eligibility compute | ~$40/month (Fargate tasks) | ~$5/month (Lambda) | -$35 |
| All other services | ~$740/month | ~$740/month | — |
| **Total OPEX** | **~$1,640/month** | **~$985/month** | **-$655/month** |

### 3-Year TCO

| | Current | Alternative |
|---|---------|-------------|
| CAPEX | $640K | $700K |
| 3-year OPEX | ~$59K | ~$36K |
| **3-year TCO** | **~$699K** | **~$736K** |

At 3 years, the alternative costs ~$37K more in total despite lower OPEX — because the upfront CAPEX premium is larger than the OPEX savings over 3 years. At 5 years, the alternative breaks even.

**Conclusion on cost:** The alternative is not primarily justified by cost savings. It is justified by correctness of the domain model and fitness for the actual workload profile. The $37K 3-year TCO difference is negligible for an innovation initiative. However, if the primary goal is minimising cost risk, the current design's fixed-cost model is more predictable.

---

## Trade-off Summary

| Dimension | Current Design | Alternative | Winner |
|-----------|---------------|-------------|--------|
| Domain model accuracy | Generic file ingestion; linear approval | Typed file model; multi-round negotiation | **Alternative** |
| Approval model fidelity | 1 approver, 1 adjustment round | Multi-level sign-off, counter-proposal support | **Alternative** |
| OPEX efficiency | Higher (always-on compute) | Lower (pay-per-use) | **Alternative** |
| Technology risk | Low (Node.js, Python, ECS — well-understood) | Medium (GraalVM, Aurora Serverless v2 — newer) | **Current** |
| Build complexity | Lower | Higher (+4–6 weeks) | **Current** |
| Financial domain fit | Requires workarounds (BigDecimal library) | First-class (JVM BigDecimal) | **Alternative** |
| Contract rule extensibility | New rule type = code change | New rule type = schema extension only | **Alternative** |
| Data residency | Not addressed | Documented partitioning path | **Alternative** |
| Team knowledge requirements | Broad (any senior dev can contribute) | Narrower (requires JVM + Spring Boot experience) | **Current** |
| 3-year TCO | ~$699K | ~$736K | **Current** (marginally) |

---

## Recommendation

**Use the current design** if:
- The team does not have strong JVM experience and hiring is constrained
- The pilot is 10 or fewer counterparties with a single, well-understood contract type
- Timeline is the primary constraint (current design ships ~6 weeks faster)
- GraalVM native compilation is not within the team's operational capability

**Use the alternative** if:
- More than 15 counterparties are expected at launch (the linear state machine becomes operationally unworkable at scale)
- Contract types are varied and complex from day one (the rule evaluator is necessary, not optional)
- The team has JVM (Spring Boot) experience available
- The reinsurer's compliance team requires multi-approver sign-off chains to be formally modelled (not just documented as a manual process)

**The most impactful single change** that could be taken from the alternative and applied to the current design without a full rewrite: the **multi-file-type ingestion model**. This is a data model and API change that does not require changing the technology stack. Implementing it within the current Node.js + ECS Fargate design would address the highest-severity gap at low added cost. The other changes (serverless compute, JVM stack, rule evaluator) can be evaluated independently.

---

## Summary Scorecard

| Dimension | Current Design | Alternative |
|-----------|---------------|-------------|
| Domain model accuracy | 2/5 — single-file model misses 4 of 5 file types | 5/5 |
| Approval workflow fidelity | 2/5 — one approver, one adjustment round | 4/5 |
| Cost efficiency | 3/5 — over-provisioned for monthly workload | 4/5 |
| Technical risk | 5/5 — proven stack | 3/5 — GraalVM + Aurora Serverless v2 newer |
| Contract extensibility | 2/5 — requires code change per new rule type | 4/5 |
| Build speed | 5/5 — 8 months | 3/5 — ~9.5 months |
| Financial domain fitness | 3/5 — workarounds needed | 5/5 |
| **Overall** | **3.1/5** | **4.0/5** |
