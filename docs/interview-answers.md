# Data Engineering Random Interview — Model Answers

> **Purpose:** Reference-quality answers to dice-triggered random interview questions. Same elevated-standard treatment as `synthesis-answers.md`: verbatim Q + verbatim Bryan answer + grade table + 9/10 model + key lessons. Each entry is self-contained.
>
> **Format:** Every entry has these sections:
> - **The question:** verbatim
> - **Bryan's answer (verbatim) + score**
> - **Grade table** — 4 dimensions
> - **Model answer** — 9/10 reference
> - **Key lessons**
> - **Consolidation status** — flagged when sub-8.0 triggers consolidation; closed when re-drilled successfully
>
> **Standards (elevated 2026-05-07):**
> - **Individual score ≥8.0 required.** Sub-8.0 triggers consolidation session until ≥95% topical-fluency confidence, then re-drill with fresh variant
> - **"I don't know" handling:** hint-based guidance, 3-strike rule before full disclosure + consolidation + re-drill
> - **Senior-DE / intern framing:** depth and substantive defense of every claim are mandatory
>
> **Companion files:**
> - [`interview-questions.md`](./interview-questions.md) — questions only, no answers
> - [`synthesis-log.md`](./synthesis-log.md) — weak patterns log, shared across random AND synthesis question streams

---

## RQ-001 — SCD2 + Natural-Key Join Failure

*Date: 2026-05-07. Source: Banked match (6,6) fired after synthesis Q4 closed.*

**The question:**

> In a star schema with `fct_orders` and `dim_product`, an analyst asks: "Why did our average order value go down in Q3?" They join `fct_orders` to `dim_product` on `product_id` (natural key) — and notice some rows are duplicated in the result. The dimension is SCD Type 2. What's most likely going wrong, and how would you diagnose and fix it in one or two sentences each?

### Bryan's answer — 8.0/10 ✓ (passes individual threshold)

> What is most likely going wrong is that they are joining on the natural key which results in a one-to-many join. The primary key in this case would be the surrogate key, with a label ending in _sk.
> I would diagnose this issue by inspecting the JOIN and running a small DESCRIBE query in order to view the column names. In order to fix it I would just refer to the correct column (product_sk for instance) to conduct the JOIN.

| Dimension | Score | Why |
|---|---|---|
| Technical Accuracy | 9/10 | Diagnosis correct (one-to-many join via natural key); fix correct (use surrogate key) |
| Conceptual Depth | 8/10 | Clear understanding of why SCD2 + natural key JOIN produces row duplication |
| Vocabulary Precision | 8/10 | Used "natural key," "primary key," "surrogate key" correctly |
| Trade-off Awareness | 7/10 | Diagnostic approach is fine but could lean harder on what specific evidence would confirm the hypothesis |

### Model answer (9/10)

**What's going wrong:** Because `dim_product` is SCD Type 2, the same `product_id` (natural key) appears in *multiple* rows — one per historical version. Joining on the fact's `product_id` against the dimension's `product_id` matches every version, producing a Cartesian-like multiplication where each fact row appears once *per dimension version* of that product.

**How to diagnose (evidence ladder):**
1. **Confirm row counts** — `SELECT COUNT(*) FROM fct_orders` vs `SELECT COUNT(*) FROM <joined query>`. If joined > fact, row multiplication is happening.
2. **Find the multiplied IDs** — `SELECT product_id, COUNT(*) FROM dim_product GROUP BY product_id HAVING COUNT(*) > 1`. Shows which products have multiple SCD2 versions.
3. **Verify the join key** — check whether the analyst's query uses natural key vs surrogate key.

