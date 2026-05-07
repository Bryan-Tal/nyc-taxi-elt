# NYC Taxi ELT Pipeline

A production-style batch ELT pipeline that ingests NYC Taxi & Limousine Commission trip data into Snowflake, transforms it into a star schema with dbt, and orchestrates the workflow with Airflow. Built as a portfolio project to demonstrate end-to-end data engineering practice.

**Status:** 🚧 In active development — Phase 0 (platform setup) and Phase 1 (data exploration & schema design) complete; Phase 2 (ingestion) is next.

---

## Project Goals

- Build a production-realistic ELT pipeline using the modern data stack (Snowflake + dbt + Airflow + Docker + GitHub Actions)
- Ship infrastructure with security best practices: scoped IAM, role-based access control, no embedded credentials, gitignored secrets
- Apply dimensional modeling (Kimball-style star schema) with slowly changing dimensions, role-playing dimensions, and surrogate keys
- Document architecture decisions and learnings so the project doubles as a learning artifact

This project is not a tutorial reproduction. Every architectural choice (storage integration vs. embedded keys, medallion layering, type-tolerant casting in STAGING, CI gates, etc.) is made deliberately to mirror what production data teams actually do.

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
- **RAW** — untouched Parquet data ingested from S3 with source-native types
- **STAGING** — typed, cleaned, conformed via dbt with `TRY_CAST` to canonical types
- **MARTS** — business-ready star schema (`fct_trips`, `dim_location`, `dim_vendor`, `dim_date`, `dim_ratecode`, `dim_payment_type`)
- **SNAPSHOTS** — dbt-managed SCD Type 2 history for `dim_location` and `dim_vendor`

---

## Tech Stack

| Layer | Tool | Why |
|---|---|---|
| Source data | NYC TLC public Parquet | Real-world scale, schema evolution across years |
| Cloud storage | AWS S3 | Industry-standard data lake landing zone |
| Warehouse | Snowflake | Most-requested cloud warehouse on DE job postings |
| Auth | Snowflake Storage Integration → IAM Role (STS AssumeRole) | No embedded credentials; production-correct pattern |
| Local profiling | DuckDB | In-process columnar SQL engine; queries Parquet directly without loading into memory |
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
├── ingestion/            # Python extract/load code
│   ├── exploration/      # Phase 1 profiling scripts (DuckDB)
│   ├── src/              # Phase 2 ingestion modules
│   └── tests/
├── data/raw/             # Local Parquet samples (gitignored)
├── dbt/                  # dbt project (Phase 3)
│   ├── models/
│   │   ├── staging/      # silver — canonical types via TRY_CAST
│   │   ├── intermediate/
│   │   └── marts/        # gold — fct_trips + 5 dimensions
│   ├── snapshots/        # SCD Type 2 history (dim_location, dim_vendor)
│   ├── tests/
│   └── macros/
├── infrastructure/       # Snowflake DDL, AWS setup scripts
│   ├── snowflake/
│   └── aws/
├── docs/                 # Documentation, design artifacts, study notes
├── .github/workflows/    # CI/CD (Phase 5)
├── docker-compose.yaml   # Local Airflow + Postgres stack
├── .env.example          # Environment variable template
└── .gitignore            # Protects .env, .venv, data/, dbt/target, airflow/logs
```

---

## Current Status

| Phase | Status | Description |
|---|---|---|
| 0 — Platform Foundation | ✅ Complete | Snowflake account + RBAC, AWS S3 + IAM, storage integration, Docker Airflow stack, repo hygiene. Synthesis re-drill avg 8.0 ✓ |
| 1 — Data Source & Exploration | ✅ Complete | Schema design (star schema, 5 dimensions, SCD types per dimension), DuckDB profiling, schema evolution investigation across 2015/2019/2024 |
| 2 — Ingestion Layer | ⏳ Next | Python ingestion → S3 → Snowflake RAW via storage integration; type-tolerant casting in STAGING |
| 3 — dbt Transformations | ⏳ Pending | Staging/intermediate/marts models with SCD Type 2 snapshots |
| 4 — Orchestration with Airflow | ⏳ Pending | Monthly DAG: ingest → dbt run → dbt test |
| 5 — CI/CD with GitHub Actions | ⏳ Pending | Lint SQL, run dbt tests on PR |
| 6 — Documentation & Polish | ⏳ Pending | Architecture diagrams, lessons learned, dbt docs site |

See [`docs/roadmap.md`](docs/roadmap.md) for granular checkbox-level progress.

### Phase 1 Outputs

- [`docs/design-doc.md`](docs/design-doc.md) — Complete dimensional model rationale, decision log, trade-offs
- [`docs/data-dictionary.md`](docs/data-dictionary.md) — Column-level reference for fct_trips and 5 dimensions
- [`ingestion/exploration/profile.py`](ingestion/exploration/) — DuckDB profiling scripts

---

## How to Run Locally

### Prerequisites

- macOS, Linux, or Windows with WSL2 (project lives on Linux filesystem — see Phase 1 lessons)
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

### Run Phase 1 Profiling Locally

```bash
# Set up Python venv (one time)
python3 -m venv .venv
source .venv/bin/activate
pip install duckdb

