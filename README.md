# NYC Taxi ELT Pipeline

A production-style batch ELT pipeline that ingests NYC Taxi & Limousine Commission trip data into Snowflake, transforms it into a star schema with dbt, and orchestrates the workflow with Airflow. Built as a portfolio project to demonstrate end-to-end data engineering practice.

**Status:** 🚧 In active development — Phase 0 (platform setup) complete; Phase 1 (data exploration and modeling) in progress.

---

## Project Goals

- Build a production-realistic ELT pipeline using the modern data stack (Snowflake + dbt + Airflow + Docker + GitHub Actions)
- Ship infrastructure with security best practices: scoped IAM, role-based access control, no embedded credentials, gitignored secrets
- Apply dimensional modeling (Kimball-style star schema) with slowly changing dimensions
- Document architecture decisions and learnings so the project doubles as a learning artifact

This project is not a tutorial reproduction. Every architectural choice (storage integration vs. embedded keys, medallion layering, CI gates, etc.) is made deliberately to mirror what production data teams actually do.

---

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌───────────────┐    ┌────────────┐
│  NYC TLC    │───▶│   Python     │───▶│   Snowflake   │───▶│    dbt     │
│  Parquet    │    │   Ingestion  │    │   (RAW layer) │    │ transforms │
│  (source)   │    │   (Docker)   │    │               │    │            │
└─────────────┘    └──────────────┘    └───────────────┘    └─────┬──────┘
                          ▲                                       │
                          │                                       ▼
                  ┌───────┴──────┐                     ┌──────────────────┐
                  │   Airflow    │                     │  Snowflake       │
                  │  (orchestr.) │                     │  STAGING → MARTS │
                  └──────────────┘                     │  (star schema)   │
                          ▲                            └──────────────────┘
                          │
                  ┌───────┴──────┐
                  │  GitHub      │
                  │  Actions CI  │
                  └──────────────┘
