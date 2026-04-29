# Data Engineering Synthesis — Model Answers

> **Purpose:** Reference-quality answers to synthesis questions, recorded only after Bryan has attempted the question. Answers reflect the 9/10 standard — what a strong senior-DE candidate would say in an interview.
>
> **Format:** For each question, three sections:
> - **Bryan's answer (graded)** — what was submitted, with score and feedback
> - **Model answer** — the 9/10 reference response
> - **Key lessons** — vocabulary fixes, conceptual sharpening, what to carry forward
>
> **Companion files:**
> - [`synthesis-questions.md`](./synthesis-questions.md) — drill questions for self-testing (no answers)
> - [`synthesis-log.md`](./synthesis-log.md) — practice log of weak patterns

---

## Phase 0 — Platform Foundation (Setup)

### Q1 — End-to-end flow

**The question:**
> Trace what happens when Snowflake successfully reads `s3://your-bucket/yellow/2024-01.parquet` via `COPY INTO`. Name every component touched, in order, and what each one *does* and *checks*.

#### Bryan's answer — 7.5/10

> Firstly, Snowflake checks whether the bucket resides in STORAGE_ALLOWED_LOCATIONS. If this passes it then begins running Storage Integration in order to connect to AWS' S3 bucket via external IAM role. Snowflake's external stage uses STS via the AssumeRole API call in order to attempt to secure the temporary credentials: Temporary ID, secret ID, and SessionToken. This works given that the externalID matches the trust policy's externalID, as well as that the permissions policy is valid. If this is validated, snowflake can use its IAM role in order to directly access the S3 bucket and copy the relevant data.

| Dimension | Score | Why |
|---|---|---|
| Technical Accuracy | 7.5/10 | Core flow correct. Two minor inaccuracies and one missing component. |
| Conceptual Depth | 8/10 | Correctly identified all three control layers (Snowflake allowlist → STS auth → AWS authorization). |
| Vocabulary Precision | 7/10 | Most terms used correctly. "Temporary ID" / "secret ID" are imprecise. |
| Trade-off Awareness | 6/10 | Didn't touch on why this flow exists vs. simpler alternatives. |

#### Model answer (9/10)

> 1. **Snowflake-side gate.** The query references `@NYC_TAXI.RAW.NYC_TAXI_STAGE/yellow/2024-01.parquet`. Snowflake checks the storage integration's `STORAGE_ALLOWED_LOCATIONS` to confirm the path is in the allowlist. If not, fails with no AWS traffic.
> 2. **STS AssumeRole call.** Snowflake's IAM user (visible as `STORAGE_AWS_IAM_USER_ARN` from `DESC INTEGRATION`) calls `sts:AssumeRole` on `snowflake-s3-role`, presenting `ExternalId` for the confused deputy mitigation. STS evaluates the trust policy: does the Principal match? Does the ExternalId match? If yes, STS issues a credential bundle (Access Key ID, Secret Access Key, Session Token), typically valid 1 hour.
> 3. **S3 API calls.** Snowflake uses those temporary credentials to call `s3:ListBucket` (to enumerate files) and `s3:GetObject` (to read Parquet bytes). Each call is evaluated against the role's permissions policy. If the policy permits the action on this resource ARN, S3 returns data; otherwise `AccessDenied`.
> 4. **Snowflake processes the data.** Snowflake reads Parquet column metadata, applies the file format (`TYPE = PARQUET`), and inserts rows into the target table.

#### Key lessons

1. **The STS credential triple has specific names:** Access Key ID, Secret Access Key, Session Token. Same shape as static AWS credentials but with the session token added. Avoid imprecise names like "Temporary ID" or "secret ID."
2. **The integration (not the stage) initiates AssumeRole.** The stage references the integration; the integration is the security primitive. One integration can back multiple stages.
3. **Name the principal explicitly:** Snowflake's IAM user — the value from `STORAGE_AWS_IAM_USER_ARN` in `DESC INTEGRATION` — is what calls AssumeRole. The trust policy authorizes that specific principal.
4. **Name AWS API calls by their action name:** `s3:ListBucket`, `s3:GetObject`, `sts:AssumeRole`. Using the formal action names signals you've actually configured these IAM policies, not just read about them.
5. **There are at least 4 distinct components in the flow:** Snowflake-side gate, STS, S3 (with permissions policy enforcement), and the data-processing step. Naming all four is the difference between 7.5 and 9.

