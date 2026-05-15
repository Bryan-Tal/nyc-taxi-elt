# Data Engineering Synthesis — Model Answers

> **Purpose:** Reference-quality answers to synthesis questions, recorded only after Bryan has attempted the question. Answers reflect the 9/10 standard — what a strong senior-DE candidate would say in an interview.
>
> **Format:** For each question, three sections:
> - **Bryan's answer (graded)** — what was submitted, with score and feedback
> - **Model answer** — the 9/10 reference response
> - **Key lessons** — vocabulary fixes, conceptual sharpening, what to carry forward
>
> **Standards (elevated 2026-05-07):** Drill advancement requires **≥8.5 average AND zero individual questions <8.0**. Sub-8.0 questions trigger consolidation sessions until ≥95% topical-fluency confidence is reached, only then re-drill. Verdicts recorded in this file under previous standards (≥8.0) are preserved as historical record but marked where retroactive re-drilling is planned.
>
> **Retroactive Phase 0 re-drill (planned for after Phase 5):** Phase 0 was cleared under the previous 8.0 threshold. Several questions (Q1: 7.5, Q2: 7.0, Q4: 6.5, Q5: 7.5, Q6: 5.5, Q7: 7.5, Q9: 7.5, Q-Re-1: 7.5) would not clear under the elevated standard. After Phase 5 ships, all Phase 0 questions scoring <8.0 will be re-drilled with consolidation-first protocol. This locks in foundational fluency before Phase 6 portfolio polish.
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

**The question:**
> You configured both `STORAGE_ALLOWED_LOCATIONS` on the Snowflake integration *and* an IAM permissions policy on the AWS role. Why both? What does each one protect against that the other doesn't? Give a concrete failure scenario where one layer saves you and the other wouldn't.

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

**The question:**
> Your Snowflake database has four schemas: RAW, STAGING, MARTS, SNAPSHOTS. A junior engineer asks, "Why not just put everything in one schema and use table prefixes like `raw_trips`, `staging_trips`, `marts_trips`?" Defend the four-schema design. Mention at least three concrete advantages — at least one related to security, at least one related to lifecycle/retention.

#### Bryan's answer — 8.5/10 ✓

> Having 4 schemas goes back into the medallion architecture:
> RAW represents the data as-ingested.
> STAGING represents the data that has been cleaned and typed.
> MARTS represents the production-level data that is aggregated and modeled.
> SNAPSHOTS represents a development environment.
> Given that each schema represents the same dataset at a different stage of the data lifecycle, the table suggestion does not work.
> One of the points of the 4 schema system is that it is easier to assign access roles to the schemas. Not everybody needs to be able to access the same data in the same way:
> Analysts, and engineers may both be able to access STAGING, but an Engineer may have write permissions whereas an Analyst may just have read permissions.
> Stakeholders should only have read permissions to query the production-level data.

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

**The question:**
> Walk through what happens at the moment you run `docker compose up -d` from your repo root. Specifically: how does the code in your `airflow/dags/` directory end up executable inside the running container? How does the Postgres metadata DB connect to the Airflow services? What would break if you deleted the `volumes:` block from `docker-compose.yaml`?

#### Bryan's answer — 6.5/10

> From what I understand, when I run docker compose up -d, it searches the directory for the docker-compose.yaml file. docker then runs the apache airflow image using the custom environment, one parameter being AIRFLOW__DATABASE__SQL_ALCHEMY_CONN:postgresql+psycopg2://airflow:airflow@postgres/airflow. This parameter connects airflow to a postgres database running in a docker container. This parameter also provides the username, password, and database that will be accessed. Moving down the docker-compose.yaml file, we can determine that each the 'volumes' section acts more as a bind mount: it connects my host path(s) into the docker container. Continuing down, this appears to be contingent on whether or not the postgres service is healthy. This runs an image of postgres on docker, using the same credentials used to access airflow. Lastly the second 'volumes' section confirms the connection between airflow and the postgres database.

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

**The question:**
> The decisions to put Snowflake and S3 in the same AWS region, set `AUTO_SUSPEND = 60`, and pick `WAREHOUSE_SIZE = XSMALL` are all cost-related. Explain *each* decision in terms of what it specifically prevents. Then describe what would change about each decision if this were a production system serving 100 concurrent analysts instead of one.

#### Bryan's answer — 7.5/10

> Setting AUTO_SUSPEND = 60 is made so the warehouse stops billing after a set number of seconds after the last query was executed, in this case 60. If this is not set, then the warehouse will keep charging the user's account even though no queries are being executed.
> Setting WAREHOUSE_SIZE = XSMALL is due to the relative scale of my project. As each size doubles in cost and compute, setting this parameter to XSMALL prevents oversized compute costs to pile up from having a larger Warehouse size, we are using more than the necessary resources (e.g. compute) in order to complete this task.
> Production Scenario:
> If this were a production system with 100 concurrent analysis attempting to run, we would change the AUTO_SUSPEND to be as short as possible, in order to save on idle compute costs. This is because depending on the resources we need, we would scale up our WAREHOUSE_SIZE = LARGE(+). Using AUTO_SUSPEND and AUTO_RESUME in this instance would help save costs by suspending quickly after executing the last query, and resuming relatively quickly after the next query is queued.

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

**The question:**
> In your Phase 0 setup, list every distinct *identity* (human or service) that exists across both AWS and Snowflake. For each identity, name what it can do and what *grants* or *policies* control that. The point of this question is to force you to enumerate the cast of characters and not conflate them.

#### Bryan's answer — 5.5/10

> Snowflake:
> Roles:
>
> * ELT_ROLE: Can access all of the Medallion architecture. Dedicated role for the ELT pipeline
> * ELT_USER: Dedicated user for the ELT pipeline
>
> * IAM User
>    * Provides credentials that we can insert into the IAM trust policy in order to connect to the Storage Integration.
>    * Can use ListBucket and GetObject.
> * Principal:
>    * AWS: Can send the sts API call AssumeRole in order to take on the IAM role's permissions.
>
> AWS S3 Bucket:
>
> * IAM user nyc-taxi-elt-user
>    * Has read and write permissions, granted by the IAM permissions policy. Can also use ListBucket and GetObject as well as GetBucket, PutObject and DeleteObject.

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

**The question:**
> You schedule a daily Airflow DAG to run `COPY INTO` from your S3 stage at 3 AM. It works for a week, then on day 8 it fails with `Access Denied (403) retrieving information from the bucket`. Nothing in your code or configuration has changed. Walk through your debugging process: what do you check first, second, third, and what's a likely root cause that fits the pattern?

#### Bryan's answer — 7.5/10

> I would first look at CloudTrail in order to determine if the authentication failure is the root cause. It would help determine if any of the following are the issue:
>
> * AssumeRole hands over temporary credentials and they could have expired on the 8th day.
>
> * The IAM permissions/trust policy may have changed due to a data leak, and may be the reason we are having this issue.
>
> I believe a likely root cause would be AssumeRole's credentials expiring, the STS API would have to issue a new set of credentials: temp access key ID, secret access key, and session token.

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

**The question:**
> A colleague clones your `nyc-taxi-elt` repo, runs `docker compose up airflow-init`, and immediately gets an error in the init container before any Airflow code runs. They've installed Docker and have a working internet connection. What's the most likely missing piece, and why would your repo not have caught this in code review?

#### Bryan's answer — 8.5/10 ✓

> My colleague is most likely missing a .env file, it is not tracked by git as it is listed in the .gitignore file, this is why my repo would not have caught this in a code review.
> Not having the .env file means they do not have access to any credentials associated with the project.

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

**The question:**
> You run `LIST @NYC_TAXI.RAW.NYC_TAXI_STAGE/yellow/` in Snowflake and it returns a list of files successfully. Five minutes later, you run the *exact same* query and get an error. Network connectivity is fine. The integration hasn't been edited. What changed, and how would you confirm it without touching AWS?

#### Bryan's answer — 7.5/10

> This may be a quirk of the Snowflake worksheet, as it does not run all queries at once. In this context, there may be some type of role or schema change that was run prior to running  LIST @NYC_TAXI.RAW.NYC_TAXI_STAGE/yellow/. You may be in the wrong role and have the wrong permission, or be in the wrong schema and cannot access that object namespace from where you are.
> If it is a role issue, you can first determine if you have the appropriate role for what you are doing by running SELECT CURRENT_ROLE().

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

**The question:**
> A senior engineer reviews your Phase 0 setup and says: "This is overengineered for a personal project. You don't need a separate IAM role, a storage integration, multiple Snowflake schemas, or RBAC. Just put your AWS keys directly in a stage and use `ACCOUNTADMIN` for everything." Defend your choices. For *each* choice they criticized, explain (a) what concrete risk the simpler version exposes you to, and (b) what skill or interview-relevant signal the proper version demonstrates.

#### Bryan's answer — 8.5/10 ✓

> Separate IAM role: We use an IAM role as it has no long-term credentials, this role can be assumed by a trusted principal and receive temporary credentials. Eliminates the need to hard code credentials anywhere.
> Risk: Using an IAM user, for instance, would be less secure as their credentials do not rotate automatically.
> Storage Integration: We use storage integration because it uses STS's API call AssumeRole in order for a principal to take on the permissions of an IAM role. They receive a temp access key ID, secret access key, and session token. We prefer this way as the keys are temporary and rotate often.
> Risk: If there's AWS keys hardcoded in a stage, a DDL leak could leak these keys in Snowflake's metadata.
> Multiple Snowflake Schemas: We prefer to have the medallion architecture for representing the dataset at different parts of the dev cycle. As such, there should be some users who should have more permissions than others. For instance, data engineers having read/write for most schemas while stakeholders have read privileges for the MART schema, which consists of production-ready, aggregated, modeled data.
> Risk: Not having this architecture and having each schema represented as a single schema gives users access to the full dataset, freely being able to write and change things.
> RBAC: ACCOUNTADMIN should only be used to grant roles to users. We use the RBAC model because even ACCOUNTADMIN cannot access certain things without being given the proper role. Permissions are attached to roles. This goes back to the principle of least privilege, a user who is analyzing data does not need full access, which they would have with the ACCOUNTADMIN role.

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