```

**Layers (medallion architecture):**
- **RAW** — untouched Parquet data ingested from S3
- **STAGING** — typed, cleaned, conformed
- **MARTS** — business-ready star schema (`fct_trips`, `dim_locations`, `dim_vendors`, `dim_date`)
- **SNAPSHOTS** — dbt-managed SCD Type 2 history

---

## Tech Stack

| Layer | Tool | Why |
|---|---|---|
| Source data | NYC TLC public Parquet | Real-world scale, schema evolution across years |
| Cloud storage | AWS S3 | Industry-standard data lake landing zone |
| Warehouse | Snowflake | Most-requested cloud warehouse on DE job postings |
| Auth | Snowflake Storage Integration → IAM Role (STS AssumeRole) | No embedded credentials; production-correct pattern |
| Ingestion | Python + boto3 | Standard for cloud-native ETL/ELT |
| Transformation | dbt | The modern transformation standard |
| Orchestration | Apache Airflow 2.10 | Industry-standard scheduler |
| Containerization | Docker Compose | Reproducible local development |
| CI/CD | GitHub Actions | Lints SQL, runs dbt tests, blocks bad merges |

---

## Repository Structure

```
nyc-taxi-elt/
├── airflow/              # Airflow DAGs, plugins, logs
│   ├── dags/             # DAG definitions (Phase 4)
│   └── plugins/
├── ingestion/            # Python extract/load code (Phase 2)
│   ├── src/
│   └── tests/
├── dbt/                  # dbt project (Phase 3)
│   ├── models/
│   │   ├── staging/      # silver layer
│   │   ├── intermediate/
│   │   └── marts/        # gold layer
│   ├── snapshots/        # SCD Type 2 history
│   ├── tests/
│   └── macros/
├── infrastructure/       # Snowflake DDL, AWS setup scripts
│   ├── snowflake/
│   └── aws/
├── docs/                 # Documentation, learning artifacts, study notes
├── .github/workflows/    # CI/CD (Phase 5)
├── docker-compose.yaml   # Local Airflow + Postgres stack
├── .env.example          # Environment variable template
└── .gitignore            # Protects .env, dbt/target, airflow/logs
```

---

## Current Status

| Phase | Status | Description |
|---|---|---|
| 0 — Platform Foundation | ✅ Complete | Snowflake account + RBAC, AWS S3 + IAM, storage integration, Docker Airflow stack, repo hygiene |
| 1 — Data Source & Exploration | 🚧 In progress | Profiling NYC TLC data, designing star schema |
| 2 — Ingestion Layer | ⏳ Pending | Python ingestion → Snowflake RAW via S3 stage |
| 3 — dbt Transformations | ⏳ Pending | Staging/intermediate/marts models with SCD Type 2 |
| 4 — Orchestration with Airflow | ⏳ Pending | Daily DAG: ingest → dbt run → dbt test |
| 5 — CI/CD with GitHub Actions | ⏳ Pending | Lint SQL, run dbt tests on PR |
| 6 — Documentation & Polish | ⏳ Pending | Architecture diagrams, lessons learned, dbt docs |

See [`docs/roadmap.md`](docs/roadmap.md) for granular checkbox-level progress.

---

## How to Run Locally

### Prerequisites

- macOS, Linux, or Windows with WSL2
- Python 3.11+
- Docker Desktop
- AWS account (free tier sufficient)
- Snowflake account ([30-day trial](https://signup.snowflake.com/) sufficient)

### Setup

1. **Clone the repo**
   ```bash
   git clone git@github.com:<your-username>/nyc-taxi-elt.git
   cd nyc-taxi-elt
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your Snowflake account and AWS credentials
   ```

3. **Initialize Snowflake** — see [`infrastructure/snowflake/`](infrastructure/snowflake/) for setup SQL.

4. **Configure AWS** — see [`infrastructure/aws/`](infrastructure/aws/) for IAM role and S3 bucket setup.

5. **Boot the local Airflow stack**
   ```bash
   docker compose up airflow-init   # one-time DB init
   docker compose up -d             # start the stack
   ```

6. **Verify** — Airflow UI at [http://localhost:8080](http://localhost:8080) (admin/admin).

Full setup walkthrough including troubleshooting in [`docs/lessons/phase-0-lessons.md`](docs/lessons/) *(coming Phase 6)*.

---

## Documentation & Learning Artifacts

This project doubles as a structured learning system. The `/docs/` folder contains:

- [`roadmap.md`](docs/roadmap.md) — 10-pillar data engineering roadmap with checkbox progress
- [`synthesis-questions.md`](docs/synthesis-questions.md) — interview-style synthesis drills, one set per phase
- [`synthesis-answers.md`](docs/synthesis-answers.md) — model answers and grading on completed drills
- [`synthesis-log.md`](docs/synthesis-log.md) — personal log of recurring weak patterns
- [`terminal-cheatsheet.md`](docs/terminal-cheatsheet.md) — useful commands organized by tool
- [`de_flashcards.csv`](docs/de_flashcards.csv) — spaced-repetition deck (Anki-importable)

See [`docs/README.md`](docs/README.md) for an index and how each artifact fits together.

---

## Key Design Decisions

A handful of intentional choices that distinguish this project from a tutorial reproduction:

**Storage integration over embedded credentials.** Snowflake reads from S3 via an IAM role assumed through STS, not embedded AWS access keys. Credentials rotate automatically and never appear in Snowflake DDL.

**Medallion architecture as separate Snowflake schemas.** RAW / STAGING / MARTS / SNAPSHOTS are distinct schemas, not table prefixes. This enables per-layer permissions, retention policies, and analyst access controls.

**Auto-suspend on warehouses.** All warehouses set to `AUTO_SUSPEND = 60` to minimize idle compute cost during development.

**Gitignored secrets, committed templates.** `.env` is never committed; `.env.example` documents required variables. Anyone cloning the repo can configure their own environment without seeing real credentials.

**`_PIP_ADDITIONAL_REQUIREMENTS` in dev only.** Phase 0 uses Airflow's pip-on-startup convenience. Phase 4 will graduate to a custom Dockerfile that bakes packages at build time — the production-correct pattern.

---

## License

This project is for educational and portfolio purposes. NYC TLC data is publicly available under the [NYC Open Data terms of use](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page).