**How to fix:** Replace `JOIN dim_product ON fct_orders.product_id = dim_product.product_id` with `JOIN dim_product ON fct_orders.product_sk = dim_product.product_sk`. Then verify: is the fact table itself loading the correct surrogate (the version active at the order's date)? If the fact has been wrong all along (storing natural keys instead of surrogates), the fix is upstream in the ingestion pipeline, not just in the analyst's query.

The senior signal: **distinguish "the analyst's query is wrong" from "the data model is wrong."** Same surface symptom, very different fix locations.

### Key lessons

1. **Mechanism matters** — naming *why* the multiplication happens (multiple SCD2 rows per natural key) is more compelling than just naming that it happens. The "fan-out via non-unique join key" framing is the senior phrasing.
2. **Diagnostic ladder beats single query.** Row count comparison surfaces the symptom; key-uniqueness analysis surfaces the cause. Both queries demonstrate systematic thinking.
3. **Two fix layers, not one.** Query-level fix (use surrogate) AND data-model-level check (is the fact loaded with correct surrogates?) — both belong in a senior answer.

### Consolidation status

**No consolidation needed.** Score 8.0 meets individual threshold. Concept is solid; the lessons above are refinements toward 9/10 rather than gaps requiring re-teaching.

---

## RQ-002 — 100M-Row fct_invoices SCD2 Join

*Date: 2026-05-07. Source: Banked match (2,2) fired after synthesis Q8; 1d100=23 triggered SQL component requirement.*

**The question:**

> A fact table `fct_invoices` has 100 million rows. You're joining it to `dim_customer` (SCD Type 2, ~10 million customers, ~3 versions each on average). The join takes 45 minutes on Snowflake's MEDIUM warehouse.
>
> **Schema reference:**
>
> ```
> fct_invoices
>   invoice_id          INT (PK)
>   customer_sk         INT (FK → dim_customer.customer_sk)
>   invoice_date        DATE
>   amount              NUMBER(10,2)
>
> dim_customer (SCD Type 2)
>   customer_sk         INT (PK, surrogate)
>   customer_id         INT (natural key, NOT unique)
>   customer_name       VARCHAR
>   region              VARCHAR
>   valid_from          DATE
>   valid_to            DATE
>   is_current          BOOLEAN
> ```
>
> **The current slow query:**
>
> ```sql
> SELECT dc.region, dc.customer_name, SUM(fi.amount) AS total_billed
> FROM fct_invoices fi
> JOIN dim_customer dc ON fi.customer_sk = dc.customer_sk
> WHERE fi.invoice_date >= '2024-01-01'
>   AND fi.invoice_date <  '2024-04-01'
>   AND dc.is_current = TRUE
> GROUP BY dc.region, dc.customer_name;
> ```
>
> (a) Identify the bug in this query — correctness, not performance. (b) Rewrite to compute what the analyst likely meant. (c) Name two distinct performance-tuning levers for the corrected query.

### Bryan's answer — 6.0/10 ⚠️ BELOW THRESHOLD

> a. The issue with this query is that the analyst set dc.is_current to TRUE. Let's say we are running this in Q1 2025 for training purposes. Setting is_current = TRUE means that any historic data we have will not be included in our query, including the data we want to observe.
> b. SELECT
> dc.region,
> dc.customer_name,
> SUM(fi.amount) AS total_billed
> FROM fct_invoices fi
> JOIN dim_customer dc
> ON fi.customer_sk = dc.customer_sk
> WHERE (fi.invoice_date >= '2024-01-01' AND fi.invoice_date = '2024-04-01')
> GROUP BY dc.region, dc.customer_name;
> c. I am not sure

| Dimension | Score | Why |
|---|---|---|
| Technical Accuracy | 6/10 | (a) reasoning right; (b) has a SQL bug (`=` instead of `<`); (c) honest "not sure" |
| Conceptual Depth | 7/10 | The (a) insight on `is_current` is genuinely good — that's senior thinking |
| Vocabulary Precision | 7/10 | "Historic data won't be included" is right but understated; the more precise framing is "fact rows with superseded SK silently drop" |
| Trade-off Awareness | 5/10 | (c) gap means the performance-vs-correctness distinction wasn't articulated |

### Model answer (9/10)

**(a) Correctness bug — the silent SCD2 + is_current trap:**
The query JOINs on `customer_sk` (correct surrogate-key behavior), then filters `WHERE dc.is_current = TRUE`. But each fact's `customer_sk` points to the dimension version active *at invoice time* — which for any customer with attribute changes (region change, name change) is NOT the current version. The is_current filter drops every invoice whose linked dimension version has been superseded. **For long-tenured customers with attribute changes, all their pre-change invoices vanish from the result. The analyst sees an artificially small total_billed for those customers — and because nothing errors out, they have no idea anything's missing.** This is a *silent* correctness bug.

**(b) Corrected SQL — minimal change is to drop the is_current filter:**
```sql
SELECT
    dc.region,
    dc.customer_name,
    SUM(fi.amount) AS total_billed
FROM fct_invoices fi
JOIN dim_customer dc ON fi.customer_sk = dc.customer_sk
WHERE fi.invoice_date >= '2024-01-01'
  AND fi.invoice_date <  '2024-04-01'
GROUP BY dc.region, dc.customer_name;
```

The elegant property of SCD2 with surrogate keys: **date-correctness comes for free from the join.** The fact's `customer_sk` already points to the version active at the time. Just don't filter for "current" and you're done.

**(c) Two performance-tuning levers:**

**Lever 1: Cluster fct_invoices on invoice_date** —
```sql
ALTER TABLE fct_invoices CLUSTER BY (invoice_date);
```
The query filters to a 90-day window. With clustering on date, Snowflake prunes entire micro-partitions outside the window, scanning maybe 25% of the table instead of 100%. On 100M rows, that's a ~4× scan-time reduction.

**Lever 2: Pre-filter the dimension to relevant SCD2 versions:**
```sql
WITH relevant_versions AS (
    SELECT customer_sk, region, customer_name
    FROM dim_customer
    WHERE valid_to >= '2024-01-01' AND valid_from < '2024-04-01'
)
SELECT rv.region, rv.customer_name, SUM(fi.amount)
FROM fct_invoices fi
JOIN relevant_versions rv ON fi.customer_sk = rv.customer_sk
WHERE fi.invoice_date >= '2024-01-01'
  AND fi.invoice_date <  '2024-04-01'
GROUP BY rv.region, rv.customer_name;
```
Shrinks the dimension side from ~30M rows to ~12M (only versions valid during Q1). Smaller hash table → faster join, less spill-to-disk risk on MEDIUM warehouse.

A third lever (not required) is **scaling up the warehouse** — MEDIUM → LARGE doubles compute. It's the lazy fix; structural fixes (clustering, pre-filtering) compound and are what senior engineers reach for first.

### Key lessons

1. **The (a) insight on is_current is real progress** — correctly identifying that filtering on a Type-2 attribute that varies across versions is the bug is senior-level thinking. Build on this.
2. **SQL precision is the gap** — `=` vs `<` is the same precision-of-execution category as the synthesis Q4 SQL bugs. Concept is right; operator slipped.
3. **Performance tuning is a knowledge gap, not a thinking gap** — "I don't know" was the honest answer. The two levers (clustering for partition pruning; pre-filtering to shrink hash table) are concrete techniques worth memorizing.
4. **The "third lever is the lazy fix" framing** — when given multiple options for performance, structural changes (data layout, query rewrites) compound; resource scale-up (bigger warehouse) doesn't. Senior engineers reach for the structural fixes first.

### Consolidation status

🚧 **Consolidation REQUIRED.** Score 6.0 is below the 8.0 individual threshold. Three areas need work before re-drill:

1. **SCD2 + is_current trap mechanics** — the (a) insight is good but the *consequence specificity* (silent bug, hits long-tenured customers with changes) needs to be internalized so it's articulated reflexively, not arrived-at on the fly.
2. **Range-filter SQL precision** — the `=` vs `<` slip is a recurring pattern. Worth practice.
3. **Snowflake performance tuning** — entirely new territory. Need teaching session covering: micro-partitions, pruning, clustering, hash joins, spill-to-disk, warehouse sizing.

**Plan:** Consolidation sessions (3) on the three gap areas above, all conducted *after* Phase 1 re-drill completes (don't pile up cognitive load). Re-drill with fresh variant on a different fact-dim pair (e.g., `fct_payments` × `dim_account` SCD2). Target re-drill date: end of Phase 2 or as part of quarterly rerun, whichever comes first. Re-drill must score ≥8.0 to close consolidation.

---

## How to Use This File

1. **Append answers immediately after grading** — don't batch. Each entry is self-contained and can be reviewed independently.
2. **Sub-8.0 entries get a "Consolidation status" block** with what gaps need closing and a target re-drill timing. Status closes only when the re-drill clears 8.0+.
3. **Verbatim preservation** — Bryan's answer is recorded *exactly as written*, even with typos or trailing punctuation. Future re-reads compare exact phrasing to the model answer for true delta detection.
4. **Quarterly rerun questions go here too** — when re-asking a prior question, append a new entry with the Comparison Protocol verdict (↑/→/↓/⚡) at the top.

## Numbering Convention

Same as `interview-questions.md`: `RQ-NNN` zero-padded, increments globally across phases.