Below the 8.0 threshold *(threshold in effect at time of original drill on 2026-04-29)*. Re-drill required for the three lowest-scoring questions (Q6, Q4, Q2) before advancing to Phase 1.

> **⚠️ Retroactive re-drill flagged (added 2026-05-07):** Under the elevated 8.5+ standard adopted on 2026-05-07, this drill outcome would require additional consolidation work. Specifically, several questions scored <8.0 individually (Q1: 7.5, Q2: 7.0, Q4: 6.5, Q5: 7.5, Q6: 5.5, Q7: 7.5, Q9: 7.5) and the re-drill itself produced one question (Q-Re-1: 7.5) below the new individual threshold. **Plan: After Phase 5 ships, retroactively re-drill all Phase 0 questions scoring <8.0 with consolidation-first protocol, before Phase 6 portfolio polish.** This avoids derailing forward momentum now while ensuring foundational fluency is locked in before the project goes public.

**Recurring pattern identified across this batch:**

The conceptual understanding is solid — no question revealed a missing concept. The points lost are concentrated in:
1. **Answer completeness** — addressing every part of multi-part questions, not just the part you're most confident on
2. **Vocabulary precision on layered systems** — distinguishing roles vs principals vs identities, integration vs stage, image vs container, etc.
3. **Pushing answers to senior depth** — naming AWS API calls, citing specific Snowflake primitives (multi-cluster warehouses, Time Travel), articulating both directions of a defense-in-depth argument

---

### Phase 0 Re-drill Answers

*Triggered by 7.45/10 average on original drill. Re-drill targets the lowest-scoring originals using fresh scenarios on the same concepts.*

---

#### Q-Re-2 — Docker composition (re-drill of original Q4)

**The question:**
> Your `docker-compose.yaml` includes the line `_PIP_ADDITIONAL_REQUIREMENTS: ${_PIP_ADDITIONAL_REQUIREMENTS:-}` in the airflow-common environment. Walk me through: (a) what this line does, (b) where the value comes from, (c) when in the container lifecycle the packages get installed, and (d) why this approach is dev-only and what the production replacement would be.

##### Bryan's first attempt — 6.5/10

> a. _PIP_ADDITIONAL_REQUIREMENTS installs the included packages whenever a container is started, which is convenient for development.
> b. it comes from the apache/airflow:2.10.3-python3.11 image which is pulled if not already cached.
> c. _PIP_ADDITIONAL_REQUIREMENTS is part of the environment variables, which are injected at runtime.
> d. As mentioned in part a, _PIP_ADDITIONAL_REQUIREMENTS installs every time a container is started, however a production environment would prefer a custom Dockerfile that extends apache/airflow:<version> with python already embedded. This approach is fast and reproducible.

**Key gap:** Part (b) attributed the value to the image (incorrect — image is the consumer, not the source). Parts (a) and (c) imprecise on layering. Triggered a consolidation session before re-attempt.

##### Bryan's re-attempt — 8.5/10 ✓

> a. This line is a shell variable that is substituted by our current environment's variable in the .env file once docker compose loads up the .yaml file.
> b. This value comes from the .env file which is loaded up by docker compose. It is then substituted into the .yaml file during compose-load time.
> c. The packages get passed on container-load time, and the pip install actually occurs on container-boot time.
> d. This approach is dev only as the pip install occurs during container-boot time via airflow's entry point script. A production approach would include adding a custom Dockerfile with Python already baked in, ensuring reproducibility.

| Dimension | Score | Why |
|---|---|---|
| Technical Accuracy | 9/10 | All four parts correct in substance. One small carryover — "Python baked in" should be "additional packages baked in"; Python is in the base image. |
| Conceptual Depth | 8/10 | Layer-naming crisp throughout; substantial improvement over original |
| Vocabulary Precision | 9/10 | "Compose-load time," "container-boot time," "shell variable substitution" — all used correctly |
| Trade-off Awareness | 8/10 | Production replacement named with right reasoning |

**Improvement vs first attempt: 6.5 → 8.5 (+2.0).** Major correction on (b), precision gain on (c), tighter reasoning chain on (d). Triggered by self-directed consolidation session that explicitly mapped the six-layer config cascade.

##### Model answer (9/10)

The line is a **YAML key-value pair** that declares an environment variable for the container, with the value populated via shell-style substitution from the host environment.

(a) **What the line does:** Sets `_PIP_ADDITIONAL_REQUIREMENTS` as an env var inside the future container. The right-hand side `${_PIP_ADDITIONAL_REQUIREMENTS:-}` uses shell-style parameter expansion: take the host's value, or default to empty string if unset.

(b) **Where the value comes from:** Compose auto-loads `.env` from the directory you ran `docker compose up` in (Compose convention, not shell). If `.env` defines `_PIP_ADDITIONAL_REQUIREMENTS=...`, that value is what Compose substitutes. If `.env` is missing or doesn't define it, the `:-` provides an empty-string default. The image is *not* the source — it's the consumer.

(c) **When in the lifecycle:** Three distinct moments:
1. **Compose-load time:** YAML is read; `${VAR:-}` substitution resolves against host environment
2. **Container-create time:** resolved env var attached to the container
3. **Container-boot time:** Airflow's entrypoint script (`airflow-entrypoint.sh`) reads the env var and runs `pip install` on every boot

The boot-time install is what makes this slow on every restart.

(d) **Why dev-only and the production replacement:** Boot-time install means every restart re-downloads and re-installs. Slow, fragile (network/dependency resolution can fail), and not reproducible across machines. Production replacement is a **custom Dockerfile**:

```dockerfile
FROM apache/airflow:2.10.3-python3.11
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
```

Packages bake into a new image layer at *build time*. Container starts skip the install entirely.

##### Key lessons

1. **Configuration cascades through layers.** When tracing where a value "comes from," walk the chain backward: consumer → tool → file. Each layer reads from the previous.
2. **`.env` is a Compose convention, not a shell convention.** `echo $VAR` in your shell can't see what Compose can see. Different processes read from different places.
3. **Three timing moments matter:** compose-load, container-create, container-boot. Naming them precisely makes the dev-only nature obvious — boot-time work runs every restart.
4. **Production-grade Docker bakes config at build time.** Runtime config is for *behavioral* settings; package installs belong in the image itself.

---

#### Q-Re-3 — Defense-in-depth (re-drill of original Q2)

**The question:**
> Your local `.env` file contains AWS access keys for the `nyc-taxi-elt-user` IAM user. The `.env` is gitignored and stays on your laptop. Despite this, your repo also enforces a permissions policy on the `nyc-taxi-elt-user` IAM user that scopes it to the single bucket. **Why both?** What does the `.env` gitignore protect against that the IAM permissions policy doesn't, and vice versa? Give a concrete failure scenario for each.

##### Bryan's answer — 8.0/10 ✓

> The .env file being gitignored protects against confidential Access Keys from leaking onto a public repository. If these keys were to leak, the IAM user could become compromised, as their credentials do not rotate automatically.
> The IAM permissions policy protects a compromised IAM user from gaining access to all buckets the role can access. With the permissions policy in place, S3 will deny any requests for bucket access outside of the given scope.

| Dimension | Score | Why |
|---|---|---|
| Technical Accuracy | 9/10 | Both directions of defense-in-depth correctly identified |
| Conceptual Depth | 8/10 | Bidirectional reasoning is now there; depth could go further on the *failure mode each defense allows* |
| Vocabulary Precision | 8/10 | "IAM permissions policy," "credentials do not rotate," "scope" all used correctly |
| Trade-off Awareness | 7/10 | Implicit understanding of layered defense; could explicitly name the threat surface |

**Improvement vs original Q2: 7.0 → 8.0 (+1.0).** Crucial gap closed: original Q2 answered defense-in-depth in only one direction; Q-Re-3 articulates both directions cleanly with a concrete failure consequence on each side.

##### Model answer (9/10)

The two layers protect against compromise in **opposite directions**:

- **Gitignore (host-side / VCS layer):** prevents the credentials from ever leaving the laptop. Threat scenario: I commit in a hurry without running `git status`. If `.env` weren't gitignored, the file is staged and pushed. Within minutes, GitHub's credential-scanning bots find the keys and exfiltrate them. *The IAM policy can't help here — the keys are real, the role is real; the only defense was preventing the file from entering version control.*

- **IAM permissions policy (cloud-side / authorization layer):** limits blast radius when keys *do* leak (via any vector — disk theft, shoulder-surfing, malware on the laptop, leaked screen recording, social engineering). Threat scenario: I lose my laptop. Someone extracts `.env` from the disk and authenticates as `nyc-taxi-elt-user`. They run `aws s3 ls` to enumerate buckets — but every bucket outside `nyc-taxi-elt-<id>/` returns `AccessDenied` because IAM evaluates the policy and rejects the request. *The gitignore can't help here — the keys leaked outside Git entirely.*

The two defenses cover **different threat vectors**: gitignore stops VCS-shaped leaks, the IAM policy contains the damage from any leak that does happen. Together they're defense in depth; either alone leaves a class of incident exposed.

##### Key lessons

