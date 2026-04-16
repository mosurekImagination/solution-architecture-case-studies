"""
Project Financials — Reinsurance Reconciliation Platform
========================================================
Single source of truth for ALL numbers in:
  - 03/docs/solution-design.adoc
  - 03/docs/solution-design-proposal.adoc

Every number that appears in either document — costs, durations, team sizes,
phase milestones, savings projections — must originate from this script.

Edit values here, run:  python financials.py
Then copy the printed numbers into both documents.
"""

import math
import sys
import io
from dataclasses import dataclass

# Ensure UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ══════════════════════════════════════════════════════════════════════════════
#  INPUTS
# ══════════════════════════════════════════════════════════════════════════════

# ── Team Composition ───────────────────────────────────────────────────────────
@dataclass
class Role:
    title: str
    count: int | float
    rate_mo: int
    months: float
    deliverables: str

roles = [
    Role("Solution Architect",            1, 15_000, 9.5, "Architecture, ADRs, oversight"),
    Role("Senior Developer",              3, 12_000, 9.5, "API, eligibility engine, portal, audit ledger"),
    Role("Security / Compliance Engineer", 1, 13_000, 7,   "RLS, Cognito, WAF, penetration tests"),
    Role("QA Engineer",                   1,  8_000, 7,   "Test suites, UAT coordination"),
]

TEAM_SIZE = sum(r.count for r in roles)  # total headcount

# ── Contingency ────────────────────────────────────────────────────────────────
CONTINGENCY_PCT = 0.20     # 20 %

# ── Phases ─────────────────────────────────────────────────────────────────────
@dataclass
class Phase:
    number: int
    name: str
    scope: str
    months: float
    team_label: str
    roles: list  # [(title, count, rate_mo), ...]

phases = [
    Phase(1,
          "Infrastructure & Auth",
          "Infrastructure, Auth, Contract Registry, Multi-File Ingestion",
          2.5,
          "Architect + 2 Devs + Security",
          [("Solution Architect", 1, 15_000),
           ("Senior Developer",   2, 12_000),
           ("Security / Compliance Engineer", 1, 13_000)]),
    Phase(2,
          "Eligibility & Workflow",
          "Eligibility Engine (expression tree), Multi-Level Approval Workflow, Audit Ledger",
          2.5,
          "Full team",
          [("Solution Architect", 1, 15_000),
           ("Senior Developer",   3, 12_000),
           ("Security / Compliance Engineer", 1, 13_000),
           ("QA Engineer",        1,  8_000)]),
    Phase(3,
          "Portal & Onboarding",
          "Multi-Tenant Portal, Notifications, First Counterparty Onboarding",
          2.5,
          "Full team",
          [("Solution Architect", 1, 15_000),
           ("Senior Developer",   3, 12_000),
           ("Security / Compliance Engineer", 1, 13_000),
           ("QA Engineer",        1,  8_000)]),
    Phase(4,
          "Reporting & Go-Live",
          "Regulatory Reporting, Data Residency, Second Counterparty Batch, Performance Testing, Go-Live",
          2.0,
          "Full team + QA",
          [("Solution Architect", 1, 15_000),
           ("Senior Developer",   3, 12_000),
           ("Security / Compliance Engineer", 1, 13_000),
           ("QA Engineer",        1,  8_000)]),
]

NUM_PHASES = len(phases)

# ── OPEX: Monthly costs (base) ────────────────────────────────────────────────
opex_base = {
    "Aurora Serverless v2 (0.5-8 ACU)":       200,
    "Lambda + API Gateway":                     45,
    "S3 (file storage + audit backups ~500GB)": 80,
    "Step Functions (Standard Workflows)":      40,
    "Cognito (up to 1,000 MAU)":                55,
    "SES (email notifications)":                15,
    "CloudFront + WAF (OWASP rules)":          120,
    "CloudWatch (logs, metrics, alarms)":       80,
    "AWS Backup + S3 Glacier (10yr retention)": 150,
    "AWS Transfer Family SFTP (opt-in)":       200,
}

DR_OVERHEAD_PER_MONTH = 815  # cross-region DR replication (eu-west-1)

# ── TCO ────────────────────────────────────────────────────────────────────────
TCO_YEARS = 3