---

### Q2 — Why two layers of access control

#### Bryan's answer — 7.0/10

> We configure STORAGE_ALLOWED_LOCATIONS on the snowflake integration in order to prevent an over-permissioned IAM role from being misused via Snowflake. We also configure an IAM permissions policy in order to authorize what the assumed role is able to do.
> Scenario: A bad actor is able to secure an IAM role with strong permissions. If they attempt to access a bucket, but snowflake does not have that bucket listed in it's allowed locations, Snowflake will not allow the integration to access the bucket.

| Dimension | Score |
|---|---|
| Technical Accuracy | 7/10 |
| Conceptual Depth | 6/10 |
| Vocabulary Precision | 8/10 |
| Trade-off Awareness | 7/10 |

#### Model answer (9/10)

The two layers protect against compromise in **opposite directions** — that's the heart of defense in depth:

- `STORAGE_ALLOWED_LOCATIONS` (Snowflake-side): protects against AWS compromise leaking *into* Snowflake. If your IAM role gets over-permissioned (someone widens the bucket policy by mistake), Snowflake still won't let the integration touch buckets not on the allowlist.
- IAM permissions policy (AWS-side): protects against Snowflake compromise leaking *out to* AWS. If someone gets `ELT_ROLE` on Snowflake, they could try to point the integration at any path on the allowlist — but AWS still checks "does the role actually have permission to read this object?" via the permissions policy.

**Concrete bidirectional scenarios:**
- An ops engineer accidentally attaches `AmazonS3FullAccess` to the role. Without `STORAGE_ALLOWED_LOCATIONS` scoping, that mistake is now exploitable through Snowflake. *Allowlist saves you.*
- A compromised Snowflake session tries to read a bucket on the allowlist that the role wasn't actually granted in IAM. *Permissions policy saves you.*

#### Key lessons

1. "Defense in depth" questions test whether you can articulate the threat model in *both directions*, not just one.
2. The two policies live on different platforms (Snowflake vs AWS) intentionally — different administrators, different audit trails, different blast radii.

---

### Q3 — Medallion separation

#### Bryan's answer — 8.5/10 ✓

> Having 4 schemas goes back into the medallion architecture: RAW represents the data as-ingested. STAGING represents the data that has been cleaned and typed. MARTS represents the production-level data that is aggregated and modeled. SNAPSHOTS represents a development environment.
> [...] Analysts, and engineers may both be able to access STAGING, but an Engineer may have write permissions whereas an Analyst may just have read permissions. Stakeholders should only have read permissions to query the production-level data.

| Dimension | Score |
|---|---|
| Technical Accuracy | 9/10 |
| Conceptual Depth | 9/10 |
| Vocabulary Precision | 8/10 |
| Trade-off Awareness | 8/10 |

#### Model answer (9.5/10)

The four schemas exist because schemas are a **permission boundary, retention boundary, and compute boundary** — none of which name prefixes give you.

- **Security boundary:** `GRANT SELECT ON SCHEMA MARTS TO ROLE ANALYST` is one statement. With prefixes, you'd need `GRANT SELECT ON ALL TABLES LIKE 'marts_%'` for every new table — Snowflake doesn't even support that pattern.
- **Lifecycle/retention boundary:** RAW is typically kept long-term (replay-from-source). STAGING is regenerable and often wiped/rebuilt. MARTS need backups and Time Travel. Per-schema retention policies enable each.
- **Compute isolation:** Different schemas can be granted to different warehouses. An analyst's expensive aggregation query against MARTS shouldn't slow down an engineer rebuilding STAGING.
- **Cognitive boundary:** A new engineer landing in `MARTS` schema knows what they're looking at — production-grade, business-ready data. Mixed prefixes in one schema are confusing.

**Correction on SNAPSHOTS:** It's not a development environment. It's where dbt stores **SCD Type 2 history snapshots** — point-in-time states of dimension tables for historical queries.

#### Key lessons

1. Schemas are a permission/retention/compute boundary, not a naming convention.
2. SNAPSHOTS = SCD Type 2 history (production), not dev.
3. When a question asks for "at least three concrete advantages," explicitly list and label them — interviewers count.

---

### Q4 — Docker + Airflow + repo

#### Bryan's answer — 6.5/10

