# Data Engineering Random Interview Questions

> **Purpose:** Persistent record of dice-triggered interview questions and quarterly reruns. Distinct from synthesis drills (which test end-of-phase synthesis): random questions surface mid-conversation when 2d10 dice match, applying spaced-repetition pressure across roadmap pillars.
>
> **Format:** ~5 sentences per question with explicit hints and resource pointers. No answers (those live in `interview-answers.md`).
>
> **Question types tracked here:**
> - **Banked matches** — dice matched but the question was deferred to a natural breakpoint
> - **Real-time matches** — dice matched and the question fired immediately
> - **Quarterly reruns** — concept-stability re-tests of prior questions, triggered every ~6 weeks
> - **Light interview questions** — short consolidation prompts mid-session
>
> **Scoring & advancement (elevated standards, 2026-05-07):**
> - Same 4-dimension rubric as synthesis: Technical Accuracy 40% / Conceptual Depth 30% / Vocabulary Precision 20% / Trade-off Awareness 10%
> - **Individual score ≥8.0 required.** Any sub-8.0 score triggers a consolidation session: Socratic walkthrough of underlying concepts, continuation until ≥95% topical-fluency confidence is reached, only then re-drill with a fresh variant
> - **"I don't know" handling:** hint-based guidance with a 3-strike rule. Three "I don't know"s on the same question → full answer + consolidation + fresh-variant re-drill
> - SQL questions always include schema reference inline
>
> **Companion files:**
> - [`interview-answers.md`](./interview-answers.md) — verbatim Q + verbatim Bryan answer + grade table + 9/10 model + key lessons
> - [`synthesis-log.md`](./synthesis-log.md) — weak patterns log (shared across random AND synthesis question streams)

---

## Index

### 2026-05 (Phase 1 timeframe)

- [RQ-001 — SCD2 + natural-key join failure (banked match 6,6)](#rq-001--scd2--natural-key-join-failure)
- [RQ-002 — 100M-row fct_invoices SCD2 join: correctness + rewrite + perf levers (banked match 2,2 with SQL component)](#rq-002--100m-row-fct_invoices-scd2-join)

---

## RQ-001 — SCD2 + Natural-Key Join Failure

*Date asked: 2026-05-07. Source: Banked match (6,6) fired after synthesis Q4 closed. Topic anchor: SCD Type 2 mechanics + surrogate-key necessity.*

**The question:**

> In a star schema with `fct_orders` and `dim_product`, an analyst asks: "Why did our average order value go down in Q3?" They join `fct_orders` to `dim_product` on `product_id` (natural key) — and notice some rows are duplicated in the result. The dimension is SCD Type 2. What's most likely going wrong, and how would you diagnose and fix it in one or two sentences each?

**Hint:** This is a direct application of the surrogate-key requirement for SCD2 dimensions. Three sub-parts: (1) what's going wrong, (2) how to diagnose, (3) how to fix.

**Resources:** `mental-models.md` (relevant to dimensional modeling); flashcards "SCD Type 2", "Surrogate Key vs Natural Key", "Fact Table"; `design-doc.md` §5.4

---

## RQ-002 — 100M-Row fct_invoices SCD2 Join

*Date asked: 2026-05-07. Source: Banked match (2,2) fired after synthesis Q8 closed; 1d100=23 triggered SQL component. Topic anchor: SCD2 + correctness pitfalls + warehouse performance.*

**The question:**

> A fact table `fct_invoices` has 100 million rows. You're joining it to `dim_customer` (SCD Type 2, ~10 million customers, ~3 versions each on average). The join takes 45 minutes on Snowflake's MEDIUM warehouse.
>
> **Schema reference:**
>
> ```
> fct_invoices
>   invoice_id          INT (PK)
>   customer_sk         INT (FK → dim_customer.customer_sk)  -- surrogate
>   invoice_date        DATE
>   amount              NUMBER(10,2)
>
> dim_customer (SCD Type 2)
>   customer_sk         INT (PK, surrogate)
>   customer_id         INT (natural key, NOT unique — same customer has multiple SK rows)
>   customer_name       VARCHAR
>   region              VARCHAR
>   valid_from          DATE
>   valid_to            DATE
>   is_current          BOOLEAN
> ```
>
> **The current slow query** an analyst is running:
>
> ```sql
> SELECT
>     dc.region,
>     dc.customer_name,
>     SUM(fi.amount) AS total_billed
> FROM fct_invoices fi
> JOIN dim_customer dc
>   ON fi.customer_sk = dc.customer_sk
> WHERE fi.invoice_date >= '2024-01-01'
>   AND fi.invoice_date <  '2024-04-01'
>   AND dc.is_current = TRUE
> GROUP BY dc.region, dc.customer_name;
> ```
>
> **(a) Identify the bug in this query.** It's not a *performance* problem first — it's a *correctness* problem hiding as performance. What's the analyst computing that they probably don't intend to compute?
>
> **(b) Rewrite the SQL to compute what the analyst likely *meant* to compute** — total billed in Q1 2024, attributed to each customer's region/name as it was at the time of invoice.
>
> **(c) Name two distinct performance-tuning levers** you'd reach for *after* fixing the correctness bug, given the table sizes (100M facts, ~30M dimension rows). For each, state what specifically the lever would change and why it would speed up *this* query.

**Hint:** Three sub-parts. Part (a) tests whether you spot that `is_current = TRUE` filter on a Type 2 dimension silently drops historical fact rows. Part (b) tests whether you can write a Type-2-aware SQL query (lessons learned from synthesis Q4 SQL bugs apply). Part (c) tests warehouse performance literacy — clustering, micro-partition pruning, hash-table sizing.

**Resources:** `flashcards`: "SCD Type 2", "Surrogate Key vs Natural Key", "Snowflake CLUSTER BY" (added 2026-05-07), "SCD2 + is_current Filter Trap" (added 2026-05-07); `design-doc.md` §5.4

---

## How to Use This File

1. **When a dice match triggers a question**, capture it here with the same format as RQ-001/RQ-002. Always include hints + resources.
2. **When a question is answered**, the verbatim Q + your verbatim answer + grade + model 9/10 + key lessons go into `interview-answers.md` (this file just keeps the question record).
3. **When sub-8.0 scores trigger consolidation**, document the consolidation outcome in `interview-answers.md` and any newly-surfaced weak pattern in `synthesis-log.md`.
4. **Quarterly rerun cadence**: every ~6 weeks, scan this file and re-ask 1-2 prior questions. Use the Comparison Protocol (verdict: ↑ improved / → flat / ↓ regressed / ⚡ different angle). Update Gaps Log on regressions.

## Numbering Convention

`RQ-NNN` (Random Question, three-digit zero-padded). Increments globally across phases — RQ-001 is the first ever, RQ-100 is the 100th, regardless of which phase generated it. Date in section header makes the timeline navigable.
