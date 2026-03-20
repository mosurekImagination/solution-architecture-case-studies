"""
Financial Model — Data-Driven Customer Engagement Platform
==========================================================
Single source of truth for all numbers in:
  - 02/docs/solution-design.adoc
  - 02/docs/solution-design-proposal.adoc

Edit values here, run:  python capex.py
Then copy the printed numbers into both documents.
"""

# ── CAPEX: Roles ───────────────────────────────────────────────────────────────
roles = [
    {"role": "Data Engineer",       "count": 2,   "rate_mo": 15_000, "months": 6},
    {"role": "Backend Developer",   "count": 1,   "rate_mo": 12_000, "months": 5},
    {"role": "ML / Data Scientist", "count": 1,   "rate_mo": 15_000, "months": 4},
    {"role": "QA Engineer",         "count": 1,   "rate_mo":  8_000, "months": 4},
    {"role": "Solution Architect",  "count": 0.5, "rate_mo": 18_000, "months": 6},
]

# ── CAPEX: Lump sums ───────────────────────────────────────────────────────────
cloud_and_infra = 15_000   # Snowflake account, AWS environments, Terraform, CI/CD,
                            # VPN setup (on-prem → AWS, required for read replica DAGs)
training        = 10_000   # Materials, external workshops

# ── CAPEX: Contingency ─────────────────────────────────────────────────────────
CONTINGENCY_PCT = 0.20     # 20% — recommended minimum for data projects with unknowns

# ── OPEX: Monthly ranges (low, high) ──────────────────────────────────────────
opex = {
    "Snowflake":          (3_000,  8_000),
    "AWS Infrastructure": (1_000,  3_000),
    "AWS SES (Email)":    (  100,    500),
    "Monitoring":         (  500,  1_000),
    "AWS MWAA":           (  300,  1_500),
    "Contingency (15%)":  (  700,  2_000),
}

# ── ROI: Illustrative assumptions ─────────────────────────────────────────────
DAILY_VISITORS   = 1_000_000
CONVERSION_RATE  = 0.02        # 2% of visitors make a purchase
AVG_BASKET       = 15          # USD — illustrative; scale to actual AOV

# Uplift scenarios (basket size increase from personalisation alone)
scenarios = [
    ("Conservative maturity",  0.05),   #  5% basket uplift — 12–18 months post-kickoff
    ("Optimistic maturity",    0.15),   # 15% basket uplift — 24–36 months post-kickoff (upper industry benchmark)
]

# ── TCO: Years to project ─────────────────────────────────────────────────────
TCO_YEARS = 3


# ══════════════════════════════════════════════════════════════════════════════
#  Calculations
# ══════════════════════════════════════════════════════════════════════════════

role_costs  = {r["role"]: r["count"] * r["rate_mo"] * r["months"] for r in roles}
lump_total  = cloud_and_infra + training
subtotal    = sum(role_costs.values()) + lump_total
contingency = subtotal * CONTINGENCY_PCT
capex_total = subtotal + contingency

opex_lo = sum(v[0] for v in opex.values())
opex_hi = sum(v[1] for v in opex.values())

year1_opex_lo = opex_lo * 12
year1_opex_hi = opex_hi * 12

tco_lo = capex_total + opex_lo * 12 * TCO_YEARS
tco_hi = capex_total + opex_hi * 12 * TCO_YEARS

daily_purchasers = DAILY_VISITORS * CONVERSION_RATE


# ══════════════════════════════════════════════════════════════════════════════
#  Output
# ══════════════════════════════════════════════════════════════════════════════

W = 58

def section(title):
    print()
    print("=" * W)
    print(f"  {title}")
    print("=" * W)

def divider():
    print("-" * W)

section("CAPEX Breakdown")
for r in roles:
    cost  = role_costs[r["role"]]
    label = r["role"] + (f" ×{r['count']}" if r["count"] != 1 else "")
    detail = f"{r['count']} × ${r['rate_mo']:,}/mo × {r['months']}mo"
    print(f"  {label:<28} {detail:<24} ${cost:>9,.0f}")
print(f"  {'Cloud Setup & CI/CD':<28} {'lump sum':<24} ${cloud_and_infra:>9,.0f}")
print(f"  {'Training':<28} {'lump sum':<24} ${training:>9,.0f}")
divider()
print(f"  {'Subtotal':<53} ${subtotal:>9,.0f}")
print(f"  {'Contingency':<28} {CONTINGENCY_PCT:.0%} of subtotal"
      f"{'':>16} ${contingency:>9,.0f}")
print("=" * W)
print(f"  {'TOTAL CAPEX':<53} ${capex_total:>9,.0f}")
print("=" * W)

# ── Per-phase approximation ────────────────────────────────────────────────────
MONTH_PER_PH = 10 / 4.33   # 10 weeks ≈ 2.31 months per phase