> When I run docker compose up -d, it searches the directory for the docker-compose.yaml file. docker then runs the apache airflow image using the custom environment [...] the 'volumes' section acts more as a bind mount: it connects my host path(s) into the docker container. [...] the second 'volumes' section confirms the connection between airflow and the postgres database.

| Dimension | Score |
|---|---|
| Technical Accuracy | 7/10 |
| Conceptual Depth | 6/10 |
| Vocabulary Precision | 6/10 |
| Trade-off Awareness | 6/10 |

#### Model answer (9/10)

When you run `docker compose up -d`:

1. Compose reads `docker-compose.yaml` in the current directory.
2. It pulls the `apache/airflow:2.10.3-python3.11` image if not cached.
3. It creates **containers** from the image (the image stays unchanged; environment variables are injected at *runtime* into each container).
4. The `airflow-scheduler` and `airflow-webserver` containers wait on `postgres` becoming healthy (`depends_on` + healthcheck).
5. Postgres starts and the named volume `postgres-db-volume` is mounted at `/var/lib/postgresql/data` — this is what makes Postgres metadata persist across `docker compose down`.
6. The Airflow services' service-level `volumes:` block creates **bind mounts**: `./airflow/dags` → `/opt/airflow/dags` etc. This is how DAG files on the host become visible inside the container.
7. Airflow connects to Postgres via the `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN` environment variable — `postgresql+psycopg2://airflow:airflow@postgres/airflow` — using Docker's internal DNS (`postgres` resolves to the postgres container's IP).

**There are TWO `volumes:` blocks doing different things:**
- **Service-level volumes** (under each service) → bind mounts (host path ↔ container path)
- **Top-level `volumes:` block** → declares **named volumes** managed by Docker

If you deleted the `volumes:` block:
- DAGs would not appear in Airflow (the image has no DAG files; bind mount is the only way they get inside)
- Code changes wouldn't propagate (editing on host has no effect without the mount)
- Postgres metadata would be lost on every restart (no persistence without the named volume)

#### Key lessons

1. Image vs container: image is the template, container is the runtime instance with env vars injected.
2. Two kinds of "volumes" in Compose: service-level bind mounts vs top-level named volumes — they serve different purposes.
3. When a question asks "what would break," answer it directly with concrete consequences, not just "the connection wouldn't work."

---

### Q5 — Cost as architecture

#### Bryan's answer — 7.5/10

> Setting AUTO_SUSPEND = 60 [...] Setting WAREHOUSE_SIZE = XSMALL [...] If this were a production system with 100 concurrent analysis attempting to run, we would change the AUTO_SUSPEND to be as short as possible, in order to save on idle compute costs.

| Dimension | Score |
|---|---|
| Technical Accuracy | 8/10 |
| Conceptual Depth | 7/10 |
| Vocabulary Precision | 8/10 |
| Trade-off Awareness | 7/10 |

#### Model answer (9/10)

Three cost decisions:

- **Same-region (Snowflake + S3):** prevents cross-region data transfer fees (~$0.02/GB in AWS). On a few TB, this adds up to real money quickly.
- **AUTO_SUSPEND = 60:** prevents idle compute charges. Snowflake bills per second a warehouse is running, not per query.
- **WAREHOUSE_SIZE = XSMALL:** prevents oversized compute. Each size doubles cost for marginal speedup on small workloads.

**Production with 100 concurrent analysts — counter-intuitive correction:**

Your instinct was "shorter AUTO_SUSPEND saves more." Actually, the trade-off flips at scale:

- AUTO_SUSPEND should usually be **longer** (5–10 min), because every suspend means a ~1 second resume on the next query. With 100 concurrent users, that latency hits all of them. Resume cost > idle cost at high traffic.
- **WAREHOUSE_SIZE doesn't necessarily go up — multi-cluster scaling does.** Snowflake supports `MIN_CLUSTER_COUNT=1, MAX_CLUSTER_COUNT=N` on a warehouse: instead of one LARGE warehouse, you have a MEDIUM that auto-spawns additional clusters under load. This is more cost-efficient than oversizing.
- **Workload separation:** in production, you'd typically have multiple warehouses (`WH_INGEST`, `WH_TRANSFORM`, `WH_ANALYTICS`) so heavy ETL doesn't slow down dashboards.

#### Key lessons

1. Cost trade-offs flip at scale: dev wants fast suspend; prod wants smooth resume.
2. Snowflake's specific scaling primitive is **multi-cluster warehouse**, not just bigger sizes.
3. Same-region pairing is a cost decision worth naming explicitly.

