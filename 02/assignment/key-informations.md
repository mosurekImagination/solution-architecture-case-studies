# Case Study 02 — Key Informations

> Extracted from client meeting transcription. Personal data anonymized.
> Speakers: **Client Representative** (enterprise side) and **Solution Architect** (consulting side).

---

## Business Context

- **Client type:** Existing enterprise — international webshop chain (not Amazon scale)
- **Market:** Operates across Europe
- **Domain:** Groceries and commodity goods — everything sellable online without restrictions (no medicine, no prescribed items)
- **Business maturity:** 15 years on the market
- **Scale:** ~1 million customers per day
- **Business goal:** Increase turnover by 20% (~1M → ~1.2M daily customers)
- **Approach:** Using collected data and AI, increase sales
- **Example 1:** Email suggestions to existing customers
- **Example 2:** Mobile app push notifications (optional, architect's discretion)
- **Enterprise mindset:** Want to be "AI enabled and data enabled"

## Existing Technical Landscape

- **Web platform:** WordPress with e-commerce plugin — has its own database
- **Mobile app:** Separate application, developed by an external vendor ~5 years ago (2 years development, 3 years maintenance). Completely separate mobile experience / buyer experience
- **Mobile vendor access:** Outsourced; to access mobile DB you must email the vendor — no direct/free access. Unknown whether mobile app uses same DB, separate DB, or API layer
- **Background jobs:** Exist, but details not provided unless specifically requested
- **Internal team:** Not deeply technical; aware of "data pipeline" concept but not solution details
- **Data landscape:** "Islands of information" — isolated pieces of data about wholesalers, users, buyers, customers across multiple systems

## Data Sources Identified

| # | Source | Access | Notes |
|---|--------|--------|-------|
| 1 | WordPress database | Free access, can replicate | Live database — replication preferred over copy |
| 2 | Mobile app database | Restricted — must email external vendor | Unknown schema, unknown DB type, unknown API |
| 3 | Wholesaler data | Multiple sources (plurality) | Amounts, discounts, deals — availability uncertain |
| 4 | Customer emails | Available from WordPress DB | 15 years of data; some are disposable/expired "10-minute mailboxes" |
| 5 | Mobile app install base | Unknown — data not currently tracked | Need to design a way to measure it |

## Technical Guidance from Meeting

### ETL Process (Extract, Transform, Load)
- Core pattern needed to unify data islands
- Extract data from all sources → Transform into needed format → Load into analytical database

### OLTP vs OLAP
- **OLTP** (Online Transactional Processing) = regular operational database for daily flows (WordPress DB)
- **OLAP** (Online Analytical Processing) = analytical database structured for analysis, not daily operations
- Need to build OLAP layer on top of existing OLTP sources

### Database Replication
- Replication from WordPress DB is preferred over copy (live database, continuous sync needed)
- Creating a separate analytics instance is possible but may cause problems with WordPress constraints

### Technology Keywords
- **Snowflake** — Data Lake approach, popular on AWS. Good for having everything in one place and running queries. Simpler
- **Databricks** — More complex and robust. Allows building various pipeline types, potentially training AI models. More advanced but more complex
- Both are similar scale; Snowflake is currently more popular, Databricks is gaining momentum

### Data Quality Principle
- "Your AI is only as good as your data" — if data is poor, everything built on it is useless
- Data quality and pipeline design are the critical foundation

## Task Breakdown (4 Steps)

1. **Collect data** — Find a way and reason to gather every piece of data from all sources
2. **Research** — Understand what the business wants, what structure is most helpful, do market research ("without market research, you are blind")
3. **Process data** — Work with data based on research findings (transform, clean, structure)
4. **Design & build** — Put everything together into a solution

## Key Constraints

- ❌ **No WordPress migration** — proposing migration will be heavily scrutinized; better have a strong reason
- ❌ **No direct mobile DB access** — gated by external vendor communication
- ⚠️ **Generic business goal** — client provides "increase sales by 20%", not a technical specification. Architect must translate business → technical
- ⚠️ **Enterprise dynamics** — large organization, may not know what to share, may not know what architect needs
- ⚠️ **Stale customer data** — some emails are non-working 10-minute mailboxes
- ⚠️ **Unknown mobile install base** — no visibility into how many users have the app installed

## Key Differences from Case Study 01

- This is an **existing enterprise** with operational systems, not a greenfield build
- Client gives **limitations but not solutions** — architect must figure out the "how"
- Hard-checked against existing business — cannot freely redesign existing systems
- More focused scope (data pipeline + recommendation) vs. full application design
- Must work **with** existing WordPress and mobile app, not replace them

## Assignment Context (Meta)

- This case study simulates a real enterprise RFP/RFI scenario
- Client Representative plays both mentor and enterprise representative roles
- The architect may follow or challenge the Client Representative's suggestions
- Questions can be asked asynchronously between sessions
- Stakes framing: the architect is positioned as an existing vendor — failure would mean losing the vendor contract

---

**Extracted by:** Solution Architect
**Date:** 2026-02-13
**Source:** Meeting transcription (VTT recording)
