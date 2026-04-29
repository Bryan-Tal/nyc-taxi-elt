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

*Q2–Q10 will be added here as Bryan completes them.*

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