1. **Bidirectional reasoning generalizes across layer pairs.** Q2 tested with `STORAGE_ALLOWED_LOCATIONS` + IAM; Q-Re-3 tested with `gitignore` + IAM. Same argument shape, different specifics. The pattern transferred — that's the real signal.
2. **Concrete failure scenarios beat abstract descriptions.** "What does the defense protect against" is a 7/10 answer; "imagine X happens — here's where defense Y kicks in and here's why defense Z couldn't help" is a 9/10 answer.
3. **Tiny mechanism nitpick:** the deny on an IAM policy violation is technically issued by IAM's policy evaluation engine, not S3. Common shorthand to say "S3 denies it," but in interviews with senior IAM-aware folks, "IAM evaluates and denies" is the more accurate phrasing.

---

#### Q-Re-1 — Identity enumeration (re-drill of original Q6)

**The question:**
> Imagine you've added a Phase 2 ingestion script that runs *inside* the Airflow container, reads from S3, and writes to Snowflake. Enumerate every distinct identity (human or service) involved in *just one execution* of that script — from the moment Airflow triggers it to the moment data lands in Snowflake. For each identity, name what authenticates it and what authorizes its actions. (At least 6 identities involved; full credit for naming all of them precisely.)

##### Bryan's answer — 7.5/10 ✓ (consolidated through guided dialogue)

**Original answer as submitted:**

> Airflow:
> - DAG scheduler - authenticated via healthy postgres state
> - Airflow container - granted access to .env via docker compose
>
> Snowflake End:
> - Human User, granted `ACCOUNTADMIN` AND `ELT_ROLE`
> - ELT_USER, granted ELT_ROLE
> - ACCOUNTADMIN: automatically given
> - ELT_ROLE: granted usage on WH_ELT, ALL on NYC_TAXI schemas, USAGE on integration
>
> AWS:
> - Human user, used for setup
> - nyc-taxi-elt-user: has access keys in ./aws/credentials; inline policy scoped to bucket
> - Snowflake's IAM user: the principal that calls AssumeRole

**Consolidated answer after Socratic walk-through:**

The original answer mixed *system cast* (identities that exist and built the system) with *runtime cast* (identities that act during the 3 AM execution). Through guided questioning, the runtime cast was clarified as:

**Airflow side (orchestration layer):**
1. **`airflow-scheduler` process** — decides when to fire the DAG, spawns the task subprocess (in LocalExecutor setup, scheduler also executes tasks)
2. **The Python subprocess** — runs the ingestion code, inherits env vars from the container

**Outbound authentications from the script:**
3. **`nyc-taxi-elt-user`** (IAM user) — when boto3 calls S3
   - Authenticated via: long-lived access keys from `.env` → environment variables (boto3 credential chain)
   - Authorized via: inline IAM permissions policy scoped to the bucket
4. **`ELT_USER`** (Snowflake user, operating as `ELT_ROLE`) — when the script connects to Snowflake
   - Authenticated via: password from `.env` → environment variables
   - Authorized via: `ELT_ROLE` granted to the user; role has USAGE on warehouse/database/schemas

**Cross-cloud authentication triggered by COPY INTO:**
5. **Snowflake's IAM user** (managed by Snowflake) — calls `sts:AssumeRole` with ExternalId
   - Authorized to assume via: trust policy on `snowflake-s3-role` matching Principal + ExternalId
6. **`snowflake-s3-role`** (IAM role in your AWS account) — assumed identity
   - Authenticated via: temporary credentials issued by STS (~1 hour TTL)
   - Authorized via: permissions policy on the role allowing `s3:ListBucket`, `s3:GetObject` on the bucket

**Dropped from original answer (system cast, not runtime cast):**
- Human Snowflake user — built the system; not logged in at 3 AM
- ACCOUNTADMIN — used for setup; not assumed during automated runs
- AWS root/human user — used for setup; not acting at runtime

| Dimension | Score | Why |
|---|---|---|
| Technical Accuracy | 8/10 | All 6 runtime identities clearly identified after walk-through |
| Conceptual Depth | 7/10 | The system-vs-runtime distinction needed Socratic scaffolding to surface, but is now explicit |
| Vocabulary Precision | 7/10 | "Authenticated via healthy postgres state" was imprecise initially; clarified through dialogue |
| Trade-off Awareness | 8/10 | The architectural insight on AssumeRole (Snowflake never has to be a credential keystore for thousands of customers) went genuinely deeper than the original Q6 ever explored |

**Improvement vs original Q6: 5.5 → 7.5 (+2.0).** The system-cast vs runtime-cast distinction is the key concept that surfaced. Score reflects that the consolidated answer is genuinely there but required guided walking — meaning the model needs more time to fully internalize before being interview-reflexive.

##### Model answer (9/10)

The runtime cast for *one execution* of an automated 3 AM Airflow-triggered ingestion script is **6 identities** (reasonably 5–7 depending on how you count the scheduler+subprocess and the user+role pairings):

**Orchestration:**
- `airflow-scheduler` process — fires the DAG on schedule; in LocalExecutor it also spawns the task subprocess. Talks to Postgres metadata DB via internal connection; connects to external services only by passing env vars to subprocesses.
- Python subprocess — inherits env vars from the container; runs the ingestion logic.

**Script's outbound authentications:**
- `nyc-taxi-elt-user` IAM user — boto3 finds access keys via the credential chain (env vars from `.env` → forwarded by Compose → inherited by subprocess). Authorized by an inline permissions policy scoped to one bucket.
- `ELT_USER` Snowflake user — `snowflake-connector-python` reads username/password from env. Authenticates via password; once connected, operates with `ELT_ROLE` grants (USAGE on warehouse, ALL on schemas).

**Cross-cloud (COPY INTO triggers):**
- Snowflake's IAM user (in Snowflake's AWS account, exposed via `STORAGE_AWS_IAM_USER_ARN`) — calls `sts:AssumeRole` on `snowflake-s3-role` with ExternalId. Authorized by the trust policy on `snowflake-s3-role`.
- `snowflake-s3-role` IAM role — assumed identity. Authenticated via STS-issued temporary credentials (Access Key ID, Secret Access Key, Session Token, ~1 hour TTL). Authorized via permissions policy on the role granting `s3:ListBucket` + `s3:GetObject` on the bucket.

**The distinction that matters:** The runtime cast excludes anything that only acted during system setup. ACCOUNTADMIN, the human Snowflake user, and the AWS root/admin user all built the system but don't authenticate during automated execution. Listing them in a runtime-cast question is a category error.

##### Key lessons

1. **System cast vs runtime cast.** Identities that exist in your system are not the same as identities that authenticate during a specific execution. When asked "who acts during X," apply the filter: at the moment X happens, is this identity actually authenticating to anything?
2. **Credential cascades determine identity.** The same boto3/snowflake-connector code executed in different environments authenticates as different identities — depending on what's in the env vars at the moment of the call. The cascade pattern from Q-Re-2 directly determines *who* authenticates here.
3. **AssumeRole as architectural risk transfer.** AssumeRole isn't just about token expiration — it's about Snowflake never having to *store* customer credentials at all. With long-lived keys, Snowflake would carry the breach risk for thousands of customers' AWS accounts. With AssumeRole, Snowflake stores zero customer credentials; a breach yields nothing useful. This is the architectural insight, not just a technical convenience.
4. **`.env` cascades through six layers to determine runtime identity:** `.env` file → Compose load → YAML substitution → container env → Python subprocess inherits → boto3/snowflake-connector reads. Each layer's job is forwarding; the *value* of who-authenticates-as-what is set at the .env layer.

---

## Phase 1 — Data Source & Exploration

*Drill date: 2026-05-07 — Final average: 6.85/10 (below threshold; re-drill required for Q9, Q10, Q6). Drill conducted under transition: original 8.0 threshold initially in force, elevated to 8.5+ AND zero sub-8.0 mid-drill. Per the new standard, several additional questions (Q1: 7.0, Q4: 7.0, Q5: 7.5, Q7: 7.5, Q8: 6.5) also fall below the individual 8.0 threshold and would require consolidation if encountered fresh today. The Q-Re-1/2/3 re-drill targets the three lowest (Q9, Q10, Q6) as the priority; depth on the others will be revisited via spaced-repetition rerun cadence.*

### Q1 — Grain & Its Consequences

**The question:**
> Your fact table `fct_shipments` has columns: `shipment_id`, `customer_id`, `origin_warehouse_id`, `destination_address_id`, `carrier_id`, `weight_lbs`, `total_cost`, `shipped_at`, `delivered_at`. State the grain in one sentence. Then describe **two analytical questions this grain supports** and **two analytical questions it does NOT support** (and what grain you would need for those). Be specific about why.

#### Bryan's answer — 7.0/10