# ── Headcount savings (proposal ROI) ──────────────────────────────────────────
CURRENT_HEADCOUNT      = 100
RECONCILIATION_SALARY  = 55_000   # GBP/year — illustrative UK market rate
REDUCTION_CONSERVATIVE = 0.50     # 2× reduction (100 → 50)
REDUCTION_OPTIMISTIC   = 0.75     # 4× reduction (100 → 25)

# ── Currency ───────────────────────────────────────────────────────────────────
GBP_USD = 1.28   # illustrative; actual rate confirmed during Investigation Period

# ── Counterparty adoption ramp ────────────────────────────────────────────────
ONBOARDING_RATE_PER_MONTH = 1.5   # average: 1–2 counterparties per month
ESTIMATED_COUNTERPARTIES  = 15    # total counterparties to onboard

# ── Solution Options (side-by-side comparison in solution design) ─────────────
options = [
    {"label": "Option 1: Lightweight Portal", "capex": 165_000, "opex_lo":  800, "opex_hi":   800, "timeline_mo": 3,  "team": "1 Architect + 2 Developers + 1 QA"},
    {"label": "Option 2: Full Platform",       "capex": None,    "opex_lo": None, "opex_hi":  None, "timeline_mo": None, "team": None},  # calculated
    {"label": "Option 3: Event-Sourced",       "capex": 1_100_000, "opex_lo": 4_500, "opex_hi": 5_500, "timeline_mo": 13, "team": "1 Architect + 4 Developers + 1 Security + 1 Data Engineer + 1 QA"},
]


# ══════════════════════════════════════════════════════════════════════════════
#  CALCULATIONS
# ══════════════════════════════════════════════════════════════════════════════

# CAPEX
role_costs  = {r.title: r.count * r.rate_mo * r.months for r in roles}
subtotal    = sum(role_costs.values())
contingency = subtotal * CONTINGENCY_PCT
capex_total = subtotal + contingency

# Timeline
total_months = sum(p.months for p in phases)

# Milestone months (cumulative)
milestone_months = []
cumulative = 0
for p in phases:
    cumulative += p.months
    milestone_months.append(cumulative)

first_counterparty_live_mo = milestone_months[2]   # end of Phase 3
full_golive_mo             = milestone_months[3]    # end of Phase 4

# Phase costs
phase_costs = []
for p in phases:
    cost = sum(count * rate * p.months for _, count, rate in p.roles)
    phase_costs.append(cost)

# OPEX
opex_base_total = sum(opex_base.values())
opex_dr_total   = opex_base_total + DR_OVERHEAD_PER_MONTH

year1_opex_lo = opex_base_total * 12
year1_opex_hi = opex_dr_total * 12

# TCO
tco_lo = capex_total + opex_base_total * 12 * TCO_YEARS
tco_hi = capex_total + opex_dr_total   * 12 * TCO_YEARS

# Option 2 = calculated values
options[1]["capex"]       = capex_total
options[1]["opex_lo"]     = opex_base_total
options[1]["opex_hi"]     = opex_dr_total
options[1]["timeline_mo"] = total_months
options[1]["team"]        = f"1 Architect + {int(roles[1].count)} Developers + 1 Security + 1 QA"

# Headcount savings
headcount_after_conservative = int(CURRENT_HEADCOUNT * (1 - REDUCTION_CONSERVATIVE))
headcount_after_optimistic   = int(CURRENT_HEADCOUNT * (1 - REDUCTION_OPTIMISTIC))
reduction_factor_conservative = int(1 / (1 - REDUCTION_CONSERVATIVE))
reduction_factor_optimistic   = int(1 / (1 - REDUCTION_OPTIMISTIC))

annual_saving_conservative = CURRENT_HEADCOUNT * REDUCTION_CONSERVATIVE * RECONCILIATION_SALARY
annual_saving_optimistic   = CURRENT_HEADCOUNT * REDUCTION_OPTIMISTIC   * RECONCILIATION_SALARY
breakeven_conservative_mo  = capex_total / (annual_saving_conservative / 12)
breakeven_optimistic_mo    = capex_total / (annual_saving_optimistic / 12)

# Currency-converted CAPEX for break-even comparison (USD → GBP)
capex_gbp = capex_total / GBP_USD

# Adoption ramp: months from go-live to full counterparty onboarding
adoption_ramp_months = math.ceil(ESTIMATED_COUNTERPARTIES / ONBOARDING_RATE_PER_MONTH)