---

### Q6 — Identity enumeration

#### Bryan's answer — 5.5/10

> Snowflake: ELT_ROLE [...] ELT_USER [...] IAM User [...] Principal: AWS [...] AWS S3 Bucket: IAM user nyc-taxi-elt-user

| Dimension | Score |
|---|---|
| Technical Accuracy | 5/10 |
| Conceptual Depth | 5/10 |
| Vocabulary Precision | 6/10 |
| Trade-off Awareness | 7/10 |

#### Model answer (9/10) — the full cast of 8 identities

**Snowflake side:**
1. **Your human Snowflake user** (the trial account login) — granted `ACCOUNTADMIN` and `ELT_ROLE`
2. **`ELT_USER`** (dedicated pipeline user) — granted `ELT_ROLE`
3. **`ACCOUNTADMIN`** (built-in superuser role) — auto-granted at account creation
4. **`ELT_ROLE`** (custom scoped role) — granted USAGE on `WH_ELT`, ALL on `NYC_TAXI` schemas, USAGE on the integration

**AWS side:**
5. **Your human AWS user** (root or named admin) — used for setup
6. **`nyc-taxi-elt-user`** (dedicated programmatic IAM user) — has the access keys in `~/.aws/credentials`; inline policy scoped to the bucket
7. **`snowflake-s3-role`** (IAM role assumed by Snowflake) — trust policy specifies who can assume; permissions policy scopes S3 actions
8. **Snowflake's own IAM user** (managed by Snowflake; visible in `STORAGE_AWS_IAM_USER_ARN` from `DESC INTEGRATION`) — the actual principal that calls AssumeRole

#### Key lesson

`Principal` in a trust policy is **not an identity** — it's a JSON field that *names* which identity is allowed to assume the role. Like the "From:" header in an email — it's a slot that names a sender, not the sender itself.

This is the same shape as Gap #3 (Functional vs Access role labeling): getting separation between layers crisp.

---

### Q7 — Failure scenario A (8-day Access Denied)

#### Bryan's answer — 7.5/10

> I would first look at CloudTrail [...] AssumeRole hands over temporary credentials and they could have expired on the 8th day [...] The IAM permissions/trust policy may have changed due to a data leak.

| Dimension | Score |
|---|---|
| Technical Accuracy | 8/10 |
| Conceptual Depth | 7/10 |
| Vocabulary Precision | 8/10 |
| Trade-off Awareness | 7/10 |

#### Model answer (9/10)

CloudTrail-first is correct — that's the senior instinct. But the 8-day pattern doesn't fit AssumeRole expiration (those are ~1 hour and auto-refreshed by Snowflake on every request). The pattern fits **scheduled infrastructure changes**:

- **Programmatic key rotation** (organizations enforce 7/14/30-day cycles via AWS Config or automation). Less likely here since `COPY INTO` uses the role, not your user's keys — but worth checking.
- **Bucket policies applied by org-level config rules** that override IAM grants.
- **Service Control Policies (SCPs)** in AWS Organizations applied with delay.
- **KMS key rotation** if the bucket uses SSE-KMS.

**Diagnostic order:**
1. CloudTrail's `AssumeRole` event — did the assume succeed? If yes, the issue is downstream of STS.
2. CloudTrail's S3 data events — what specific action was denied?
3. IAM Access Analyzer — does the role still have expected permissions?
4. Bucket policy / SCPs — anything applied at the org level?
5. KMS key policy if encryption is in play.

**Key lesson:** when something fails after a regular interval with "no code changes," look for **scheduled infrastructure automation**, not credential expiration.

---

### Q8 — Failure scenario B (colleague clones repo)

#### Bryan's answer — 8.5/10 ✓

> My colleague is most likely missing a .env file, it is not tracked by git as it is listed in the .gitignore file [...]

| Dimension | Score |
|---|---|
| Technical Accuracy | 9/10 |
| Conceptual Depth | 8/10 |
| Vocabulary Precision | 8/10 |
| Trade-off Awareness | 8/10 |

#### Model answer (9.5/10)

Clean diagnosis. To push past 9: name `.env.example` as the **intentional onboarding mechanism**. The error isn't a bug; it's expected behavior. The standard onboarding flow is:

```bash
git clone <repo>
cp .env.example .env
# fill in .env with own credentials
docker compose up airflow-init
```