# Download a sample month
mkdir -p data/raw
curl -o data/raw/yellow_tripdata_2024-01.parquet \
  https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet

# Run profiling
python3 ingestion/exploration/profile.py
```

---

## Documentation & Learning Artifacts

This project doubles as a structured learning system. The `/docs/` folder contains:

- [`README.md`](docs/README.md) — Artifact index and how each piece fits together
- [`roadmap.md`](docs/roadmap.md) — 10-pillar DE roadmap with checkbox progress
- [`design-doc.md`](docs/design-doc.md) — Phase 1 dimensional model design rationale
- [`data-dictionary.md`](docs/data-dictionary.md) — Per-table column reference
- [`mental-models.md`](docs/mental-models.md) — Reusable thinking tools surfaced across phases
- [`synthesis-questions.md`](docs/synthesis-questions.md) — Interview-style drills per phase
- [`synthesis-answers.md`](docs/synthesis-answers.md) — Verbatim answers + grading + model answers
- [`synthesis-log.md`](docs/synthesis-log.md) — Recurring weak patterns + strong patterns log
- [`tooling-reference.md`](docs/tooling-reference.md) — Commands, SQL idioms, DuckDB↔Pandas mappings
- [`de_flashcards.csv`](docs/de_flashcards.csv) — Spaced-repetition deck (Anki-importable)

---

## Key Design Decisions

A handful of intentional choices that distinguish this project from a tutorial reproduction:

**Storage integration over embedded credentials.** Snowflake reads from S3 via an IAM role assumed through STS, not embedded AWS access keys. Credentials rotate automatically and never appear in Snowflake DDL. (Phase 0)

**Medallion architecture as separate Snowflake schemas.** RAW / STAGING / MARTS / SNAPSHOTS are distinct schemas, not table prefixes. This enables per-layer permissions, retention policies, and analyst access controls. (Phase 0)

**Star schema (not snowflake schema).** Modern columnar warehouses compress repeated dimension values efficiently, making the storage advantage of normalized snowflake schemas largely moot. Star wins on query simplicity and analyst friendliness. (Phase 1)

**Type-tolerant casting in STAGING.** Source Parquet types drift across years (e.g., `passenger_count` is BIGINT in 2015, DOUBLE in 2019, BIGINT in 2024). Schema evolution investigation in Phase 1 confirmed type drift but no column add/drop. STAGING dbt models cast to canonical target types using `TRY_CAST`, isolating type-handling complexity from MARTS. (Phase 1)

**Per-dimension SCD type assignment.** Dimensions where attribute changes carry historical meaning (zone names, vendor names) get SCD Type 2 with surrogate keys. Dimensions where changes are cosmetic (rate code descriptions, payment type names) get Type 1. `dim_date` is Type 0 (calendar attributes are fixed). (Phase 1)

**Auto-suspend on warehouses.** All warehouses set to `AUTO_SUSPEND = 60` to minimize idle compute cost during development. (Phase 0)

**Gitignored secrets, committed templates.** `.env` is never committed; `.env.example` documents required variables. The project lives on the Linux filesystem (`~/Projects/`) — never in OneDrive/Dropbox/iCloud-managed folders, which interfere with rapid file operations and can leak gitignored secrets to cloud sync.

**`_PIP_ADDITIONAL_REQUIREMENTS` in dev only.** Phase 0 uses Airflow's pip-on-startup convenience. Phase 4 will graduate to a custom Dockerfile that bakes packages at build time — the production-correct pattern.

---

## License

This project is for educational and portfolio purposes. NYC TLC data is publicly available under the [NYC Open Data terms of use](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page).