# Time-to-value: go-live + ramp period during which savings accrue incrementally.
# During ramp, average saving is ~50% of full rate (linear counterparty onboarding).
# Break-even from kickoff = delivery + (capex_gbp / half-rate monthly saving).
ramp_breakeven_conservative_mo = capex_gbp / ((annual_saving_conservative * 0.5) / 12)
ramp_breakeven_optimistic_mo   = capex_gbp / ((annual_saving_optimistic   * 0.5) / 12)
time_to_value_conservative = full_golive_mo + ramp_breakeven_conservative_mo
time_to_value_optimistic   = full_golive_mo + ramp_breakeven_optimistic_mo
full_savings_from_kickoff_mo = full_golive_mo + adoption_ramp_months


# ══════════════════════════════════════════════════════════════════════════════
#  ADOC ATTRIBUTE EXPORT
# ══════════════════════════════════════════════════════════════════════════════

def write_adoc_attrs():
    """Write AsciiDoc attribute file consumed by include:: in .adoc documents."""
    from pathlib import Path

    opex_items = list(opex_base.items())

    team_short = (f"1 Architect + {int(roles[1].count)} Developers"
                  f" + 1 Security + 1 QA")
    team_long = (f"1 Architect + {int(roles[1].count)} Senior Developers"
                 f" + 1 Security Engineer + 1 QA Engineer")

    attrs = {
        # ── CAPEX ────────────────────────────────────────────────────────
        "capex-exact":          f"${capex_total:,.0f}",
        "capex-approx":         f"~${capex_total / 1000:.0f}K",
        "capex-gbp-exact":      f"£{capex_gbp:,.0f}",
        "capex-gbp-approx":     f"~£{capex_gbp / 1000:.0f}K",
        "subtotal":             f"${subtotal:,.0f}",
        "contingency-pct":      f"{CONTINGENCY_PCT:.0%}",
        "contingency-amount":   f"${contingency:,.0f}",
        "contingency-approx":   f"~${contingency / 1000:.0f}K",

        # Per-role (for solution-design CAPEX table)
        "architect-rate":       f"${roles[0].rate_mo:,}",
        "architect-months":     f"{roles[0].months}",
        "architect-cost":       f"${role_costs[roles[0].title]:,.0f}",
        "dev-count":            f"{int(roles[1].count)}",
        "dev-rate":             f"${roles[1].rate_mo:,}",
        "dev-months":           f"{roles[1].months}",
        "dev-cost":             f"${role_costs[roles[1].title]:,.0f}",
        "security-rate":        f"${roles[2].rate_mo:,}",
        "security-months":      f"{roles[2].months}",
        "security-cost":        f"${role_costs[roles[2].title]:,.0f}",
        "qa-rate":              f"${roles[3].rate_mo:,}",
        "qa-months":            f"{roles[3].months}",
        "qa-cost":              f"${role_costs[roles[3].title]:,.0f}",

        # Per-phase
        "phase-1-months":       f"{phases[0].months}",
        "phase-2-months":       f"{phases[1].months}",
        "phase-3-months":       f"{phases[2].months}",
        "phase-4-months":       f"{phases[3].months}",
        "phase-1-cost-approx":  f"~${phase_costs[0] / 1000:.0f}K",
        "phase-2-cost-approx":  f"~${phase_costs[1] / 1000:.0f}K",
        "phase-3-cost-approx":  f"~${phase_costs[2] / 1000:.0f}K",
        "phase-4-cost-approx":  f"~${phase_costs[3] / 1000:.0f}K",

        # ── OPEX ─────────────────────────────────────────────────────────
        "opex-aurora":          f"~${opex_items[0][1]:,}",
        "opex-lambda-apigw":    f"~${opex_items[1][1]:,}",
        "opex-s3":              f"~${opex_items[2][1]:,}",
        "opex-step-functions":  f"~${opex_items[3][1]:,}",
        "opex-cognito":         f"~${opex_items[4][1]:,}",
        "opex-ses":             f"~${opex_items[5][1]:,}",
        "opex-cloudfront-waf":  f"~${opex_items[6][1]:,}",
        "opex-cloudwatch":      f"~${opex_items[7][1]:,}",
        "opex-backup-glacier":  f"~${opex_items[8][1]:,}",
        "opex-sftp":            f"~${opex_items[9][1]:,}",
        "opex-base":            f"~${opex_base_total:,}/month",
        "opex-dr":              f"~${opex_dr_total:,}/month",
        "opex-range":           f"${opex_base_total:,}\u2013${opex_dr_total:,}/month",
        "dr-overhead":          f"${DR_OVERHEAD_PER_MONTH:,}",
        "year1-opex-approx":    f"~${year1_opex_lo // 1000}K\u2013${year1_opex_hi // 1000}K",

        # ── TCO ──────────────────────────────────────────────────────────
        "tco-years":            f"{TCO_YEARS}",
        "tco-range-approx":     f"~${tco_lo / 1000:.0f}K\u2013${tco_hi / 1000:.0f}K",

        # ── Timeline / Milestones ────────────────────────────────────────
        "timeline-months":      f"{total_months}",
        "num-phases":           f"{NUM_PHASES}",
        "milestone-phase-1":    f"{milestone_months[0]}",
        "milestone-phase-2":    f"{milestone_months[1]}",
        "milestone-phase-3":    f"{milestone_months[2]}",
        "milestone-phase-4":    f"{milestone_months[3]}",
        "first-cp-live-mo":     f"{first_counterparty_live_mo}",
        "full-golive-mo":       f"{full_golive_mo}",

        # ── Team ─────────────────────────────────────────────────────────
        "team-size":            f"{TEAM_SIZE:.0f}",
        "team-short":           team_short,
        "team-long":            team_long,

        # ── Headcount / Savings ──────────────────────────────────────────
        "current-headcount":                f"{CURRENT_HEADCOUNT}",
        "reconciliation-salary":            f"£{RECONCILIATION_SALARY:,}",
        "headcount-after-conservative":     f"{headcount_after_conservative}",
        "headcount-after-optimistic":       f"{headcount_after_optimistic}",
        "reduction-factor-conservative":    f"{reduction_factor_conservative}",
        "reduction-factor-optimistic":      f"{reduction_factor_optimistic}",
        "saving-conservative-approx":       f"~£{annual_saving_conservative / 1000:,.0f}K",
        "saving-conservative-per-year":     f"~£{annual_saving_conservative / 1000:,.0f}K/year",
        "saving-optimistic-approx":         f"~£{annual_saving_optimistic / 1000:,.0f}K",
        "saving-optimistic-per-year":       f"~£{annual_saving_optimistic / 1000:,.0f}K/year",
        "breakeven-conservative-mo":        f"{breakeven_conservative_mo:.1f}",
        "breakeven-optimistic-mo":          f"{breakeven_optimistic_mo:.1f}",

        # ── Adoption Ramp / Time-to-Value ────────────────────────────────
        "adoption-ramp-months":             f"{adoption_ramp_months}",
        "onboarding-rate":                  f"{ONBOARDING_RATE_PER_MONTH}",
        "estimated-counterparties":         f"{ESTIMATED_COUNTERPARTIES}",
        "ttv-conservative":                 f"~{time_to_value_conservative:.0f}",
        "ttv-optimistic":                   f"~{time_to_value_optimistic:.0f}",

        # ── Currency ─────────────────────────────────────────────────────
        "gbp-usd":              f"{GBP_USD}",

        # ── Option 1 (Lightweight Portal) ────────────────────────────────
        "opt1-capex-approx":    f"~${options[0]['capex'] / 1000:.0f}K",
        "opt1-opex":            f"~${options[0]['opex_lo']:,}",
        "opt1-timeline":        f"{options[0]['timeline_mo']}",
        "opt1-team":            f"{options[0]['team']}",

        # ── Option 3 (Event-Sourced) ─────────────────────────────────────
        "opt3-capex-approx":    f"~$1.1M",
        "opt3-opex-range":      f"~${options[2]['opex_lo']:,}\u2013${options[2]['opex_hi']:,}",
        "opt3-timeline":        f"{options[2]['timeline_mo']}",
        "opt3-team":            f"{options[2]['team']}",
    }

    out = Path(__file__).with_name("financials-attrs.adoc")
    lines = [
        "// Auto-generated by financials.py — do not edit by hand.",
        f"// Regenerate: python {Path(__file__).name}",
        "",
    ]
    for k, v in attrs.items():
        lines.append(f":{k}: {v}")
    lines.append("")  # trailing newline

    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n  ✓ Wrote {len(attrs)} attributes → {out}")


