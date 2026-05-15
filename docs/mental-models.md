# Data Engineering Mental Models

> **Purpose:** A reference of thinking tools for approaching DE problems. Updated as new mental models surface across phases. These are *patterns of reasoning* — distinct from flashcards (vocabulary) and the tooling reference (commands).
>
> **How to use this file:** When stuck on a problem, scan the table of contents for a mental model that fits the shape of what you're facing. Reading the worked examples before applying is more useful than memorizing definitions cold.
>
> **Companion files:**
> - [`de_flashcards.csv`](de_flashcards.csv) — vocabulary (terms and short definitions)
> - [`tooling-reference.md`](tooling-reference.md) — concrete commands and idioms
> - [`synthesis-questions.md`](synthesis-questions.md) — interview-style drills

---

## Table of Contents

### Reasoning About Architecture
1. [Configuration Cascade](#1-configuration-cascade)
2. [System Cast vs Runtime Cast](#2-system-cast-vs-runtime-cast)
3. [Defense in Depth (Bidirectional)](#3-defense-in-depth-bidirectional)

### Reasoning About Data
4. [Predict Before You Query](#4-predict-before-you-query)
5. [Grain First, Schema Second](#5-grain-first-schema-second)
6. [The Richness Test (When to Build a Dimension)](#6-the-richness-test-when-to-build-a-dimension)
11. [Schema vs Semantics Stability](#11-schema-vs-semantics-stability)
12. [Investigation as Decision Tree](#12-investigation-as-decision-tree)

### Reasoning About Cost & Scale
7. [Cost Trade-offs Flip at Scale](#7-cost-trade-offs-flip-at-scale)
8. [Risk Transfer via Indirection](#8-risk-transfer-via-indirection)

### Reasoning About Process
9. [Self-Directed Consolidation](#9-self-directed-consolidation)
10. [Naming Convention as Automation Surface](#10-naming-convention-as-automation-surface)

---

## 1. Configuration Cascade

**The model:** Configuration values flow through ordered layers, each consuming the previous and producing for the next. To debug a missing or wrong value, walk the chain backward to find the layer that dropped or modified it.

### Why it works

Software is composed. Every tool reads config from somewhere and passes it forward. When something goes wrong, the bug is at *one specific layer*, but the symptom appears at the end of the chain. Fixing it requires finding the right layer — not throwing fixes at random.

### When to apply

- Environment variable not visible where you expect it
- Config file changes "didn't take effect"
- Something works locally but fails in container
- Same code runs but with different behavior in different environments
- Anytime you find yourself wondering "where is this value *coming from*?"

### Worked example — Phase 0, Q-Re-2

The line `_PIP_ADDITIONAL_REQUIREMENTS: ${_PIP_ADDITIONAL_REQUIREMENTS:-}` in `docker-compose.yaml` requires walking six layers to fully understand:

```
.env file
  ↓ (Compose auto-loads .env from current directory)
Compose's own environment
  ↓ (substitutes ${VAR:-default} into YAML at compose-load time)
docker-compose.yaml (now has resolved value)
  ↓ (forwarded into container as env var at container creation)
Container's environment
  ↓ (entrypoint script reads env var at every container boot)
Airflow entrypoint script
  ↓ (runs pip install at boot)
pip
```

A bug at *any one layer* produces "packages aren't installed" as a symptom. The fix depends on which layer is broken. Senior debugging is fast because it finds the right layer immediately rather than trying things at random.

### Generalizes to

- dbt profiles (`profiles.yml` → environment vars → connection)
- Terraform variables (`.tfvars` → CLI → provider → API)
- Kubernetes ConfigMaps (YAML → mounted file → app reads)
- Airflow connections (UI form → metadata DB → operator → external service)

---

## 2. System Cast vs Runtime Cast

**The model:** When asked "who acts during X," distinguish identities that **exist in the system** (built it, configured it, can use it) from identities that **act during a specific execution**. The runtime cast is typically much narrower than the full inventory.

### Why it works

Conflating "who exists" with "who acts" produces inflated, imprecise answers in identity/security contexts. Interviewers explicitly probe for this distinction because it tests whether you understand authentication actually happens at runtime, not at setup time.

### When to apply

- Listing identities involved in an automated job
- Designing IAM policies (over-privileging happens when system cast is treated like runtime cast)
- Debugging "why is this auth failing?" — narrow to who's actually authenticating, not who exists
- Security audits and threat modeling

### Worked example — Phase 0, Q-Re-1

When an automated 3 AM Airflow DAG runs an ingestion script:

**System cast (built the system, irrelevant at runtime):**
- ❌ Your human Snowflake user (not logged in at 3 AM)
- ❌ ACCOUNTADMIN (not assumed by anyone during the run)
- ❌ AWS root/admin user (used to create the bucket; not acting now)

**Runtime cast (actually acts during this execution):**
- ✅ `airflow-scheduler` process — fires the DAG, spawns subprocess
- ✅ Python subprocess — inherits env vars, runs the code
- ✅ `nyc-taxi-elt-user` (IAM user) — boto3 reads its keys from env
- ✅ `ELT_USER` (Snowflake user, with `ELT_ROLE` privileges) — connector reads password
- ✅ Snowflake's IAM user — calls `sts:AssumeRole` when COPY INTO runs
- ✅ `snowflake-s3-role` — assumed identity that reads S3

### The diagnostic question

> "At the moment X happens, what is *literally* authenticating to *what*?"

If an identity isn't presenting credentials to a service during X, it's not part of the runtime cast — even if it exists in the system.

---

## 3. Defense in Depth (Bidirectional)

**The model:** Two independent security layers don't justify themselves with one direction of threat. Each layer must protect against a class of compromise that the other doesn't cover. Defense-in-depth requires articulating threats from *both directions*.

### Why it works

Stacking layers is only valuable if the layers fail independently. If both layers fail to the same threat, you have one defense, not two. Bidirectional reasoning ensures you've actually achieved redundancy.

### When to apply

- Designing or defending any multi-layer security setup
- Justifying "why both" to a skeptical reviewer
- Identifying gaps where you *think* you have defense in depth but actually don't

### Worked example — Phase 0, Q-Re-3

`.env` gitignore + IAM permissions policy on `nyc-taxi-elt-user`:

| Threat | gitignore protects? | IAM policy protects? |
|---|---|---|
| Accidental commit of `.env` to public GitHub | ✅ Yes | ❌ No (the keys are real, the role permits the actions) |
| Laptop theft + extraction of `.env` | ❌ No (keys leak via non-Git path) | ✅ Yes (limits blast radius to one bucket) |

**The pair is genuine defense-in-depth** because each protects against a class of incident the other can't cover.

### When two "layers" are actually one

If you stacked two gitignore rules (one in `.gitignore`, one in a hook), they'd both fail to the same threat (laptop theft). That's not depth — that's one layer with redundant implementations.

### Generalizes to

- `STORAGE_ALLOWED_LOCATIONS` + IAM permissions policy
- Network firewall + application authentication
- Backup + replication
- Code review + automated tests

---

## 4. Predict Before You Query

**The model:** Before running an exploratory query, write down what you expect the result to be. The gap between prediction and reality is where insight lives — far more valuable than the query result alone.

### Why it works

Querying without prediction trains you to *consume* outputs. Predicting first forces you to articulate your mental model. When prediction matches result, your model is sound. When it doesn't, you've found a gap — and the gap is the most useful thing in data engineering, because gaps point at assumptions you didn't know you had.

### When to apply

- First-pass profiling of any new dataset
- Investigating data quality issues
- Validating an upstream change ("did this migration produce what I expected?")
- Reviewing a teammate's pipeline output before approving

### Worked example — Phase 1

Predicted of `PULocationID`:
- min_id: 0–1
- max_id: 4–5
- distinct_count: 5

Actual:
- min_id: 1
- max_id: 265
- distinct_count: 260

The gap — 5 expected, 260 actual — revealed that the column wasn't representing boroughs at all. It was representing TLC's custom-designed taxi zones, a much finer-grained geographic concept. That single gap-discovery shaped the entire star schema design that followed.

If I'd run the query without predicting, I might have just taken `260` at face value and moved on. Predicting "5" forced me to ask "wait, why 260?" — and the *why* was the actual learning.

### The ritual

For any unfamiliar dataset:
1. Before opening the file, write down what columns you expect
2. For each column, predict cardinality, value range, null rate
3. Run the queries
4. Note where reality differs from prediction
5. Investigate the gaps — they're where the dataset is *interesting*

---

## 5. Grain First, Schema Second

**The model:** Before designing a fact table, define exactly what one row represents. Grain decisions determine which questions are answerable; schema decisions follow from grain.

### Why it works

Most schema design errors trace back to fuzzy grain. "One row per X" sounds trivial but is rarely articulated precisely. When the grain is "one row per order," teams later struggle to answer "which products in this order?" because the line-level grain is missing. Stating grain first prevents these gaps.

### When to apply

- Designing any fact table from scratch
- Auditing an existing fact table you inherited ("what's the grain here?")
- Deciding whether to build one fact table or multiple
- Diagnosing "why is this query so awkward?" — often the answer is a grain mismatch

### Worked example — Phase 1

Looking at `yellow_tripdata`, the grain is **one row per completed taxi trip**. Evidence:
- Each row has both pickup and dropoff timestamps (a single trip event)
- Per-trip measurements: fare, tip, distance, passenger count
- One pickup location, one dropoff location

This grain supports questions like:
- ✅ Avg fare per trip
- ✅ Trips per day
- ✅ Most popular pickup zones

This grain does *not* support:
- ❌ "How many minutes was each passenger in the cab?" (No per-passenger grain)
- ❌ "What route did this cab take?" (No per-segment grain)

A real production warehouse might have multiple fact tables at different grains — `fct_trips` (per trip) and `fct_trip_segments` (per route segment) — to answer different question types from the same source events.

### The diagnostic question

When designing or inheriting a fact table, ask:

> "If I told a junior engineer to write a query against this table, what would they need to know about *what one row means* before they could write a correct SUM or COUNT?"

If you struggle to state grain in one sentence, the table needs grain clarification — or refactoring.

---

## 6. The Richness Test (When to Build a Dimension)

**The model:** A column should become its own dimension when it passes three tests: (1) cardinality is meaningfully greater than 2–5, (2) the set of values may grow over time, (3) you'd plausibly want to attach descriptive attributes. Failing any one pushes toward keeping it in the fact table as a degenerate dimension.

### Why it works

Junior engineers tend to either over-dimensionalize (building a `dim_yes_no` for boolean flags) or under-dimensionalize (leaving rich entities like vendors as raw integers). The three tests give you a deliberate framework for the call.

### When to apply

- Designing a star schema for a new fact table
- Deciding whether a categorical column needs lookup
- Reviewing schema work — flagging columns that "should be a dimension"
- Code review on dbt models

### Worked examples — Phase 1

| Column | Cardinality | Stable? | Rich attributes? | Verdict |
|---|---|---|---|---|
| `PULocationID` | 260 | Stable | Borough, zone, service zone | **Dimension** ✓ |
| `payment_type` | ~6 | May grow | Description, requires_processing | **Dimension** ✓ |
| `RatecodeID` | 6 | Stable | Description, is_airport, flat_rate | **Dimension** ✓ |
| `VendorID` | 2 | Mostly stable | Vendor name, contact, contract | **Borderline → Dimension** ✓ |
| `passenger_count` | 1–6 | Fixed | None worth attaching | **Degenerate** |
| `store_and_fwd_flag` | 2 (Y/N) | Fixed | None | **Degenerate** |
| `tip_amount` | Continuous | N/A | N/A | **Pure measure** |

### The shortcut question

If the three formal tests feel slow, use this:

> "Would a business analyst writing a report ever want to JOIN to this column to get richer text or attributes?"

If yes → dimension. If no → degenerate. The shortcut wraps all three formal tests into one pragmatic question.

---

## 7. Cost Trade-offs Flip at Scale

**The model:** A cost optimization that's correct in development is often wrong in production. The trade-offs invert because what's expensive at low traffic (latency, restart cost) becomes the dominant cost at high traffic, while what's expensive at high traffic (idle resources) is irrelevant at low traffic.

### Why it works

Cost optimization is multidimensional — compute, latency, idle time, complexity. Different points on the traffic curve weight these dimensions differently. Optimizing for "saving money in dev" without recognizing the inversion produces production systems that hurt user experience to save trivial amounts on idle compute.

### When to apply

- Setting any auto-suspend / auto-shutdown timer
- Sizing compute resources
- Choosing between batch and streaming
- Caching design decisions
- Deciding "should this run on demand or always-on?"

### Worked example — Phase 0, Q5

`AUTO_SUSPEND = 60` is correct for development:
- Low traffic (one query every few hours)
- Idle compute is the dominant cost
- Resume latency is acceptable (one query, not user-facing)

For production with 100 concurrent analysts, the trade-off flips:
- High traffic (many queries per minute)
- Each suspend → 1-second resume hits user experience
- Idle compute is rare anyway under sustained load
- Setting `AUTO_SUSPEND = 600` (10 min) is *cheaper net* because you avoid resume cost on every dropped query

### The diagnostic question

> "If I 10x the traffic this system handles, which of my current cost decisions become *more* expensive instead of less?"

Anything that gets worse at scale needs to be re-thought before scale arrives — not after.

---

## 8. Risk Transfer via Indirection

**The model:** Designing a service to *hold* customer credentials makes the service a high-value attack target carrying its customers' risk. Designing the service to *delegate* via short-lived credentials shifts the risk: the keystore problem disappears entirely.

### Why it works

Credential storage is asymmetric — the cost is constant for the holder, but the risk scales with the number of customers. A breach of a service holding 10,000 customer credentials is a 10,000-victim incident. A breach of a service that holds zero long-lived credentials is a much smaller incident.

### When to apply

- Designing any third-party integration
- Architecting service-to-service authentication
- Evaluating "should we accept credentials directly?"
- OAuth vs password storage decisions
- Cross-account / cross-cloud access patterns

### Worked example — Phase 0, Q-Re-1

Snowflake → S3 access could have been designed two ways:

**Long-lived keys design:** Snowflake stores customer's AWS access keys.
- N customers → N permanent credential sets in Snowflake's storage
- Snowflake breach = mass leak of customer credentials
- Customer rotation requires coordination

**AssumeRole design (chosen):** Snowflake's IAM user requests temp credentials per-request.
- N customers → 0 long-lived customer credentials in Snowflake's storage
- Snowflake breach yields short-lived in-flight tokens, expire in minutes
- Customer rotation = update trust policy, no Snowflake coordination

The architectural insight isn't "tokens expire faster." It's that **the keystore problem is eliminated entirely.**

### Generalizes to

- OAuth (apps don't store user passwords)
- Service mesh mTLS (services don't share secrets)
- Workload identity in Kubernetes (pods don't carry static credentials)
- Any "delegation > storage" architectural decision

---

## 9. Self-Directed Consolidation

**The model:** When a concept comes in below threshold or feels fuzzy, pause for deliberate consolidation *before* moving on or re-attempting. Re-attempting without consolidation reinforces the same gaps. Consolidation means slowing down enough to map the concept's full structure, not just memorizing the right answer.

### Why it works

Speed-pressure encourages pattern-matching to surface answers; consolidation encourages building a model that can *generate* answers. The latter transfers; the former doesn't.

### When to apply

- Just got a concept-related question wrong
- Feeling like you "kind of know" something but can't articulate it crisply
- About to re-attempt something you previously got 60–70% on
- Studying for an interview where you'll need fluent recall, not pattern-match recall

### Worked example — Phase 0, Q-Re-2

Original Q4 score: 6.5/10. Concept: Docker Compose templating + lifecycle.

Two choices: power through to Q-Re-2 with the fuzzy model, or pause for consolidation. Consolidation chose:
- Sat with the six-layer cascade until each layer was nameable
- Worked through the `${VAR:-default}` syntax explicitly
- Asked "where do values come from?" until the answer was reflex

Result on Q-Re-2: 8.5/10 (+2.0). The same underlying concept, tested with a different scenario, with the consolidated model in place.

### The signal that you need this

If you can pattern-match your way to a correct answer but couldn't *teach* it to someone else from scratch, you have a fuzzy model. Consolidation makes the model teachable, which means it's also durable.

---

## 10. Naming Convention as Automation Surface

**The model:** Predictable, structured naming patterns (`{type}_tripdata_{YYYY}-{MM}.parquet`) let a single function or query handle the entire family of artifacts. Unpredictable naming forces per-instance special-case logic. Naming conventions are not bureaucracy — they are design contracts that future automation depends on.

### Why it works

Automation reads. Reading happens at scale (every file, every table, every DAG run). Predictable naming means one rule covers all instances; unpredictable naming means every new instance needs new code or manual handling.

### When to apply

- Designing file naming schemes for cloud storage
- S3 prefix structures
- dbt model naming
- Hive-style partition paths
- Airflow DAG IDs and task IDs
- Snowflake table naming
- Any artifact your code or queries will need to enumerate

### Worked example — Phase 1

NYC TLC publishes:
```
yellow_tripdata_2024-01.parquet
yellow_tripdata_2024-02.parquet
green_tripdata_2024-01.parquet
...
```

This pattern enables:
```python
def build_url(taxi_type: str, year: int, month: int) -> str:
    return f"https://.../{taxi_type}_tripdata_{year}-{month:02d}.parquet"
```

One function handles every file across the entire dataset family. If they had used `nyc-taxi-yellow-jan24-final-v3.parquet` style names, this entire automation would collapse into either manual case-by-case handling or fragile regex-with-exceptions.

### The diagnostic question

When naming a new artifact (file, table, DAG, etc.), ask:

> "If I have 1000 of these in a year, can a single function/query handle all of them based on the name pattern alone?"

If yes — the convention is automation-ready.
If no — pick a more structured pattern *now*, before instances proliferate.

---

## 11. Schema vs Semantics Stability

**The model:** A column's *existence* (schema) and a column's *meaning* (semantics) can drift independently across time. A column may always have existed without always having data; data presence may shift due to policy changes, system rollouts, or backfill operations during republishing. Always verify value distributions before assuming a column's meaning is stable across the historical range.

### Why it works

When inspecting a long-running dataset, schema-level checks (column count, names, types) only validate the *structure* of the data. The *interpretation* of each column may have shifted in ways the schema doesn't reveal. Conflating these creates analyses that silently misinterpret historical periods.

### When to apply

- Profiling any dataset with multi-year history
- Validating ingestion pipelines that consume historical data
- Reviewing analytical queries that aggregate across long time windows
- Investigating "wait, why is this metric weirdly low for 2015?"

### Worked example — Phase 1, Step 3

Investigation of `yellow_tripdata` Parquet files across 2015, 2019, 2024:

**Schema-level finding:** all three years have identical 19-column schema. No columns added or removed. *Looks like* simple type drift only.

**Semantics-level finding (revealed by querying actual values):** `congestion_surcharge` and `airport_fee` are NULL for *every single row* in January 2015 — 12.7M rows, all NULL. The columns existed in the schema but were not populated until the corresponding policies launched (congestion pricing 2019, airport fees 2022).

The schema-level check would have led to a confident "no schema evolution issues" conclusion. The semantics-level check revealed that aggregations on these columns must filter by date or risk silently misinterpreting NULL as "no surcharge applied" when it actually means "the policy didn't exist yet."

### The diagnostic ritual

For any historical dataset, run two passes:

1. **Structural pass:** `DESCRIBE` across years; compare column names, types, count
2. **Semantic pass:** for each column that's expected to be populated, sample distributions (`SELECT col, COUNT(*) GROUP BY col`) across each year. Look for periods where the column is suspiciously NULL, all-zero, or all-default. Look for new categorical values appearing partway through history. Look for numerical scale shifts (a `cost` column averaging 50 in 2018 and 5000 in 2020 is a sign of a unit change). Look for definition shifts in metric documentation.

The semantic pass catches everything the structural pass misses.

### The taxonomy of semantic drift (with characteristic fixes)

Five drift categories worth distinguishing, because each has a different *fix* even though they share a *symptom*:

| Drift category | What changes | Example | Characteristic fix |
|---|---|---|---|
| **NULL-population drift** | Column existed but had no values until a policy/feature/system launched | `congestion_surcharge` NULL for all 2015 NYC TLC rows | Filter by date when aggregating; document policy launch dates in data dictionary |
| **Unit / encoding drift** | Same column, different measurement system (USD↔EUR, cents↔dollars, UTC↔local) | `revenue` storing dollars in 2018, cents in 2024 | Normalize the unit using historical conversion data |
| **Definition drift** | The real-world concept the column references changed | "ad impression" redefined to require viewability after 2017 | Segment the analysis — cannot combine pre-change and post-change; compare within each definition era |
| **Taxonomy expansion** | New categorical values added without retiring old ones | `payment_method` adding `apple_pay` in 2019, `crypto` in 2024 | Decide whether to roll up new categories into legacy ones for cross-period comparison, or report new vs legacy distinctly |
| **Soft-state drift** | Same row exists but its meaning shifts via flags | `is_active = false` records persist but represent something different than active records | Decide whether soft-state records should be filtered before analysis, included as a distinct cohort, or aggregated separately |

The senior signal is naming both the *category* of drift AND the *characteristic fix* — they pair together because the fix shape derives from the change shape.

### The danger isn't crashes; it's silent wrongness

The reason these models matter for senior data engineers: schema-mismatch bugs are *easy* — they produce errors, missing columns, type cast failures. Loud failures get fixed. Semantic drift bugs are *dangerous* because they produce **plausible-looking results that are quietly wrong.** An analyst computing "average revenue per customer" across 8 years gets a number that looks reasonable, fits in a deck, supports a decision — and is wrong because revenue was redefined in year 4 or stored in cents starting in year 6. Bad decisions get made on bad numbers, and nobody knows the data was the cause.

This is why the structural pass alone is insufficient. The temptation is to use the fast check (DESCRIBE) as a proxy for the slow check (per-period value sampling). That temptation is the failure mode.

### Generalizes to

- API field deprecation (a field exists in the response schema but is never populated)
- Soft-deleted records (rows exist but flagged inactive)
- Feature flags (column exists but only populated for users in the rollout)
- Versioned events (event type names evolve while schema remains stable)

---

## 12. Investigation as Decision Tree

**The model:** When a data finding surprises you (count differs from expected, distribution doesn't match documentation, an aggregation looks wrong), the senior reflex is to **pause before querying**. The pause does discrete cognitive work: enumerate a hypothesis space first, then design queries that *distinguish between* hypotheses rather than confirm one. The pause prevents confirmation bias on the first plausible explanation.

### Why it works

Most data anomalies have multiple consistent explanations. If you query to test hypothesis #1, you'll likely find evidence consistent with #1 — *and* with #2, #3, #4, because they overlap in observable signals. Confirmation feels like progress, but you've actually filtered out the better answers without seeing them. The decision-tree structure (each query rules in/out specific candidates) is the antidote: queries earn their place by *distinguishing*, not by *confirming*.

### When to apply

- Profiling a new dataset and a count, distribution, or schema property surprises you
- Validating an ingestion pipeline and outputs don't match expectations
- Investigating a user-reported bug ("this report number looks wrong")
- Reviewing an analyst's query that produces suspicious results
- Any situation where "let me just check X" is the impulse

### The hypothesis-generation checklist (6 canonical categories)

When generating hypotheses for "why doesn't this data match expectations," walk through these six categories. Each surfaces a different mechanism:

| # | Category | Mechanism | Example signal |
|---|---|---|---|
| 1 | **Documentation drift** | Doc was correct at some point; data evolved without doc updates | New values appearing only after a date |
| 2 | **Data quality / human entry** | Typos, casing, whitespace in free-text fields | Many low-count near-duplicates of canonical values |
| 3 | **Schema misinterpretation** | Column mislabeled, columns swapped, wrong column queried | Values resemble what *another* column should hold |
| 4 | **Multi-source heterogeneity** | Dataset is union of multiple systems with different taxonomies | Distinct values cluster cleanly when grouped by region/system/business unit |
| 5 | **Migration artifacts** | Source-system migration left old encoding + new encoding coexisting | Mix of formats (e.g., "1" and "Bronze" in same column) |
| 6 | **Composite/encoded values** | Column intentionally stores multiple semantic units, but the encoding wasn't expected | Structured patterns like "X-Y" or fixed-length codes; close to category-count × subcategory-count distinct values |

### The distinguishing-query pattern

Once hypotheses exist, queries earn their place by ruling in/out *specific* candidates. The structure: "If I run query Q and see result R, that confirms hypothesis A and rules out B, C, D."

Worked example — `customer_segment` column shows 47 distinct values, doc says 5:

| Query | What it distinguishes |
|---|---|
| `SELECT TRIM(LOWER(seg)), COUNT(*) GROUP BY 1` | If normalized count drops to ~5 → category 2 (data quality) confirmed; if still ~47 → rules out category 2 |
| `SELECT seg, MIN(created_at) GROUP BY seg` | New values appearing post-some-date → category 1 (doc drift); evenly distributed → rules it out |
| `SELECT seg, COUNT(*) GROUP BY seg ORDER BY 2 DESC` plus inspect tail | Long tail of similar-looking variants → category 2; structured patterns like "Gold-NY" → category 6 |
| `SELECT region, seg, COUNT(*) GROUP BY 1, 2` | Clean ~5-per-region split → category 4 (multi-source); flat distribution → rules it out |
| Sample raw rows: `SELECT seg, * FROM table WHERE seg NOT IN (canonical 5) LIMIT 20` | Reveals whether values are typos, codes, composites, or wrong column entirely |

The investigation order matters. Run distinguishing queries by **information gain** — the query that splits the hypothesis space the most goes first.

### Worked example — Phase 1 Q9 ("customer_segment 47 distinct values")

The original answer fixated on hypothesis 3 (schema mislabel) and proposed three queries that all served that one hypothesis. The senior version: enumerate all six categories, then design 4-5 queries each of which rules in/out distinct candidates. Same data, same surprise, fundamentally different investigation quality.

The score gap (5.5 → target 8.5+) reflects exactly this difference: hypothesis fixation vs. structured enumeration.

### Generalizes to

- Debugging production bugs (multiple hypothesis space, distinguishing log queries)
- Root-cause analysis on outages (the "5 whys" with explicit candidate enumeration at each level)
- Performance investigations (slow query → CPU? IO? memory? lock contention? — each has a distinguishing diagnostic)
- Code review on suspicious behavior (multiple ways the bug could be produced; design tests that distinguish between them)

The pattern transfers anywhere the impulse is "let me just check X" — that's the sign you should pause and enumerate first.

---

## How to Add to This File

When a new mental model surfaces in conversation:

1. **Recognize it as a pattern.** Mental models are reusable thinking tools, not one-off tips. Ask "would I apply this in a different context too?" If yes — it's a model.
2. **Name it.** A short evocative phrase that you can reach for later.
3. **Write the four sections:** the model, why it works, when to apply, worked example.
4. **Cite where it surfaced.** Link back to the conversation/phase where you first applied it. This builds the personal pattern history that makes the file uniquely yours.

Models will accumulate from every phase. The goal isn't comprehensiveness — it's having a reachable set of thinking tools you can pattern-match against under interview pressure.