> Q1: One row of this table represents shipping information, specifically packages that are originally stored at warehouses then shipped delivered to customers via some carrier.
> Two questions this grain supports:
> * What is the average weight of packages shipped from origin_warehouse_id = 10201?
> * What is the most expensive package delivered by carrier xyz?
> Two Questions this grain does not support:
> * What is the fastest time a package has been delivered from order to delivery? (requires an ordered_at column with timestamps containing the order times)
> * How many stops does a package make before being delivered? (requires dataset to keep track of each stop on a package's route to the customer)

| Dimension | Score | Why |
|---|---|---|
| Technical Accuracy | 7/10 | Grain idea correct in spirit but stated imprecisely; supported/unsupported splits reasonable |
| Conceptual Depth | 7/10 | Identified the right shape; missed precise grain articulation |
| Vocabulary Precision | 6/10 | "Shipping information" is descriptive, not precise. Grain statements need to name *exactly what one row represents* |
| Trade-off Awareness | 8/10 | Both unsupported-question explanations correctly identify what attribute or grain shift would be needed |

#### Model answer (9/10)

The grain of `fct_shipments` is: **one row per shipment**.

A shipment is one event of one package being sent on one journey to one destination via one carrier. The single-noun precision ("one row per X") is what distinguishes a grain statement from a domain description.

Supported questions (existing grain works, just aggregate):
- Average weight from origin_warehouse_id = 10201 — single WHERE + AVG
- Most expensive package delivered by carrier xyz — single WHERE + ORDER BY total_cost DESC LIMIT 1

Unsupported questions, with the distinction worth naming:
- "Fastest time from order to delivery" — *attribute availability* problem. Same grain (per shipment), but needs an additional `ordered_at` column. The fact table just needs an additional attribute.
- "How many stops before delivery?" — *grain* problem. Requires a finer grain: `fct_shipment_stops` at "one row per (shipment, stop)" grain. This is structurally a different fact table.

The senior insight: distinguish *attribute availability* problems (same grain, missing column) from *grain* problems (need a different fact table). Different engineering responses.

#### Key lessons

1. **Grain statements are single-noun precise.** "One row per shipment" not "shipping information."
2. **Two categories of unanswerable.** Attribute-availability problems vs grain problems require fundamentally different fixes.
3. **Senior signal:** explicitly naming which category each unanswerable question falls into demonstrates depth most engineers don't articulate.

---

### Q2 — Dimension Classification

**The question:**
> A teammate is designing a fact table for an e-commerce orders dataset and shows you these source columns: `order_id`, `customer_id`, `product_id`, `coupon_code` (string, ~50 distinct values like "SUMMER10"), `discount_amount` (decimal), `is_gift` (boolean), `order_status` (string: "pending"/"shipped"/"delivered"/"cancelled"), `device_type` (string: "mobile"/"desktop"/"tablet"). For each non-PK column, classify it as: dimension table / degenerate dimension / pure measure. Justify each classification using the Richness Test.

#### Bryan's answer — 8.0/10 ✓

> Q2:
> * customer_id: dimension
>    * cardinality can become larger than 5 with a moderate user base
>    * this set will become larger as the e-commerce site grows.
>    * You would want to attach descriptive attributes, such as full name and other personal information.
> * product_id: dimension
>    * cardinality is can definitely be larger than 5
>    * this set will become larger as the e-commerce site adds new products to their catalog
>    * You would want to attach attributes such as product name, stock, cost of goods, etc.
> * coupon_code: degenerate
>    * cardinality is already larger than 5 with ~50 codes
>    * this set would not need to grow, company can simply rotate coupon codes out.
>    * There are no descriptive attributes you would want to add to these codes besides maybe their discount values. But most companies attach those directly to the code name itself.
> * discount_amount: pure metric
>    * can't be represented by cardinality as it is a continuous value
>    * not part of a set
>    * no descriptive attributes that would be worth adding.
> * is_gift: degenerate
>    * cardinality is 2
>    * set is non-growing as it is represented by a boolean.
>    * no descriptive attributed are needed.
> * order_status: degenerate
>    * cardinality is 4
>    * set does not increase as it is a static list of order statuses.
>    * there are no extra descriptive attributes that are worth adding. The status itself is the description.
> * device_type: degenerate
>    * cardinality is 3
>    * set is very likely not to increase
>    * there are no extra attributes anyone would be interested in.

| Dimension | Score | Why |
|---|---|---|
| Technical Accuracy | 8/10 | 5 of 7 correct outright; 2 mis-classified but with reasonable thinking |
| Conceptual Depth | 8/10 | Applied all three Richness Test criteria explicitly to each column |
| Vocabulary Precision | 9/10 | Crisp use of "cardinality," "degenerate," "pure measure" |
| Trade-off Awareness | 7/10 | Solid reasoning, but missed why coupon_code is borderline interesting |

#### Model answer (9/10)

| Column | Classification | Justification |
|---|---|---|
| customer_id | Dimension | High cardinality, growing, rich attributes (name, segment, contact info) |
| product_id | Dimension | High cardinality, growing, rich attributes (name, price, category) |
| coupon_code | **Dimension** | ~50 values, churns over time (new campaigns added/expired), and rich attributes worth attaching: discount_pct, min_order_value, valid_from/valid_to, campaign_name. An analyst asking "what was 2024's summer campaign ROI?" wants to JOIN to dim_coupon and filter campaign_name |
| discount_amount | Pure measure | Continuous numeric, aggregated |
| is_gift | Degenerate | Cardinality 2, no plausible attributes worth attaching |
| order_status | Degenerate (defensible) | 4 values; some warehouses build dim_order_status for richness like is_terminal_state, is_revenue_recognized |
| device_type | Degenerate | 3 stable values, no plausible richness |

The two under-classifications (coupon_code, arguably order_status) reveal the same pattern from Phase 1 conversation around VendorID and RatecodeID: weighting cardinality more than the richness test.

The shortcut question worth memorizing: *"Would a business analyst writing a report ever want to JOIN to this column for richer text or attributes?"* For coupon_code: yes (campaigns, validity windows, discount mechanics). For is_gift: no.

#### Key lessons

1. **Apply all three Richness Tests, not just cardinality.** The richness criterion catches dimensions that low cardinality alone would miss.
2. **The shortcut question** ("would an analyst want to JOIN for richer text?") is faster than the formal three-test walk for borderline cases.

---

### Q3 — SCD Type Reasoning

**The question:**
> For an analytical warehouse tracking historical product sales, you have three dimensions:
> - `dim_product` — products are renamed occasionally (e.g., "iPhone 14 Pro" → "iPhone 14 Pro Max"); we want historical reports to show what the product was called at the time of sale
> - `dim_category` — broad categories like "Electronics", "Apparel", "Home Goods" — categories rarely change, but a typo correction in 2024 changed "Apparrel" to "Apparel"
> - `dim_currency` — `currency_code`, `currency_name`, `symbol` — currency codes are stable; descriptions are stable
>
> Assign an SCD type (0/1/2/3) to each dimension and explain your reasoning. **Address all three dimensions explicitly.**

#### Bryan's answer — 8.5/10 ✓

> Q3:
> * dim_product: SCD type 2 as we want to preserve the historical product names at time of sale.
> * dim_category: SCD 1 as we don't need to preserve historical category names, such as the typo. We would rather overwrite it.
> * dim_currency: SCD type 0 as currency codes and their descriptions are stable.

| Dimension | Score | Why |
|---|---|---|
| Technical Accuracy | 9/10 | All three classifications correct |
| Conceptual Depth | 8/10 | Right reasoning, but compressed — could go further on *why* each fits |
| Vocabulary Precision | 9/10 | "Preserve historical product names at time of sale," "stable" — all tight terms |
| Trade-off Awareness | 8/10 | Implicit; could be stronger by naming what each choice trades off |

#### Model answer (9/10)

- **dim_product → SCD Type 2.** Historical reports need product names *at time of sale*. Each product version gets its own row with valid_from/valid_to. **Requires surrogate keys** because product_id appears in multiple rows.
- **dim_category → SCD Type 1.** The typo correction "Apparrel" → "Apparel" is *cosmetic*, not a meaning change. The category itself didn't change; only the label was fixed. Type 2 would be misleading (analysts would see two "Apparel" entries with no semantic distinction).
- **dim_currency → SCD Type 0.** ISO 4217 currency codes are explicitly designed to be immutable. Adding new currencies via INSERT is fine; modifying existing ones is the prohibited operation. Type 0 captures this cleanly.

The principle: **SCD type addresses changes to existing rows, not additions of new rows.**

#### Key lessons

1. **Connect SCD choice to schema implication.** Type 2 → surrogate keys required. Type 1 → no validity windows. Type 0 → no change-tracking machinery.
2. **Type vs adds.** "We add new categories sometimes" is not an SCD operation — it's just INSERT.

---

### Q4 — Role-Playing Dimensions

**The question:**
> Explain (a) what a role-playing dimension is, (b) why our project uses one for `dim_location` and `dim_date`, and (c) write the SQL skeleton (no need for a complete query — just JOINs and aliases) showing how you'd query "for each pickup borough, what's the average trip duration grouped by pickup day-of-week?" using the role-playing dimensions correctly.

#### Bryan's answer — 7.0/10

> Q4:
> a. A role-playing dimension is a dimension table that is referenced more than once by a fact table.
> b. Our project uses one for dim_location as it is referenced by PULocationID and DOLocationID in the fact table, while dim_date is referenced by tpep_pickup_datetime and tpep_dropoff_datetime in the fact table.
> c.
> SELECT pu, pud, AVG(tpep_pickup_datetime - tpep_dropoff_datetime) as avg_trip_duration
> FROM fct_trips f
> JOIN dim_location pu ON f.PULocationID = pu.location_id
> JOIN dim_location do ON f.DOLocationID = do.location_id
> JOIN dim_date pud ON f.pickup_date_key = pud.date_key
> JOIN dim_date dod ON f.dropoff_date_key = dod.date_key
> GROUP BY pu, pud

| Dimension | Score | Why |
|---|---|---|
| Technical Accuracy | 6/10 | Concept right; SQL has 4 specific bugs that would prevent it from running |
| Conceptual Depth | 8/10 | (b) correctly identifies both role-playing dimensions in our schema |
| Vocabulary Precision | 7/10 | "Referenced more than once" missing the "different semantic role" nuance |
| Trade-off Awareness | 7/10 | Implicit understanding shown via correct schema usage |

#### Model answer (9/10)

(a) A role-playing dimension is a single physical dimension table referenced multiple times by one fact table, where each reference plays a different semantic role (e.g., pickup vs dropoff, order vs ship vs delivery date). Storing one physical table avoids data duplication; SQL aliases disambiguate roles at query time.

(b) `dim_location` is role-playing because `fct_trips` references it twice via `pickup_location_sk` and `dropoff_location_sk` (both surrogate-key foreign keys). `dim_date` is role-playing because `fct_trips` references it twice via `pickup_date_key` and `dropoff_date_key` (both INT YYYYMMDD foreign keys). Note: `tpep_pickup_datetime` and `tpep_dropoff_datetime` are TIMESTAMP columns preserved in the fact for sub-day precision; they don't participate in the dim_date join.

(c) Correct SQL skeleton:
```sql
SELECT
    pu.borough              AS pickup_borough,
    pud.day_name            AS pickup_day_of_week,
    AVG(DATEDIFF('minute', f.tpep_pickup_datetime, f.tpep_dropoff_datetime))
        AS avg_trip_minutes
FROM fct_trips f
JOIN dim_location pu  ON f.pickup_location_sk = pu.location_sk
JOIN dim_date     pud ON f.pickup_date_key    = pud.date_key
GROUP BY pu.borough, pud.day_name
```

Four bugs in the original answer:
1. **SELECT/GROUP BY use table aliases as if they were columns.** `SELECT pu` should be `SELECT pu.borough`.
2. **Joined on natural key instead of surrogate key.** `f.PULocationID = pu.location_id` would produce one-to-many joins on a Type 2 dimension. Should be `f.pickup_location_sk = pu.location_sk`.
3. **Trip duration math is backwards and unitless.** `pickup - dropoff` returns a negative interval. Should be `DATEDIFF('minute', pickup, dropoff)` for clarity and correct sign.
4. **Grouped by table alias instead of attribute.** "Day of week" requires `pud.day_name`, not the entire `pud` table.

#### Key lessons

1. **Concept solid, execution buggy.** The four SQL bugs are practical-skill gaps, not concept gaps.
2. **Phase 3 (dbt) will be the proving ground** for star-schema query writing.
3. **The four bug categories** (alias-as-column, natural-vs-surrogate join, interval-arithmetic precision, group-by-attribute vs group-by-table) are recurring senior-level SQL hazards.

---

### Q5 — Star vs Snowflake (Comparison)

**The question:**
> A senior engineer reviews your `dim_location` design and proposes normalizing it into three tables: `dim_location` (location_id, zone, borough_id, service_zone_id), `dim_borough` (borough_id, borough_name), `dim_service_zone` (service_zone_id, service_zone_name). Defend your choice to keep `dim_location` flat. Address: (a) what shape this proposal would create, (b) historically why this normalized shape existed, (c) why modern columnar warehouses make it less compelling, and (d) the specific cost-benefit for our 260-row dimension.

#### Bryan's answer — 7.5/10

> a. the overall shape would resemble a snowflake, requiring multiple joins in order to access the same breadth of information as our flat dim_location table.
> b. this shape used to exist historically in order to save storage, however today this is less of an issue with larger amounts of storage becoming more widely available due to various compression methods.
> c. modern columnar warehouses make this less compelling as columnar compression mitigates the issue of storage. This is also why production warehouses opt to use parquet files.
> d. Keeping our dimension table flat reduces the amount of joins we have to make, which is an analytical benefit.

| Dimension | Score | Why |
|---|---|---|
| Technical Accuracy | 8/10 | All four parts addressed correctly in spirit |
| Conceptual Depth | 7/10 | Surface-level on (b) and (d) — could go deeper on the *why* |
| Vocabulary Precision | 7/10 | "Resemble a snowflake" is informal; could name the design pattern explicitly |
| Trade-off Awareness | 7/10 | Identified the trade-off but didn't quantify it for our specific case |

#### Model answer (9/10)

(a) The proposal creates a **snowflake schema** — `dim_location` no longer holds borough/service_zone names directly; analysts traverse two additional joins (`dim_location` → `dim_borough`, `dim_location` → `dim_service_zone`) to access those attributes. This is *normalization depth*, breaking dimension attributes across multiple tables.

(b) Snowflake schemas were the historical default in the OLTP-influenced era when storage was costly (~$1000/GB in 1995) AND mechanical disk seek time was the dominant query cost. Normalizing eliminated redundancy that would otherwise multiply storage cost and slow disk-bound queries. The pattern carried into early data warehousing because OLTP database engines (Oracle, SQL Server) were the dominant warehouse backends.

(c) Modern columnar warehouses (Snowflake, BigQuery, Redshift) compress repeated dimension values via dictionary encoding — "Manhattan" stored 10M times costs nearly the same as stored once. Combined with cheap cloud storage, the historical case for snowflake schemas evaporates. Star schemas now win on query simplicity (one join per dimension) and analyst friendliness (flat dimensions are immediately readable).

(d) For our specific case: `dim_location` has ~260 zones, ~5 boroughs, ~3 service zones. Storage savings from normalizing would be measured in kilobytes. Meanwhile, every analyst query filtering by borough or service zone would gain *two extra joins* — measurable query latency and notable cognitive overhead. Cost-benefit is asymmetric: trivial savings, real overhead. Star is the unambiguous win.

#### Key lessons

1. **Depth-per-part matters.** Each sub-part deserves *mechanism + consequence*, not just conclusion.
2. **Quantify when scale is invoked.** "260-row dimension" is an invitation to do the math, not just gesture at the principle.
3. **Historical context demonstrates depth.** Naming the OLTP-influenced era and disk-seek economics shows you understand *why* designs evolved.

---

### Q6 — Schema vs Semantics Stability

**The question:**
> You're hired to analyze a 10-year dataset of online ad impressions for a question about engagement trends. The schema is identical across all 10 years (good news!). Walk through your investigation plan to validate that the *semantics* are also stable across the period. Specifically: (a) what would you query, (b) what would you look for, and (c) name two distinct categories of semantic drift that schema-level inspection would miss.

#### Bryan's answer — 6.0/10

> a. I would SELECT all values and group them by column.  SELECT year, COUNT(*) FROM table GROUP BY year.
> b. I would look for years where the column displays NULL or 0 values.
> c. 2 examples of semantic drift that schema-level inspection would miss:
> * querying the distributions of the data across long periods of time. e.g. part a.
> * records that exist in the dataset but are flagged as inactive.

| Dimension | Score | Why |
|---|---|---|
| Technical Accuracy | 6/10 | (a) and (b) too thin to constitute an investigation plan; (c) names two examples but with weak categorization |
| Conceptual Depth | 5/10 | The mental model wasn't fully reached for — "first thing that came to mind" rather than "applied framework" |
| Vocabulary Precision | 7/10 | Reasonable terminology; "semantic drift" used correctly |
| Trade-off Awareness | 6/10 | Implicit understanding present; not articulated |

#### Model answer (9/10)

(a) **Investigation queries** — for each suspect column (categorical/enum, ID columns, boolean flags, timestamps), query value distributions per year:
```sql
SELECT year, <column>, COUNT(*) AS row_count
FROM table
GROUP BY year, <column>
ORDER BY year, row_count DESC;
```

(b) **What to look for:**
- NULL-prevalence shifts (column unpopulated until policy launch)
- Value distribution shifts (categorical values appearing/disappearing year-over-year)
- Taxonomy expansion (e.g., "social" → "social_organic" + "social_paid")
- Numerical scale changes (cost in cents vs dollars across migration)
- Encoding/timezone changes
- Definition shifts (what counts as an "impression" gets tightened)

(c) **Three categories of semantic drift schema inspection misses:**

1. **Policy-driven population gaps** — column exists from day 1 but only populated after a policy/feature launch (NYC's `congestion_surcharge` is the canonical example: schema has it from 2015, but every value is NULL until 2019)
2. **Taxonomy/category evolution** — values within a categorical column expand, contract, or rename over time
3. **Definition shifts** — what a value *means* changes even though the value itself stays consistent (e.g., "ad impression" gets a stricter viewability definition)
4. **Soft-delete / activation state changes** — rows persist but their meaning shifts via flags
5. **Unit/encoding changes** — same column, different unit (cents→dollars, local→UTC)

#### Key lessons

1. **Open-book leverage.** When a question explicitly hints at a mental model by name (here: Schema vs Semantics Stability), consult the doc before answering. The depth of those entries is exactly what produces 9/10 answers.
2. **"Categories of drift" means categories, not examples.** Naming the *type* of drift (taxonomy, scale, definition) demonstrates internalized framework; naming an example only demonstrates exposure.

---

### Q7 — Type Drift Pipeline Decision

**The question:**
> You're loading historical NYC TLC data: 2013 (column type INTEGER), 2018 (DOUBLE), 2024 (BIGINT) for a column `trip_count`. Three approaches are proposed:
>
> 1. Cast everything to BIGINT in Python before loading
> 2. Land raw types in `RAW`, cast in `STAGING` with `TRY_CAST` to BIGINT
> 3. Use schema-evolution machinery (e.g., dbt-snowflake Iceberg tables) to handle evolution automatically
>
> Recommend one approach and explain why it's better than each of the other two for this specific scenario. Include one concrete failure mode each rejected approach would create.

#### Bryan's answer — 7.5/10

> Q7: I believe landing raw types in RAW and casting in STAGING with TRY_CAST would be the best decision in this case.
> Why is this choice better than:
> * casting to BIGINT in Python before loading: the datatype in 2018 is DOUBLE, explicitly casting without first checking could potentially lead to information loss, which could skew findings when someone analyzes this data. Would require a query to determine if fractional values exist.
> * using schema-evolution machinery: this is historical data, so dealing with schema-evolution machinery is unnecessary as we will not have to deal with adding/dropping columns.

| Dimension | Score | Why |
|---|---|---|
| Technical Accuracy | 8/10 | Recommendation correct; both rejections technically sound |
| Conceptual Depth | 7/10 | Rejection 1 has good depth; rejection 2 too compressed |
| Vocabulary Precision | 8/10 | "Information loss," "fractional values" used correctly |
| Trade-off Awareness | 7/10 | The *positive* case for option 2 wasn't fully articulated |

#### Model answer (9/10)

**Recommendation: Option 2 (TRY_CAST in STAGING).** Three positive reasons:
1. **Failed casts become observable** as NULLs rather than blocking the load
2. **Cast logic lives in version-controlled SQL** (dbt models) — testable, reviewable, easy to evolve
3. **The "land raw, transform later" pattern preserves the original** — wrong assumptions can be re-applied without re-ingesting

**Rejection of Option 1 (Python pre-cast):** Casting DOUBLE → BIGINT in Python silently truncates fractional values. If 2018 has `passenger_count = 6.5` rows (rare data quality issue), Python's `int()` writes 6 with no error or warning. The data quality issue is *hidden, not just unhandled*. Option 2 lands 6.5 in RAW, becomes NULL after TRY_CAST, and **is visible** as a data quality problem. Trade: simplicity for observability — wrong direction.

**Rejection of Option 3 (schema-evolution machinery):** Iceberg/Delta adds operational complexity (partitioning strategies, time-travel config, schema-versioning policies) only justified when columns are *added or removed*. Our investigation confirmed type drift only, no column changes. Concrete failure mode: **opportunity cost / over-engineering** — engineering time spent configuring evolution machinery is time not spent on actual ingestion logic, dbt tests, or business value. Onboarding new engineers also gets harder.

#### Key lessons

1. **Defend rejected options with concrete failure modes**, not just verdicts. "Unnecessary" is a verdict; "over-engineering with X concrete cost" is a diagnosis.
2. **Python pre-cast trades observability for simplicity.** That trade is wrong-directional in any data engineering context where data quality matters.
3. **Senior signal:** knowing when *not* to reach for fancy infrastructure is itself a skill.

---

### Q8 — Surrogate Key Failure Mode

**The question:**
> Your colleague is implementing the SCD Type 2 logic for `dim_location` and decides to skip surrogate keys to "keep it simple" — using `location_id` directly as the primary key. They argue: "We have a `valid_from`/`valid_to` window, so we can always identify the right row by joining on `location_id` AND a date range comparison." Walk through what specifically goes wrong with this approach. Include both a correctness failure and a performance failure.

#### Bryan's answer — 6.5/10

> Q8:
> the biggest issue with this approach is using the natural key as their primary key. When the location_id from the fact table JOINs with the location_id on the dimension table, it creates a Cartesian multiplication that will duplicate a fact row per dimension version of that product, which is not the sought after result. In the extreme case: say we have n dimension versions of the product, conducting a cartesian multiplication with a dataset that large will not only be incorrect, but it will be incredibly slow.

| Dimension | Score | Why |
|---|---|---|
| Technical Accuracy | 7/10 | Core concept right (one-to-many multiplication); two minor inaccuracies in framing |
| Conceptual Depth | 6/10 | One unified failure described well, but question asked for **two distinct categories** |
| Vocabulary Precision | 7/10 | "Cartesian multiplication" is correct technically but slightly imprecise here |
| Trade-off Awareness | 6/10 | Conflated correctness and performance instead of separating them |

#### Model answer (9/10)

**Correctness failure:** Without surrogate keys, the fact table's foreign key (`location_id`) joins against the dimension's natural key, which appears in *multiple* SCD2 rows. Each fact row matches every historical version of its location — producing **fan-out / row multiplication**. An analyst computing `SELECT location_id, SUM(fare_amount) FROM fct_trips JOIN dim_location` would see each fare counted N times (N = number of dimension versions). Returns wrong values with no error. The colleague's "date range comparison" mitigation is supposed to fix this, but range filters are easy to write incorrectly (`<` vs `<=` boundary cases) and analysts copy-pasting joins will silently miss the date filter, reintroducing the bug.

**Performance failure:** Even when the date range filter is correctly added (`f.trip_date >= dl.valid_from AND f.trip_date < dl.valid_to`), the join becomes a **range join** rather than an equality join. Modern columnar warehouses heavily optimize equality joins via hash tables — `INTEGER = INTEGER` lookups are near-constant-time per row. Range joins require interval-tree or sort-merge strategies, orders of magnitude slower at scale. Billion-row fact: 30 seconds with surrogates vs 30 minutes with natural-key range joins. Same correctness, dramatically different latency.

The two failures have *different fixes* in the worst case (correctness needs data correction; performance needs query optimization), so naming them separately demonstrates understanding of failure categories.

#### Key lessons

1. **"Cartesian product" vs "fan-out join."** Cartesian = no join condition. Fan-out = one-to-many via non-unique join key. Different mechanics.
2. **Multi-part questions need multi-part answers structurally.** When the question asks for X AND Y, the answer should have X-paragraph and Y-paragraph, not one combined paragraph that covers both.
3. **Range joins ≠ equality joins** in performance terms. Worth knowing for any warehouse query optimization conversation.

---

### Q9 — Profiling Investigation Surprise

**The question:**
> You profile a new dataset and find that a column `customer_segment` has 47 distinct values when documentation says there should be only 5 (Bronze/Silver/Gold/Platinum/Diamond). Walk through your investigation plan — what queries would you run, in what order, and what hypotheses would you be testing? Identify at least three plausible root causes and what each would look like in your query results.

#### Bryan's answer — 5.5/10

> I hypothesize that our dataset was labeled incorrectly.
> Queries I would run:
> * Checking to see if the original customer_segment values are included in the 47 distinct values. If the values are not included, we can assume there was a mix up of the column names
> * Checking if the values are associated with another column. If the values are not present, we can
> * Query the values themselves to determine what column I would believe they would be from based on the context (works if the distinct values are not integers)

| Dimension | Score | Why |
|---|---|---|
| Technical Accuracy | 6/10 | "Labeling mix-up" hypothesis is plausible but only one possibility |
| Conceptual Depth | 5/10 | Single hypothesis explored; question asked for at least three |
| Vocabulary Precision | 6/10 | Two of three queries trail off mid-sentence ("we can ") |
| Trade-off Awareness | 5/10 | No structured matching of queries-to-hypotheses |

#### Model answer (9/10)

**Three+ plausible root causes with diagnostic fingerprints:**

1. **Documentation is stale.** Doc was written in 2020; business has added segments since then ("Diamond Plus," "Trial," "VIP"). Fingerprint: 5 documented values present with substantial counts; the other 42 are reasonable-looking strings; timestamps show new values appearing only after a date.
   ```sql
   SELECT customer_segment, MIN(created_at) AS first_seen, COUNT(*)
   FROM customers GROUP BY customer_segment ORDER BY first_seen;
   ```

2. **Data quality issues — typos, casing, whitespace.** Fingerprint: clusters of "Gold"/"gold"/"GOLD"/" Gold ", "Platinum"/"Platnum"/"Platinium". Normalization query crashes count from 47 to ~5:
   ```sql
   SELECT TRIM(LOWER(customer_segment)) AS normalized, COUNT(*)
   FROM customers GROUP BY normalized;
   ```

3. **Multi-tenancy or composite encoding.** Dataset is a union of business units, each with own segmentation; OR field is encoded "Gold-NY", "Gold/Premium". Fingerprint: structured composite values with separators, OR clean 5-segment pattern per region:
   ```sql
   SELECT region, customer_segment, COUNT(*)
   FROM customers GROUP BY region, customer_segment;
   ```

4. **Source-system migration.** Field used to be INT (1-5 mapped externally) and migrated to VARCHAR mid-history. Old rows have "1"-"5"; new have name strings; buggy migration produces "1", "Bronze", "01", "BRONZE_TIER" mix.

**Investigation order distinguishes between candidates:**
1. Distribution + length query — values dominated by a few = typos likely (cause 2). Balanced = cause 1 or 3.
2. Normalization query (lowercase + trim) — count crashes 47→5 = cause 2 confirmed.
3. Time-ordered query — new values cluster after a date = cause 1.
4. Cross-tabulation with region — 47 splits cleanly per region = cause 3.

#### Key lessons

1. **Investigation plan = decision tree.** Each query distinguishes between candidate hypotheses. "If I see X, then cause A; if Y, cause B."
2. **"At least three" means at least three.** Count what the question asks for; verify your answer matches.
3. **Diagnostic fingerprints separate good investigations from random poking.** Each hypothesis should have a *predictable* signature in the data.

---

### Q10 — Defending the Whole Design

**The question:**
> A new tech lead joins your team and questions the entire star schema design: *"Why are we using a separate `dim_date` table when every modern warehouse has built-in date functions? Why role-playing dimensions instead of just having `pickup_borough` and `dropoff_borough` columns directly in the fact? And why a flat `dim_location` when we can compute everything from PostGIS-style spatial libraries?"* Defend each of the three design choices. For each, explain (a) what concrete capability you'd lose with their proposal, and (b) what skill or interview-relevant signal the proper version demonstrates.

#### Bryan's answer — 5.5/10

> Using "built-in" date functions makes our company lose the capability to define our personal company calendar, each companies has a different schedule, different timelines, so attempting to coalesce these all into one "built-in" function can lose the company a lot of relevant information. We use role-playing dimensions because our locations are more finely grained than the general boroughs. We use unique zones that have been defined by the TLC, and using boroughs would be reductive and would result in data loss. We have a flat dim_location for the partially the same reason. We use two columns from dim_location simultaneously in order to correctly measure pick up and drop off areas. Using a PostGIS-style spacial library would make our maps too finely grained, leading to potential inaccuracies when it comes to analysis.

| Dimension | Score | Why |
|---|---|---|
| Technical Accuracy | 5/10 | All three challenges addressed but with significant misreads on Challenges 2 and 3 |
| Conceptual Depth | 5/10 | One angle per challenge; question asked for two angles each (capability + signal) |
| Vocabulary Precision | 6/10 | "Coalesce" used loosely; "role-playing" rationale not actually about role-playing |
| Trade-off Awareness | 6/10 | Real cost identified for `dim_date`; weaker for the other two |

#### Model answer (9/10)

**Challenge 1 — `dim_date` vs built-in date functions:**
- (a) Capability lost: organization-specific calendar concepts. Built-in functions extract `MONTH(timestamp)` but don't know your fiscal year starts in February, your company-specific holidays, or that Juneteenth became a federal holiday in 2021. Every analyst would re-implement this logic in queries, with subtle differences (one uses `MONTH`, another `TO_CHAR(ts, 'MMMM')`, a third ISO week).
- (b) Signal: senior-level data modeling. Knowing calendar logic belongs in a centralized dimension to ensure consistency across all reports — not scattered through individual queries — is a portfolio-grade signal.

**Challenge 2 — Role-playing dimensions vs denormalized columns:**
- (a) Capability lost: every other location attribute beyond borough. Denormalizing `pickup_borough` directly into the fact loses zone, service_zone, future neighborhood/district/centroid additions. Either you explode the fact with 6+ denormalized columns to maintain, or you lose ability to filter by anything except borough. Worse: zone-name change = millions of fact-row UPDATEs instead of one dimension-row UPDATE.
- (b) Signal: **understanding of dimensional modeling fundamentals.** (1) dimensions exist to centralize attribute changes, (2) the same physical entity can play multiple semantic roles in a fact, (3) SQL aliases disambiguate roles. Most junior engineers default to denormalizing and learn the cost when fact tables grow to 50 columns and zone renames cascade into multi-billion-row UPDATEs.

**Challenge 3 — Flat `dim_location` vs PostGIS:**
- (a) Capability lost: PostGIS-based dynamic zone computation requires (1) actual lat/lng in the fact (TLC stopped publishing in 2016 — switched to LocationIDs precisely to anonymize), (2) per-query point-in-polygon math against 260 zone polygons for every fact row scanned, and (3) PostGIS or equivalent in your warehouse. You'd be doing per-query work that should be done once at ingestion. Worst: you lose the ability to handle historical zone changes via SCD2 — polygons have no native concept of "this zone's name in January 2024 vs December 2024."
- (b) Signal: **knowing when *not* to reach for fancy infrastructure.** PostGIS is powerful but for our use case (260 zones, lookup-only, no spatial analysis needed) it's massive over-engineering. Senior engineers know "we *could* use PostGIS" and "we *should* use PostGIS" are different questions.

#### Key lessons

1. **Read the proposal carefully before defending.** Challenge 2 wasn't about zone-vs-borough granularity; it was about denormalizing already-resolved borough names. Challenge 3 wasn't about PostGIS being "too fine-grained"; it was about lookup tables vs dynamic spatial computation.
2. **Enumeration depth.** Question explicitly asked "(a) capability lost AND (b) signal demonstrated" — six items total. Six should be delivered.
3. **The "interview signal" framing is meta.** Defending a design is not just "is this right?" but "what does this design *say* about the engineer who built it?"
4. **Diagnostic question for multi-part:** "How many distinct things does this question ask me to enumerate? Have I named that many?"

---

### Phase 1 Re-drill — Round 1 (Q-Re-3, Schema vs Semantics Stability)

*Drill date: 2026-05-08. Re-drill of original Q6 (scored 6.0/10). Preceded by full consolidation session (Layers 1-3): foundation rebuild, drift category enumeration, diagnostic ritual transfer to fitness-tracker domain. Confidence at re-drill: ≥96%.*

#### Q-Re-3 — Schema vs Semantics Stability (8-year e-commerce dataset)

**The question:**

> You inherit an 8-year e-commerce orders dataset from a previously-acquired company that you're now integrating. The schema is identical across all 8 years. Walk through your investigation plan to validate the *semantics* are stable: (a) what queries would you run, (b) what would you specifically look for in the results, and (c) name **three distinct categories of semantic drift** schema-level inspection would miss — for each category, give a concrete example of what it might look like in this e-commerce dataset.
>
> **Schema reference:**
>
> | Column | Type |
> |---|---|
> | `order_id` | INT |
> | `customer_id` | INT |
> | `order_date` | DATE |
> | `order_total` | DECIMAL(10,2) |
> | `currency_code` | VARCHAR (e.g., "USD", "EUR", "GBP") |
> | `payment_method` | VARCHAR |
> | `shipping_country` | VARCHAR |
> | `order_status` | VARCHAR |
> | `discount_amount` | DECIMAL(10,2) |
> | `is_gift` | BOOLEAN |

#### Bryan's answer — 8.0/10 ✓ (closes consolidation)

> a.
> * I would query the distribution of payment methods by date (compare 8 years ago to today) in order to determine if this can be considered a taxonomy expansion drift.
> * I would query the dataset by comparing the number of rows to the number of rows with is_gift = TRUE, I would also query the dataset in order to determine when is_gift began to be implemented in order to determine if this is a soft-state drift.
> * I would query each column in order to determine the presence of NULL values
> b. I would specifically look for:
> * payment methods that appear in today's query and their prevalence.
> * a lack of is_gift = TRUE for a given year, which means this row may not have been implemented during that year if is_gift = TRUE exists in a row pertaining to another year.
> * a large amount of NULL values in a column, which implies the column is not populated with the values that are expected to be there.
> c. Three distinct categories of semantic drift that schema-level inspection would miss:
> * soft-state drift, as the is_gift column may not have been implemented until 2020, and other gifts may be mislabeled as FALSE when they were in fact, gifts.
> * taxonomy drift - in the 8 years that this dataset has been active, multiple payment methods and buy now pay later options have been implemented, aggregations without keeping this in mind are sure to present incorrect, but plausible, measures that could be used to make important decisions.
> * NULL-population drift - One of these columns could contain many NULL values that would not be spotted if only checking the schema out. In this example, they may have included order_status 2 years ago, meaning the rest of the column would contain NULLs

| Dimension | Score | Why |
|---|---|---|
| Technical Accuracy | 8/10 | All three categories correctly identified; mechanisms sound |
| Conceptual Depth | 8/10 | Each category includes a plausible mechanism grounded in the e-commerce domain |
| Vocabulary Precision | 8/10 | Used "soft-state," "taxonomy expansion," "NULL-population" correctly. One small slip: `is_gift` example is closer to NULL-population than soft-state |
| Trade-off Awareness | 7/10 | Implicit understanding present; missed leveraging the *acquisition* hint in the question framing |

#### Model answer (9/10)

**(a) Investigation queries** — apply the structural pass + semantic pass discipline:

```sql
-- Structural pass: confirm schema stability across years (already given)
-- Semantic pass: per-column queries for each high-analytical-weight column

-- Currency drift check
SELECT YEAR(order_date), currency_code, COUNT(*)
FROM orders GROUP BY 1, 2 ORDER BY 1, 3 DESC;

-- Payment method taxonomy drift
SELECT YEAR(order_date), payment_method, COUNT(*)
FROM orders GROUP BY 1, 2 ORDER BY 1;

-- Order total scale check (drift in unit or definition)
SELECT YEAR(order_date),
       AVG(order_total), MIN(order_total), MAX(order_total),
       AVG(discount_amount)
FROM orders GROUP BY 1 ORDER BY 1;

-- is_gift implementation check
SELECT YEAR(order_date), is_gift, COUNT(*)
FROM orders GROUP BY 1, 2 ORDER BY 1, 2;

-- order_status taxonomy/soft-state drift
SELECT YEAR(order_date), order_status, COUNT(*)
FROM orders GROUP BY 1, 2 ORDER BY 1;

-- shipping_country encoding consistency
SELECT YEAR(order_date), LENGTH(shipping_country), COUNT(*)
FROM orders GROUP BY 1, 2;
```

**(b) Specific signals to look for:**

- `currency_code` distribution shifting around acquisition date (acquired company in EUR, parent in USD)
- `payment_method` new values appearing partway through (taxonomy expansion); old values disappearing (deprecation)
- `order_total` and `discount_amount` average shifting by 100x (cents↔dollars unit drift)
- `is_gift` always FALSE before some year, then mixed (NULL-population drift — column existed but unpopulated)
- `order_status` values changing or new values appearing (taxonomy expansion or soft-state — was "canceled" added later because cancels used to be deleted?)
- `shipping_country` length distribution shifting from 2 to 3 (ISO alpha-2 → alpha-3 encoding change)

**(c) Three distinct drift categories with acquisition-specific examples:**

1. **Unit/encoding drift in `currency_code` and `order_total`** — the acquired company may have been EUR-denominated. After integration, all orders are stored in their *original* currency, but a naive `SUM(order_total)` mixes EUR and USD invisibly. Even when `currency_code` is correctly stamped per row, analysts forgetting to filter or convert by currency get inflated/deflated totals. Same numeric value, different unit.

2. **Definition drift in `order_total`** — the acquired company may have included tax in `order_total` while the parent excludes it (or vice versa). Same column, same unit, *different real-world concept*. A trend analysis showing "order_total grew 12% in the year of acquisition" is artifactual — the apparent growth is the parent's inclusive-of-tax accounting absorbing the acquired company's exclusive-of-tax data.

3. **Taxonomy expansion clash in `order_status`** — the acquired company used statuses like `placed`, `fulfilled`, `returned`. The parent uses `pending`, `shipped`, `refunded`. Post-merge, the same column has 6+ values that overlap-but-differ semantically. Analysts asking "what % of orders are completed?" must define which statuses count — and might get wildly different numbers depending on whether they include `fulfilled` (acquired's term) alongside `shipped` (parent's term) or treat them as distinct.

**The acquisition lens:** every drift category has an acquisition-specific manifestation that wouldn't appear in organically-grown data. The question's framing was a hint to lean into that.

#### Key lessons

1. **Soft-state vs NULL-population precision.** Soft-state = same row, meaning shifts via flag policy (canceled rows kept with `is_active=FALSE`). NULL-population = column existed but wasn't populated until a feature launched. The `is_gift` example is the latter, not the former. Worth refining the mental model so categories don't blur.
2. **Read scenario context for hints.** "Previously-acquired company" was a forcing function for acquisition-specific drift — currency clashes, status taxonomy collisions, accounting-standard differences. A senior answer leverages context clues like this.
3. **Framework transferred.** The structural pass + semantic pass discipline applied automatically without consulting the doc — that's the consolidation working. Original Q6 (6.0) → Q-Re-3 (8.0) = +2.0 improvement, matching the Phase 0 Q-Re-2 consolidation pattern.

#### Consolidation status

✅ **CLOSED.** Score 8.0 meets individual threshold. Schema vs Semantics Stability model is internalized and transferable. Confidence: ≥96%. Round 1 of Phase 1 re-drill complete.

---

### Phase 1 Re-drill — Round 2 (Q-Re-1, Investigation as Decision Tree)

*Drill date: 2026-05-08. Re-drill of original Q9 (scored 5.5/10). Preceded by full consolidation session (Layers 1-3) plus a mid-round mini-consolidation on hypothesis-fingerprint sharpness when the first re-attempt landed at 7.5. Confidence at final re-attempt: ≥96%.*

#### Q-Re-1 — Profiling Investigation (HR analytics, 327 department codes)

**The question:**

> You're profiling a new HR analytics dataset for a Fortune 500 company. The column `department_code` is documented as a 4-character code (e.g., "FINX", "HRBP", "ENGG"). When you query distinct values, you find 327 distinct codes — some 4 characters, some 3, some 5, some with hyphens, some with numbers.
>
> Walk through your investigation plan: (a) what queries would you run in what order, (b) what hypotheses are you testing with each query, and (c) name at least three plausible root causes with the specific data signature each would leave in your query results.
>
> **Schema reference:**
>
> ```
> employees
>   employee_id      INT (PK)
>   department_code  VARCHAR
>   hire_date        DATE
>   region           VARCHAR
>   business_unit    VARCHAR
>   manager_id       INT
> ```

#### Bryan's answer — 8.0/10 ✓ (closes consolidation)

> a.
> * My first query would split columns that contain a hyphen, and then grouping both sides in order to see if there are signs reminiscent of these being regional codes, department codes, or other distinguishing characteristics.
> * My second query would run SELECT(DISTINCT(TRIM(LOWER(col)))) to determine if a majority of the distinct values are attributed to typos or user input.
> * My third query would filter department codes that are not 4 characters, and compare the count to how many are consisting of 4 characters.
> b.
> * I am testing the hypothesis of composite/encoded data with query 1, doc drift could also be considered but composite/encoded data is stronger.
> * I am testing the hypothesis of data quality/user input with query 2
> * I am testing the hypothesis of schema mislabel with query 3
> c.
> * composite/encoded data: either side of hyphen would appear to resemble something similar to a region/department code/role hierarchy code, etc. We would see that the overall count of distinct values collapses if the left/right side of a hyphen coincides with a region, for instance. We would not see a similar count of distinct values.
> * We would see a strong collapse of distinct values, approximately 30 or so plus data with notable errors, such as typos, after applying normalization.
> * We would see a large amount of 'department_codes' that are greater or smaller than 4 characters, this could potentially indicate a mislabeling of this column.

| Dimension | Score | Why |
|---|---|---|
| Technical Accuracy | 8/10 | Three valid hypotheses; queries align with hypotheses; framework applied throughout. One hypothesis-query mismatch: length-anomaly query in (a3) doesn't uniquely discriminate schema mislabel from composite or data quality |
| Conceptual Depth | 8/10 | Distinguishing-query design visible; predict-before-query work present; negative-evidence framing applied ("we would not see..."); magnitude awareness ("approximately 30") |
| Vocabulary Precision | 8/10 | "Composite/encoded," "data quality/user input," "schema mislabel" used correctly. One phrasing slip in composite fingerprint ("we would not see a similar count of distinct values" is unclear) |
| Trade-off Awareness | 8/10 | Acknowledged competing hypotheses without ignoring them ("doc drift could also be considered but composite/encoded data is stronger") — senior epistemic discipline |

#### Model answer (9/10)

**(a) Investigation queries in order of information gain:**

```sql
-- Query 1: Normalization-collapse test (data quality discriminator)
-- Highest information gain because the magnitude tells us a lot in one number
SELECT
  COUNT(DISTINCT department_code) AS raw_count,
  COUNT(DISTINCT TRIM(LOWER(department_code))) AS normalized_count,
  COUNT(DISTINCT department_code) - COUNT(DISTINCT TRIM(LOWER(department_code))) AS collapse_size
FROM employees;
-- Crash from 327→~30 = data quality confirmed
-- Stays at ~320+ = data quality ruled out; investigate other hypotheses

-- Query 2: Composite structure test
SELECT
  SPLIT_PART(department_code, '-', 1) AS prefix,
  COUNT(DISTINCT SPLIT_PART(department_code, '-', 2)) AS suffix_variety
FROM employees
WHERE department_code LIKE '%-%'
GROUP BY 1 ORDER BY suffix_variety DESC;
-- If prefix list is small (~30) and each prefix has small suffix variety (~5-10) →
-- composite confirmed; 30 × 8 ≈ 240 + uncounted non-hyphenated ≈ 327

-- Query 3: Multi-source partition test
SELECT region, business_unit, COUNT(DISTINCT department_code) AS distinct_codes
FROM employees
GROUP BY 1, 2 ORDER BY distinct_codes;
-- If each (region, unit) group has small consistent set (~30), with codes
-- differing between groups → multi-source confirmed (partitioned signal)

-- Query 4: Schema mislabel test (inspect non-canonical values for cross-column resemblance)
SELECT department_code, COUNT(*) AS occurrences
FROM employees
WHERE LENGTH(department_code) <> 4
   OR department_code ~ '[0-9]'
GROUP BY 1 ORDER BY occurrences DESC LIMIT 50;
-- If values resemble employee_id (pure integers), job_title phrases, or hire_date
-- patterns → schema mislabel; if values look like structured codes → ruled out

-- Query 5: Temporal pattern test (migration artifact + doc drift discriminator)
SELECT
  YEAR(hire_date),
  COUNT(DISTINCT department_code) AS codes_in_year,
  AVG(LENGTH(department_code)) AS avg_length
FROM employees GROUP BY 1 ORDER BY 1;
-- Sharp transition at specific year → migration artifact
-- Gradual increase in distinct codes over time → doc drift
-- Uniform → both ruled out
```

**(b) Hypothesis-to-query map:**

| Query | Distinguishes |
|---|---|
| 1 | data quality vs. everything else (magnitude of normalization collapse) |
| 2 | composite/encoded vs. everything else (multiplicative structure on split) |
| 3 | multi-source vs. doc drift (partitioned vs. uniform signal across groups) |
| 4 | schema mislabel vs. all structured-code hypotheses (cross-column resemblance) |
| 5 | migration artifact vs. doc drift (sharp temporal transition vs. gradual evolution) |

**(c) Five+ fingerprints with tight signatures:**

1. **Data quality:** `COUNT(DISTINCT TRIM(LOWER(...)))` crashes from 327 to ~30-50. Order-of-magnitude collapse is the discriminator — composite or multi-source would show only marginal collapse (~5% at most). Absence of structured patterns (no clean hyphenated splits) rules out composite.

2. **Composite/encoded:** Splitting on `-` yields small finite sets on each side (~30 prefixes, ~8 suffixes). 30 × 8 ≈ 240 explains most of the 327 (slight overshoot suggests a third dimension like seniority level). Absence of near-duplicates rules out data quality.

3. **Multi-source heterogeneity:** GROUP BY (region, business_unit) shows each group with a *small, internally-consistent* set of codes (~30 per group), with codes *differing between groups* — partitioned signal. Total distinct = sum of per-group distinct because groups don't overlap.

4. **Schema mislabel:** Non-canonical values resemble *another column's content* — pure integers (employee_id-like), long English phrases (job_title-like), pure dates (hire_date-like). Discriminator from composite: values don't follow a structured composite pattern; from data quality: values aren't near-duplicates of canonical codes.

5. **Migration artifact:** GROUP BY YEAR(hire_date) shows a sharp transition — pre-Year-X codes follow one format, post-Year-X codes follow another. Coexistence of two distinct formats over time, not gradual evolution.

6. **Documentation drift:** GROUP BY YEAR(hire_date) shows gradual, monotonic increase in distinct codes over years. No sharp transition (that would be migration); no partition by region (that would be multi-source); no normalization collapse (that would be data quality).

#### Key lessons

1. **The 327 number itself is evidence.** A senior investigator factors 327 into possible explanations: 30×8 (composite), 327 standalone (doc drift unique values), sum-of-region-clusters (multi-source). The number tells you which hypotheses are arithmetically plausible.
2. **Information gain orders queries.** The normalization-collapse query rules out the most hypotheses fastest. Run highest-information-gain queries first to narrow the space, then drill in.
3. **Hypothesis-query mismatches are common gaps.** Length-anomaly is shared by many hypotheses, not specific to schema mislabel. The schema-mislabel-specific signature is cross-column resemblance, not length-deviation.
4. **Composite encoding is the strongest a-priori candidate for HR department codes.** Large companies frequently encode org structure into codes (ENGG-PLATFORM, HRBP-EMEA). Reaching for it first is senior pattern-matching.
5. **Mini-consolidation as a recovery pattern.** When a re-drill falls short (7.5), pause to do focused precision-building on the specific gap (fingerprint sharpness) before re-attempting — instead of either accepting the lower score or jumping immediately to another fresh question. This is a meta-skill: surgical correction beats global re-attack.

#### Consolidation status

✅ **CLOSED.** Score 8.0 meets individual threshold. Investigation as Decision Tree framework is internalized and transferable. Confidence: ≥96%. Round 2 of Phase 1 re-drill complete.

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