phase1_roles = [
    ("Data Engineer",      2,   15_000, 1.0),
    ("Solution Architect", 0.5, 18_000, 1.0),
    ("QA Engineer",        1,    8_000, 0.25),
]
phase2_roles = [
    ("Data Engineer",      1,   15_000, 1.0),
    ("Backend Developer",  1,   12_000, 1.0),
    ("ML / Data Scientist",1,   15_000, 1.0),
    ("QA Engineer",        1,    8_000, 1.0),
    ("Solution Architect", 0.5, 18_000, 1.0),
]
phase3_roles = [
    ("Data Engineer",      1,   15_000, 1.0),
    ("Backend Developer",  1,   12_000, 1.0),
    ("QA Engineer",        1,    8_000, 0.5),
]

def phase_cost(phase_roles):
    return sum(c * f * r * MONTH_PER_PH for _, c, r, f in phase_roles)

p1, p2, p3 = phase_cost(phase1_roles), phase_cost(phase2_roles), phase_cost(phase3_roles)

section("Per-Phase Cost  (approximate — for planning)")
print(f"  Phase 1  Foundation & WordPress Pipeline    ${p1:>9,.0f}")
print(f"  Phase 2  Suggestion Engine & Email Channel  ${p2:>9,.0f}")
print(f"  Phase 3  Mobile & Wholesaler Expansion      ${p3:>9,.0f}")
print(f"  Cloud Setup + Training                      ${lump_total:>9,.0f}")
print(f"  Contingency ({CONTINGENCY_PCT:.0%})                              ${contingency:>9,.0f}")
divider()
print(f"  Authoritative TOTAL CAPEX                   ${capex_total:>9,.0f}")
print(f"  (Per-phase windows are equal 2.31-month slices;")
print(f"   role durations differ — phases are illustrative.)")
print("=" * W)

section("OPEX (Monthly)")
for service, (lo, hi) in opex.items():
    print(f"  {service:<30} ${lo:>6,} – ${hi:>6,}/mo")
divider()
print(f"  {'TOTAL OPEX':<30} ${opex_lo:>6,} – ${opex_hi:>6,}/mo")
print("=" * W)

section("TCO")
print(f"  CAPEX                                       ${capex_total:>9,.0f}")
print(f"  Year 1 OPEX  ({opex_lo:,}–{opex_hi:,}/mo × 12)    ${year1_opex_lo:>9,} – ${year1_opex_hi:,}")
print(f"  {TCO_YEARS}-Year OPEX  ({opex_lo:,}–{opex_hi:,}/mo × {TCO_YEARS*12})"
      f"   ${opex_lo*12*TCO_YEARS:>9,} – ${opex_hi*12*TCO_YEARS:,}")
divider()
print(f"  {TCO_YEARS}-Year TCO                                 "
      f"${tco_lo:>9,.0f} – ${tco_hi:,.0f}")
print("=" * W)

section("ROI Projection  (illustrative)")
print(f"  Daily visitors:    {DAILY_VISITORS:,}")
print(f"  Conversion rate:   {CONVERSION_RATE:.0%}  ->  {daily_purchasers:,.0f} purchasers/day")
print(f"  Average basket:    ${AVG_BASKET}")
print()
for label, uplift in scenarios:
    basket_uplift   = AVG_BASKET * uplift
    daily_uplift    = daily_purchasers * basket_uplift
    monthly_uplift  = daily_uplift * 30
    breakeven_mo    = capex_total / monthly_uplift
    print(f"  {label} ({uplift:.0%} basket uplift):")
    print(f"    Basket: ${AVG_BASKET} -> ${AVG_BASKET + basket_uplift:.2f}  (+${basket_uplift:.2f}/order)")
    print(f"    Daily uplift:   ${daily_uplift:>10,.0f}/day")
    print(f"    Monthly uplift: ${monthly_uplift:>10,.0f}/month")
    print(f"    CAPEX break-even: {breakeven_mo:.1f} months post-maturity")
    print()
print("=" * W)

section("Numbers for Documents  (copy-paste)")
print(f"  CAPEX total:        ~${capex_total/1000:.0f}K  (exact: ${capex_total:,})")
print(f"  Subtotal:           ${subtotal:,}")
print(f"  Contingency:        {CONTINGENCY_PCT:.0%} / ${contingency:,.0f}")
print(f"  OPEX/month:         ${opex_lo//1000}K–${opex_hi//1000}K")
print(f"  Year 1 OPEX:        ~${year1_opex_lo//1000}K–${year1_opex_hi//1000}K")
print(f"  3-Year TCO:         ~${tco_lo/1000:.0f}K–${tco_hi/1000:.0f}K")
conservative_monthly = daily_purchasers * AVG_BASKET * scenarios[0][1] * 30
target_monthly       = daily_purchasers * AVG_BASKET * scenarios[1][1] * 30
print(f"  Conservative uplift: +${conservative_monthly:,.0f}/month")
print(f"  Target uplift:       +${target_monthly:,.0f}/month")
print("=" * W)