write_adoc_attrs()


# ══════════════════════════════════════════════════════════════════════════════
#  OUTPUT
# ══════════════════════════════════════════════════════════════════════════════

W = 72

def section(title):
    print()
    print("=" * W)
    print(f"  {title}")
    print("=" * W)

def divider():
    print("-" * W)


# ── Timeline & Team ──────────────────────────────────────────────────────────
section("Timeline & Team")
print(f"  Total delivery:          {total_months} months")
print(f"  Number of phases:        {NUM_PHASES}")
print(f"  Team size:               {TEAM_SIZE:.0f} people")
print()
for i, (p, cost) in enumerate(zip(phases, phase_costs)):
    end_mo = milestone_months[i]
    print(f"  Phase {p.number}: {p.name}")
    print(f"    Duration: {p.months} months  |  Ends at month {end_mo}"
          f"  |  Team: {p.team_label}  |  ~${cost:,.0f}")
print()
print(f"  First counterparty live: month {first_counterparty_live_mo}")
print(f"  Full go-live:            month {full_golive_mo}")
print("=" * W)


# ── CAPEX ────────────────────────────────────────────────────────────────────
section("CAPEX Breakdown")
for r in roles:
    cost  = role_costs[r.title]
    label = r.title + (f" (x{r.count})" if r.count != 1 else "")
    detail = f"{r.count} x ${r.rate_mo:,}/mo x {r.months}mo"
    print(f"  {label:<38} {detail:<22} ${cost:>10,.0f}")