Calling this out shows you understand the design wasn't accidental — it's the standard pattern for handling secrets in version-controlled projects, and `.env.example` is the contract between code and environment.

#### Key lesson

Gitignored `.env` + committed `.env.example` is the **12-Factor App** pattern. Naming it that way signals you know the broader principle.

---

### Q9 — Failure scenario C (LIST works, then doesn't)

#### Bryan's answer — 7.5/10

> This may be a quirk of the Snowflake worksheet [...] there may be some type of role or schema change that was run prior [...] you can first determine if you have the appropriate role for what you are doing by running SELECT CURRENT_ROLE().

| Dimension | Score |
|---|---|
| Technical Accuracy | 8/10 |
| Conceptual Depth | 7/10 |
| Vocabulary Precision | 7/10 |
| Trade-off Awareness | 7/10 |

#### Model answer (9/10)

The most precise diagnosis: **session context drift**. The same query string can fail if any of `CURRENT_DATABASE`, `CURRENT_SCHEMA`, `CURRENT_ROLE`, or `CURRENT_WAREHOUSE` changed between runs.

Common causes in a worksheet:
- Running `USE ROLE ...` in another worksheet (changes session-wide active role)
- Running `USE SCHEMA ...` between LIST calls
- The Snowflake UI's "Database/Schema" selector dropdowns at the top — they silently issue `USE` statements when changed

**Best diagnostic command:**
```sql
SELECT CURRENT_ROLE(), CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_WAREHOUSE();
```

All four at once tells the full session state. You named one.

**The fix beyond the diagnosis:** automated scripts and dbt models should always **fully qualify** object references (`@NYC_TAXI.RAW.NYC_TAXI_STAGE/yellow/`). Bulletproof against context drift.

#### Key lesson

Session state is invisible global mutable state. Always check it first when "the same query gave different results."

---

### Q10 — Design defense

#### Bryan's answer — 8.5/10 ✓

> [Multi-paragraph defense covering IAM role, storage integration, schema separation, and RBAC, each with a stated risk]

| Dimension | Score |
|---|---|
| Technical Accuracy | 9/10 |
| Conceptual Depth | 8/10 |
| Vocabulary Precision | 9/10 |
| Trade-off Awareness | 8/10 |

#### Model answer notes

Strong technical defense across all four shortcuts. To reach 9.5, address part (b) of the question more explicitly: **what skill/interview signal does the proper version demonstrate?**

- IAM role + storage integration: "I've shipped production-grade Snowflake integrations, not just done tutorials"
- Multiple schemas: "I think about access patterns and team workflows at design time"
- RBAC over ACCOUNTADMIN: "I think about security as a default, not an afterthought"

The (b) part is what makes the question *interview-relevant* rather than just *technical*. You scored 8.5 because (a) was excellent throughout.

#### Key lesson

Senior interviews test "would I trust this person to make design decisions on my team?" — articulating *why* you chose the production way (not just *what* the production way is) demonstrates the judgment they're looking for.

---

## Phase 0 Drill Final Verdict

**Average across 10 questions: 7.45/10**

Below the 8.0 threshold. Re-drill required for the three lowest-scoring questions (Q6, Q4, Q2) before advancing to Phase 1.

**Recurring pattern identified across this batch:**

The conceptual understanding is solid — no question revealed a missing concept. The points lost are concentrated in:
1. **Answer completeness** — addressing every part of multi-part questions, not just the part you're most confident on
2. **Vocabulary precision on layered systems** — distinguishing roles vs principals vs identities, integration vs stage, image vs container, etc.
3. **Pushing answers to senior depth** — naming AWS API calls, citing specific Snowflake primitives (multi-cluster warehouses, Time Travel), articulating both directions of a defense-in-depth argument

---

## Phase 1 — Data Source & Exploration

*Answers will be added as Bryan completes Phase 1's drill.*

---

## Phase 2 — Ingestion Layer

*Answers will be added as Bryan completes Phase 2's drill.*

---

## Phase 3 — dbt Transformations

*Answers will be added as Bryan completes Phase 3's drill.*

---

## Phase 4 — Orchestration with Airflow

*Answers will be added as Bryan completes Phase 4's drill.*

---

## Phase 5 — CI/CD with GitHub Actions

*Answers will be added as Bryan completes Phase 5's drill.*

---

## Phase 6 — Documentation & Polish

*Answers will be added as Bryan completes Phase 6's drill.*
