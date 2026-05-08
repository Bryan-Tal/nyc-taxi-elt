# Data Engineering Synthesis Questions

> **Purpose:** End-of-phase synthesis drills to test cross-component understanding before advancing to the next phase. Updated as each phase completes.
>
> **Format:** ~6 synthesis questions ("how X and Y work together") + ~4 scenario/debugging questions per phase.
>
> **Scoring:** Technical Accuracy 40% / Conceptual Depth 30% / Vocabulary Precision 20% / Trade-off Awareness 10%. Average ≥8.0 across all 10 questions = phase complete, advance to next.
>
> **Companion files:**
> - [`synthesis-answers.md`](./synthesis-answers.md) — model answers for questions completed
> - [`synthesis-log.md`](./synthesis-log.md) — practice log of hardest questions and weak patterns

---

## Table of Contents

- [Phase 0 — Platform Foundation (Setup)](#phase-0--platform-foundation-setup)
  - [Phase 0 Re-drill](#phase-0-re-drill-triggered-by-74510-average) *(triggered by below-threshold drill average)*
- [Phase 1 — Data Source & Exploration](#phase-1--data-source--exploration)
  - [Phase 1 Re-drill](#phase-1-re-drill-triggered-by-68510-average) *(triggered by below-threshold drill average)*
- [Phase 2 — Ingestion Layer](#phase-2--ingestion-layer) *(coming soon)*
- [Phase 3 — dbt Transformations](#phase-3--dbt-transformations) *(coming soon)*
- [Phase 4 — Orchestration with Airflow](#phase-4--orchestration-with-airflow) *(coming soon)*
- [Phase 5 — CI/CD with GitHub Actions](#phase-5--cicd-with-github-actions) *(coming soon)*
- [Phase 6 — Documentation & Polish](#phase-6--documentation--polish) *(coming soon)*

---

## Phase 0 — Platform Foundation (Setup)

**Drill date:** 2026-04-29
**Coverage:** Snowflake account/RBAC, AWS S3/IAM, storage integration, Docker Compose, Airflow stack, repo hygiene.

### Synthesis Questions

#### Q1 — End-to-end flow

> Trace what happens when Snowflake successfully reads `s3://your-bucket/yellow/2024-01.parquet` via `COPY INTO`. Name every component touched, in order, and what each one *does* and *checks*. Include both Snowflake-side and AWS-side components.

**Hint:** Think about the request as a journey through 3 layers: Snowflake checks something first, then AWS authenticates, then AWS authorizes. Each layer has its own gate.

**Resources:** Flashcards `Snowflake Storage Integration`, `STORAGE_ALLOWED_LOCATIONS`, `AWS STS`, `AssumeRole`, `Trust Policy vs Permissions Policy`. Also see [Snowflake's data-loading flow diagram](https://docs.snowflake.com/en/user-guide/data-load-s3-config-storage-integration) — focus on the architecture diagram, skip the setup steps.

---

#### Q2 — Why two layers of access control

> You configured both `STORAGE_ALLOWED_LOCATIONS` on the Snowflake integration *and* an IAM permissions policy on the AWS role. Why both? What does each one protect against that the other doesn't? Give a concrete failure scenario where one layer saves you and the other wouldn't.

**Hint:** This is a "defense in depth" question. Ask: *what happens if one layer is misconfigured but the other is correct?* Walk through both directions.

**Resources:** Flashcards `STORAGE_ALLOWED_LOCATIONS`, `Trust Policy vs Permissions Policy`, `Principle of Least Privilege`. Think about: who controls each policy? What's the threat model if one of those control surfaces is breached?

---

#### Q3 — The role of medallion separation

> Your Snowflake database has four schemas: RAW, STAGING, MARTS, SNAPSHOTS. A junior engineer asks, "Why not just put everything in one schema and use table prefixes like `raw_trips`, `staging_trips`, `marts_trips`?" Defend the four-schema design. Mention at least three concrete advantages — at least one related to security, at least one related to lifecycle/retention.

**Hint:** Schemas are a permission boundary, not just a naming convention. Think about what you can do *to a schema* that you can't easily do *to a name prefix*. Also think about who consumes each layer and what queries should reach each layer.

**Resources:** Flashcards `Medallion Architecture`, `GRANT ON FUTURE`, `Functional Role vs Access Role`. Consider: how would you write a permissions grant for "analysts can read staging but only marts in production"?

---

#### Q4 — Docker + Airflow + your repo

> Walk through what happens at the moment you run `docker compose up -d` from your repo root. Specifically: how does the code in your `airflow/dags/` directory end up executable inside the running container? How does the Postgres metadata DB connect to the Airflow services? What would break if you deleted the `volumes:` block from `docker-compose.yaml`?

**Hint:** This question is testing whether you understand the *boundary* between host machine and container. The DAG files exist on your Mac filesystem — but Airflow runs inside a Linux container. Something has to bridge that gap. Same for the database connection.

**Resources:** Flashcards `Docker Image vs Container`, `Docker Volume`, `Bind Mount vs Volume`, `Airflow Metadata Database`. Look at your actual `docker-compose.yaml` — pay attention to the `volumes:` and `environment:` sections.

---

#### Q5 — Cost as an architectural concern

> The decisions to put Snowflake and S3 in the same AWS region, set `AUTO_SUSPEND = 60`, and pick `WAREHOUSE_SIZE = XSMALL` are all cost-related. Explain *each* decision in terms of what it specifically prevents. Then describe what would change about each decision if this were a production system serving 100 concurrent analysts instead of one.

**Hint:** Each setting prevents a *different* category of cost: data transfer, idle compute, oversized compute. Then for production, ask: *what tradeoff am I making by being cheap, and would that tradeoff hurt at scale?*

**Resources:** Flashcards `AUTO_SUSPEND`, `AUTO_RESUME`, `Snowflake Virtual Warehouse`, `S3 Bucket`. AWS pricing model knowledge: data egress fees, S3 cross-region transfer costs, Snowflake credit consumption.

---

#### Q6 — Identity vs authorization

> In your Phase 0 setup, list every distinct *identity* (human or service) that exists across both AWS and Snowflake. For each identity, name what it can do and what *grants* or *policies* control that. The point of this question is to force you to enumerate the cast of characters and not conflate them.

**Hint:** Don't forget identities you didn't create directly but that exist anyway — like Snowflake's *own* IAM user (the one returned by `DESC INTEGRATION`). There are at least 5 distinct identities involved in Phase 0. Name them all and what each can do.

**Resources:** Flashcards `IAM Role`, `IAM User`, `Trust Policy`, `IAM Policy`, `Snowflake RBAC Model`, `GRANT ROLE`, `ACCOUNTADMIN`. Re-read the trust policy JSON you wrote — note the `Principal` block. That principal *is* an identity.

---

### Scenario Questions

#### Q7 — Failure scenario A

> You schedule a daily Airflow DAG to run `COPY INTO` from your S3 stage at 3 AM. It works for a week, then on day 8 it fails with `Access Denied (403) retrieving information from the bucket`. Nothing in your code or configuration has changed. Walk through your debugging process: what do you check first, second, third, and what's a likely root cause that fits the pattern? (Hint: think about what *can* change in AWS/Snowflake without anyone touching code.)

**Hint:** "Nothing changed in code/config" is the key constraint. So what *can* change without code changes? Think about: credentials with TTLs, automated rotations, temporary tokens, pulled keys from leaked-secret scanners, IAM policy version bumps. The 8-day pattern is a clue.

**Resources:** Flashcards `AWS STS`, `AssumeRole`, `CloudTrail`. The first thing to check in *any* AWS auth failure is CloudTrail.

---

#### Q8 — Failure scenario B

> A colleague clones your `nyc-taxi-elt` repo, runs `docker compose up airflow-init`, and immediately gets an error in the init container before any Airflow code runs. They've installed Docker and have a working internet connection. What's the most likely missing piece, and why would your repo not have caught this in code review?

**Hint:** What's in the repo vs what's not in the repo? You explicitly *don't* commit certain things. What does the init container need to start that wouldn't be in a fresh clone?

**Resources:** Flashcards `Pre-commit Audit Discipline`, `Conventional Commits`. Look at your `.gitignore` — what does it block from being committed? Your colleague has the repo but is missing what you have on your machine.

---

#### Q9 — Failure scenario C

> You run `LIST @NYC_TAXI.RAW.NYC_TAXI_STAGE/yellow/` in Snowflake and it returns a list of files successfully. Five minutes later, you run the *exact same* query and get an error. Network connectivity is fine. The integration hasn't been edited. What changed, and how would you confirm it without touching AWS?

**Hint:** "The integration hasn't been edited" — but did you edit anything else? Roles? Schemas? Stages? Think about object resolution and session state. Also: STS credentials have lifetimes, but those don't usually expire in 5 minutes by default.

**Resources:** Flashcards `Snowflake Object Namespace`, `USE ROLE`, `Snowflake Worksheet`. Run `SELECT CURRENT_ROLE(), CURRENT_DATABASE(), CURRENT_SCHEMA();` in your head as a debugging step.

---

#### Q10 — Design defense

> A senior engineer reviews your Phase 0 setup and says: "This is overengineered for a personal project. You don't need a separate IAM role, a storage integration, multiple Snowflake schemas, or RBAC. Just put your AWS keys directly in a stage and use `ACCOUNTADMIN` for everything." Defend your choices. For *each* choice they criticized, explain (a) what concrete risk the simpler version exposes you to, and (b) what skill or interview-relevant signal the proper version demonstrates. This is the question that tests whether you can articulate why you did things the production way.

**Hint:** Every "overengineered" choice has *two* defenses: the **technical** defense (what bad thing can happen with the simpler approach) and the **professional** defense (what you'd be signaling about your skill level if you took the shortcut). Both matter in real interviews. The senior engineer is testing you, not actually advocating for the bad design.

**Resources:** This question pulls from almost every flashcard. Particularly: `Confused Deputy Problem`, `Principle of Least Privilege`, `ACCOUNTADMIN`, `Functional Role vs Access Role`, `Trust Policy vs Permissions Policy`, `Medallion Architecture`. Think about each shortcut as a "what could go wrong" exercise.

---

### Phase 0 Re-drill (Triggered by 7.45/10 Average)

*Drill date: 2026-04-29. Average across original Q1–Q10 fell below the 8.0 threshold. The three questions below target the lowest-scoring originals (Q6: 5.5, Q4: 6.5, Q2: 7.0) using the same underlying concepts in fresh scenarios — to confirm understanding without rewarding memorization.*

*Rules: average ≥8.0 across all three to greenlight Phase 1. Address every sub-part of multi-part questions explicitly.*

#### Q-Re-1 — Re-drill of Q6 (Identity enumeration)

> Imagine you've added a Phase 2 ingestion script that runs *inside* the Airflow container, reads from S3, and writes to Snowflake. Enumerate every distinct identity (human or service) involved in *just one execution* of that script — from the moment Airflow triggers it to the moment data lands in Snowflake. For each identity, name what authenticates it and what authorizes its actions. (At least 6 identities involved; full credit for naming all of them precisely.)

**Why this variant:** same concept (identity enumeration), but adds the Airflow execution layer to test whether the model has solidified or whether new identities still get lost in the cracks.

**Hint:** Start at Airflow and walk forward. The DAG is its own actor. The container is another. The Snowflake connection has identity. The S3 client has identity. Don't miss anything. *And remember from Q6 grading:* `Principal` is a JSON field naming an identity, not the identity itself.

**Resources:** Flashcards `IAM Role`, `IAM User`, `Trust Policy`, `Trust Policy vs Permissions Policy`, `Snowflake RBAC Model`, `GRANT ROLE`, `ACCOUNTADMIN`, `AssumeRole`. Also re-read the synthesis-answers Q6 model answer for the full cast of 8 identities — this question adds 1–2 more (the Airflow scheduler context, the script's runtime AWS/Snowflake credentials).

---

#### Q-Re-2 — Re-drill of Q4 (Docker composition)

> Your `docker-compose.yaml` includes the line `_PIP_ADDITIONAL_REQUIREMENTS: ${_PIP_ADDITIONAL_REQUIREMENTS:-}` in the airflow-common environment. Walk me through: (a) what this line does, (b) where the value comes from, (c) when in the container lifecycle the packages get installed, and (d) why this approach is dev-only and what the production replacement would be. **Make sure you address all four parts.**

**Why this variant:** same composition mechanics as Q4, different specific feature. The "make sure you address all four parts" prompt is intentional — directly tests the answer-completeness pattern that cost points across the original drill.

**Hint:** The `${VAR:-}` syntax is a shell variable expansion with a default. Where do shell variables in compose files come from? You set this up in Phase 0; revisit your `.env` file. For part (c), think about *image build time* vs *container runtime*. For part (d), recall what we hit when this approach made the webserver unhealthy.

**Resources:** Flashcards `Docker Image vs Container`, `Docker Image Layers`, `Custom Airflow Dockerfile`, `Airflow Task Execution Patterns`. The custom-Dockerfile flashcard answers most of part (d) directly.

---

#### Q-Re-3 — Re-drill of Q2 (Defense-in-depth)

> Your local `.env` file contains AWS access keys for the `nyc-taxi-elt-user` IAM user. The `.env` is gitignored and stays on your laptop. Despite this, your repo also enforces a permissions policy on the `nyc-taxi-elt-user` IAM user that scopes it to the single bucket. **Why both?** What does the `.env` gitignore protect against that the IAM permissions policy doesn't, and vice versa? Give a concrete failure scenario for each.

**Why this variant:** same defense-in-depth concept as Q2, different layer pair (gitignore + IAM scoping instead of STORAGE_ALLOWED_LOCATIONS + IAM permissions). Tests whether the bidirectional reasoning has generalized beyond the original scenario.

**Hint:** For each layer, ask "what's the threat scenario this defends against, and what threat does it NOT defend against?" Think about: where can the keys leak from in each scenario, and what does each defense stop?

**Resources:** Flashcards `IAM Policy`, `Trust Policy vs Permissions Policy`, `Principle of Least Privilege`, `Pre-commit Audit Discipline`. Also re-read your original Q2 answer and the model answer in synthesis-answers — the bidirectional reasoning pattern is the key takeaway.

---

## Phase 1 — Data Source & Exploration

*Drill date: TBD. Covers grain, dimension classification, SCD types, role-playing dimensions, star vs snowflake, schema evolution, type drift handling.*

### Synthesis Questions

#### Q1 — Grain & Its Consequences

> Your fact table `fct_shipments` has columns: `shipment_id`, `customer_id`, `origin_warehouse_id`, `destination_address_id`, `carrier_id`, `weight_lbs`, `total_cost`, `shipped_at`, `delivered_at`. State the grain in one sentence. Then describe **two analytical questions this grain supports** and **two analytical questions it does NOT support** (and what grain you would need for those). Be specific about why.

**Hint:** Apply the Grain First mental model. Look at what column combinations would have to be unique for each row to represent a single instance of something.

**Resources:** `mental-models.md` §5 (Grain First, Schema Second), flashcard "Grain"

---

#### Q2 — Dimension Classification

> A teammate is designing a fact table for an e-commerce orders dataset and shows you these source columns: `order_id`, `customer_id`, `product_id`, `coupon_code` (string, ~50 distinct values like "SUMMER10"), `discount_amount` (decimal), `is_gift` (boolean), `order_status` (string: "pending"/"shipped"/"delivered"/"cancelled"), `device_type` (string: "mobile"/"desktop"/"tablet"). For each non-PK column, classify it as: dimension table / degenerate dimension / pure measure. Justify each classification using the Richness Test.

**Hint:** Three tests for "dimension table": cardinality > 2-5, stability of values, descriptive richness. Failing any → degenerate. Continuous numeric measures → pure measure.

**Resources:** `mental-models.md` §6 (Richness Test), flashcards "Degenerate Dimension Heuristic"

---

#### Q3 — SCD Type Reasoning

> For an analytical warehouse tracking historical product sales, you have three dimensions:
>
> - `dim_product` — products are renamed occasionally (e.g., "iPhone 14 Pro" → "iPhone 14 Pro Max"); we want historical reports to show what the product was called at the time of sale
> - `dim_category` — broad categories like "Electronics", "Apparel", "Home Goods" — categories rarely change, but a typo correction in 2024 changed "Apparrel" to "Apparel"
> - `dim_currency` — `currency_code`, `currency_name`, `symbol` — currency codes are stable; descriptions are stable
>
> Assign an SCD type (0/1/2/3) to each dimension and explain your reasoning. **Address all three dimensions explicitly.**

**Hint:** SCD type is determined by what *changes*, not what's *added*. Ask: when an existing row's attributes change, what should historical analyses see?

**Resources:** `mental-models.md`, flashcards "SCD Type 1/2/3", `design-doc.md` §5.3

---

#### Q4 — Role-Playing Dimensions

> Explain (a) what a role-playing dimension is, (b) why our project uses one for `dim_location` and `dim_date`, and (c) write the SQL skeleton (no need for a complete query — just JOINs and aliases) showing how you'd query "for each pickup borough, what's the average trip duration grouped by pickup day-of-week?" using the role-playing dimensions correctly.

**Hint:** Role-playing means the same dimension table referenced multiple times by one fact, with each reference playing a different role. SQL aliases disambiguate.

**Resources:** `design-doc.md` §5.6, flashcard "Role-playing dimension"

---

#### Q5 — Star vs Snowflake (Comparison)

> A senior engineer reviews your `dim_location` design and proposes normalizing it into three tables: `dim_location` (location_id, zone, borough_id, service_zone_id), `dim_borough` (borough_id, borough_name), `dim_service_zone` (service_zone_id, service_zone_name). Defend your choice to keep `dim_location` flat. Address: (a) what shape this proposal would create, (b) historically why this normalized shape existed, (c) why modern columnar warehouses make it less compelling, and (d) the specific cost-benefit for our 260-row dimension.

**Hint:** Same shape of question as Q10 from Phase 0 — defend the design choice with specific risks the alternative exposes you to.

**Resources:** `design-doc.md` §5.1, `mental-models.md`, flashcard "Star vs Snowflake Schema"

---

#### Q6 — Schema vs Semantics Stability (Synthesis)

> You're hired to analyze a 10-year dataset of online ad impressions for a question about engagement trends. The schema is identical across all 10 years (good news!). Walk through your investigation plan to validate that the *semantics* are also stable across the period. Specifically: (a) what would you query, (b) what would you look for, and (c) name two distinct categories of semantic drift that schema-level inspection would miss.

**Hint:** Apply the new mental model directly. Two-pass investigation: structural pass + semantic pass.

**Resources:** `mental-models.md` §7 (Schema vs Semantics Stability), flashcard "Schema vs Semantics Stability"

---

### Scenario Questions

#### Q7 — Type Drift Pipeline Decision

> You're loading historical NYC TLC data: 2013 (column type INTEGER), 2018 (DOUBLE), 2024 (BIGINT) for a column `trip_count`. Three approaches are proposed:
>
> 1. Cast everything to BIGINT in Python before loading
> 2. Land raw types in `RAW`, cast in `STAGING` with `TRY_CAST` to BIGINT
> 3. Use schema-evolution machinery (e.g., dbt-snowflake Iceberg tables) to handle evolution automatically
>
> Recommend one approach and explain why it's better than each of the other two for this specific scenario. Include one concrete failure mode each rejected approach would create.

**Hint:** The right answer ties to the architectural conclusion of our Phase 1 Step 3 investigation. Type-tolerant casting in STAGING is the chosen pattern.

**Resources:** `design-doc.md` §7, flashcards "TRY_CAST vs CAST", "Type Coercion Safety"

---

#### Q8 — Surrogate Key Failure Mode

> Your colleague is implementing the SCD Type 2 logic for `dim_location` and decides to skip surrogate keys to "keep it simple" — using `location_id` directly as the primary key. They argue: "We have a `valid_from`/`valid_to` window, so we can always identify the right row by joining on `location_id` AND a date range comparison." Walk through what specifically goes wrong with this approach. Include both a correctness failure and a performance failure.

**Hint:** Surrogate keys give you exactly-one-match-per-fact-row. Without them, fact joins become range-based rather than equality-based.

**Resources:** `design-doc.md` §5.4, flashcard "Surrogate Key vs Natural Key"

---

#### Q9 — Profiling Investigation Surprise

> You profile a new dataset and find that a column `customer_segment` has 47 distinct values when documentation says there should be only 5 (Bronze/Silver/Gold/Platinum/Diamond). Walk through your investigation plan — what queries would you run, in what order, and what hypotheses would you be testing? Identify at least three plausible root causes and what each would look like in your query results.

**Hint:** Apply the Predict Before You Query mental model. Then plan investigative queries that would distinguish between plausible explanations.

**Resources:** `mental-models.md` §4 (Predict Before You Query)

---

#### Q10 — Defending the Whole Design

> A new tech lead joins your team and questions the entire star schema design: *"Why are we using a separate `dim_date` table when every modern warehouse has built-in date functions? Why role-playing dimensions instead of just having `pickup_borough` and `dropoff_borough` columns directly in the fact? And why a flat `dim_location` when we can compute everything from PostGIS-style spatial libraries?"* Defend each of the three design choices. For each, explain (a) what concrete capability you'd lose with their proposal, and (b) what skill or interview-relevant signal the proper version demonstrates.

**Hint:** This is the Phase 1 equivalent of Phase 0 Q10 (Design Defense). Multiple sub-parts; address each explicitly.

**Resources:** Whole `design-doc.md`, especially §5

---

### Phase 1 Re-drill (Triggered by 6.85/10 Average)

*Drill date: 2026-05-07. Average across original Q1–Q10 fell below the 8.0 threshold. The three questions below target the lowest-scoring originals (Q9: 5.5, Q10: 5.5, Q6: 6.0) using the same underlying concepts in fresh scenarios — to confirm understanding without rewarding memorization.*

*Rules: average ≥8.0 across all three to greenlight Phase 2. Address every sub-part. Per re-drill consolidation rule, EACH question gets a consolidation session BEFORE re-testing — confused fundamentals are walked through Socratically first, then the re-drill question is asked.*

#### Q-Re-1 — Re-drill of Q9 (Profiling Investigation)

> You're profiling a new HR analytics dataset for a Fortune 500 company. The column `department_code` is documented as a 4-character code (e.g., "FINX", "HRBP", "ENGG"). When you query distinct values, you find 327 distinct codes — some 4 characters, some 3, some 5, some with hyphens, some with numbers. Walk through your investigation plan: (a) what queries would you run in what order, (b) what hypotheses are you testing with each query, and (c) name **at least three plausible root causes** with the specific data signature each would leave in your query results.

**Why this variant:** same concept (structured profiling investigation), different domain (HR data instead of customer segments). Tests whether the *enumeration depth + decision-tree investigation* pattern transferred or whether it was answer-specific to the original question.

**Hint:** This is the enumeration-depth pattern in disguise. Count what's asked: **at least three causes, each with diagnostic fingerprints, plus the queries that would distinguish them.** A complete answer enumerates each cause with its expected data signature.

**Resources:** `mental-models.md` §4 (Predict Before You Query), §7 (Schema vs Semantics Stability). Re-read your original Q9 answer in `synthesis-answers.md` for the gap pattern.

---

#### Q-Re-2 — Re-drill of Q10 (Design Defense)

> A staff engineer reviews your dbt project and questions three design choices: *"(1) Why are we materializing fct_trips as a table instead of a view — views are cheaper to maintain. (2) Why use surrogate keys at all when we could just join on the natural keys directly — it's one fewer column to maintain. (3) Why have a separate STAGING layer when we could just transform RAW directly into MARTS?"* Defend each design choice. For each, explain **(a) what concrete capability you'd lose** with their proposal AND **(b) what skill or interview-relevant signal the proper version demonstrates.** Address all six sub-parts (3 challenges × 2 angles each).

**Why this variant:** same design-defense pattern, different design choices, fresh interview scenario. Specifically tests whether the **enumeration depth on multi-part questions** lesson transferred. The original Q10 only addressed (a) for each challenge; this re-drill explicitly enumerates the six items.

**Hint:** Six items to address. Apply the diagnostic question: *"How many distinct things does this question ask me to enumerate? Have I named that many?"* If you find yourself wrapping up after three points, you're not done.

**Resources:** `design-doc.md` for the architecture decisions; `mental-models.md` for the patterns to invoke.

---

#### Q-Re-3 — Re-drill of Q6 (Schema vs Semantics Stability)

> You inherit an 8-year e-commerce orders dataset from a previously-acquired company that you're now integrating. The schema is identical across all 8 years. Walk through your investigation plan to validate the *semantics* are stable: (a) what queries would you run, (b) what would you specifically look for in the results, and (c) name **three distinct categories of semantic drift** schema-level inspection would miss — for each category, give a concrete example of what it might look like in this e-commerce dataset.

**Why this variant:** same mental model (Schema vs Semantics Stability), different domain (e-commerce instead of ad impressions), with a tighter requirement that each category include an example *grounded in the e-commerce context*. Tests whether the mental-model framework was internalized or just exposed.

**Hint:** Open the `mental-models.md` doc. §7 (Schema vs Semantics Stability) has a "diagnostic ritual" with specific drift categories enumerated. The re-drill rewards reaching for this structure rather than improvising.

**Resources:** `mental-models.md` §7 specifically. The original Q6 model answer in `synthesis-answers.md` for the gap pattern.

---

## Phase 2 — Ingestion Layer

*Questions will be added at the end of Phase 2.*

---

## Phase 3 — dbt Transformations

*Questions will be added at the end of Phase 3.*

---

## Phase 4 — Orchestration with Airflow

*Questions will be added at the end of Phase 4.*

---

## Phase 5 — CI/CD with GitHub Actions

*Questions will be added at the end of Phase 5.*

---

## Phase 6 — Documentation & Polish

*Questions will be added at the end of Phase 6.*

---

## How to Use This Drill File

1. **Skim relevant flashcards first** (~10 minutes) — refresh, don't memorize
2. **Answer questions in order** within a phase — earlier ones build mental model for later ones
3. **Bullets are fine, precision matters more than length** — aim for ~30–60 second responses
4. **Use proper vocabulary** — "STS AssumeRole" beats "AWS auth thing"; vocab precision is 20% of the score
5. **For scenarios, narrate the diagnostic process** — which logs/commands you'd reach for, in what order
6. **Don't worry about being wrong** — this is calibration. Lower scores just mean re-drilling specific topics before advancing