divider()
print(f"  {'Subtotal':<62} ${subtotal:>10,.0f}")
print(f"  {'Contingency':<38} {CONTINGENCY_PCT:.0%} of subtotal"
      f"{'':>14} ${contingency:>10,.0f}")
print("=" * W)
print(f"  {'TOTAL CAPEX':<62} ${capex_total:>10,.0f}")
print(f"  {'TOTAL CAPEX (GBP)':<62} £{capex_gbp:>10,.0f}")
print("=" * W)


# ── Per-Phase ────────────────────────────────────────────────────────────────
section("Per-Phase Cost (approximate)")
for p, cost in zip(phases, phase_costs):
    label = f"Phase {p.number} -- {p.scope[:52]}"
    print(f"  {label:<60} ${cost:>10,.0f}")
print(f"  {'Contingency (' + f'{CONTINGENCY_PCT:.0%}' + ')':<60} ${contingency:>10,.0f}")
divider()
print(f"  {'Sum of phases + contingency':<60} ${sum(phase_costs) + contingency:>10,.0f}")
print(f"  {'Authoritative TOTAL CAPEX':<60} ${capex_total:>10,.0f}")
print(f"  (Phase costs are approximate; authoritative total is role x duration.)")
print("=" * W)


# ── OPEX ─────────────────────────────────────────────────────────────────────
section("OPEX (Monthly)")
for service, cost in opex_base.items():
    print(f"  {service:<50} ${cost:>6,}/mo")
divider()
print(f"  {'Total OPEX (base)':<50} ${opex_base_total:>6,}/mo")
print(f"  {'Total OPEX (incl. DR replication)':<50} ${opex_dr_total:>6,}/mo")
print("=" * W)


# ── TCO ──────────────────────────────────────────────────────────────────────
section("TCO")
print(f"  CAPEX                                                    ${capex_total:>10,.0f}")
print(f"  Year 1 OPEX  (${opex_base_total:,}-${opex_dr_total:,}/mo x 12)"
      f"          ${year1_opex_lo:>10,} - ${year1_opex_hi:,}")
print(f"  {TCO_YEARS}-Year OPEX  (${opex_base_total:,}-${opex_dr_total:,}/mo x {TCO_YEARS * 12})"
      f"         ${opex_base_total * 12 * TCO_YEARS:>10,} - ${opex_dr_total * 12 * TCO_YEARS:,}")
divider()
print(f"  {TCO_YEARS}-Year TCO"
      f"{'':>40} ${tco_lo:>10,.0f} - ${tco_hi:,.0f}")
print("=" * W)


# ── Solution Options ─────────────────────────────────────────────────────────
section("Solution Options (side-by-side)")
for o in options:
    print(f"  {o['label']}")
    print(f"    CAPEX: ~${o['capex']:,.0f}  |  OPEX: ~${o['opex_lo']:,}-${o['opex_hi']:,}/mo"
          f"  |  Timeline: {o['timeline_mo']} months")
    print(f"    Team: {o['team']}")
    print()
