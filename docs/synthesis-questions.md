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
- [Phase 1 — Data Source & Exploration](#phase-1--data-source--exploration) *(coming soon)*
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

*Questions will be added at the end of Phase 1.*

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