print("=" * W)


# ── Headcount Savings ────────────────────────────────────────────────────────
section("Headcount Savings (illustrative, for proposal)")
print(f"  Current reconciliation headcount:     {CURRENT_HEADCOUNT}")
print(f"  Average annual salary (illustrative): £{RECONCILIATION_SALARY:,}")
print(f"  Exchange rate assumption:             £1 = ${GBP_USD} (illustrative)")
print(f"  CAPEX in GBP:                         £{capex_gbp:,.0f}")
print()
print(f"  Conservative ({reduction_factor_conservative}x reduction"
      f" -- {CURRENT_HEADCOUNT} -> {headcount_after_conservative} managers):")
print(f"    Annual saving:          £{annual_saving_conservative:,.0f}")
print(f"    Break-even (at full):   {breakeven_conservative_mo:.1f} months after full adoption")
print(f"    Break-even (with ramp): {ramp_breakeven_conservative_mo:.1f} months after go-live (inc. adoption ramp)")
print(f"    Time-to-value:          ~{time_to_value_conservative:.0f} months from kickoff")
print()
print(f"  Optimistic ({reduction_factor_optimistic}x reduction"
      f" -- {CURRENT_HEADCOUNT} -> {headcount_after_optimistic} managers):")
print(f"    Annual saving:          £{annual_saving_optimistic:,.0f}")
print(f"    Break-even (at full):   {breakeven_optimistic_mo:.1f} months after full adoption")
print(f"    Break-even (with ramp): {ramp_breakeven_optimistic_mo:.1f} months after go-live (inc. adoption ramp)")
print(f"    Time-to-value:          ~{time_to_value_optimistic:.0f} months from kickoff")
print()
print(f"  Adoption ramp:            {ESTIMATED_COUNTERPARTIES} counterparties at {ONBOARDING_RATE_PER_MONTH}/mo = ~{adoption_ramp_months} months")
print(f"  Full savings from:        ~month {full_savings_from_kickoff_mo} from kickoff")
print("=" * W)


# ── Copy-Paste Reference ────────────────────────────────────────────────────
section("Numbers for Documents (copy-paste)")
print(f"  CAPEX total:          ~${capex_total / 1000:.0f}K  (exact: ${capex_total:,.0f})")
print(f"  CAPEX total (GBP):    ~£{capex_gbp / 1000:.0f}K  (at £1 = ${GBP_USD})")
print(f"  Subtotal:             ${subtotal:,.0f}")
print(f"  Contingency:          {CONTINGENCY_PCT:.0%} / ${contingency:,.0f}")
print(f"  Timeline:             {total_months} months, {NUM_PHASES} phases")
print(f"  First CP live:        month {first_counterparty_live_mo}")
print(f"  Full go-live:         month {full_golive_mo}")
team_desc = ", ".join(
    f"{r.count:.0f} {r.title}" + ("s" if r.count > 1 else "")
    for r in roles
)
print(f"  Team:                 {TEAM_SIZE:.0f} people ({team_desc})")
print(f"  OPEX/month (base):    ~${opex_base_total:,}")
print(f"  OPEX/month (DR):      ~${opex_dr_total:,}")
print(f"  Year 1 OPEX:          ~${year1_opex_lo // 1000}K-${year1_opex_hi // 1000}K")
print(f"  {TCO_YEARS}-Year TCO:           ~${tco_lo / 1000:.0f}K-${tco_hi / 1000:.0f}K")
print(f"  Conservative saving:  £{annual_saving_conservative / 1000:.0f}K/year"
      f" -> break-even {breakeven_conservative_mo:.1f}mo (full adoption)"
      f" / ~{time_to_value_conservative:.0f}mo from kickoff (with ramp)")
print(f"  Optimistic saving:    £{annual_saving_optimistic / 1000:.0f}K/year"
      f" -> break-even {breakeven_optimistic_mo:.1f}mo (full adoption)"
      f" / ~{time_to_value_optimistic:.0f}mo from kickoff (with ramp)")
for i, (p, cost) in enumerate(zip(phases, phase_costs)):
    print(f"  Phase {p.number} cost:          ~${cost / 1000:.0f}K"
          f"  ({p.months}mo, ends month {milestone_months[i]})")
print("=" * W)
