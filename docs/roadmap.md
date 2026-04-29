# Data Engineering Roadmap

> **Purpose:** Track granular progress across 10 foundational pillars of data engineering. Updated continuously as concepts move from theory → applied → interview-ready.

## Legend

| Symbol | Meaning |
|---|---|
| ☐ | Not started |
| ◐ | In progress (encountered but not yet locked in) |
| ☑ | Theory learned (can explain) |
| ◇ | Applied in project (used in code/config, not just discussed) |
| ★ | Interview-ready (can explain + apply + discuss trade-offs) |

**Last updated:** 2026-04-29 (post Phase 0 synthesis drill grading)

---

## Summary

- **Total items tracked:** 90+
- **★ Interview-ready:** 4 *(Git workflows, Medallion architecture, Snowflake RBAC patterns, IAM principles)*
- **☑ Theory learned:** 5
- **◐ In progress:** 7
- **Current phase:** Project 1, Phase 1 (Data Source & Exploration) — pending re-drill of Q2/Q4/Q6 to clear Phase 0

---

## Pillar 1 — Programming Foundations

- ☐ Python for data engineering: idiomatic code, typing, virtual environments
- ☐ Python standard library deep dive: `itertools`, `collections`, `functools`, `contextlib`
- ☐ File I/O and serialization: JSON, CSV, Parquet, Avro, ORC (when to use which)
- ☐ Pandas for ETL (and its limits — when to reach for something else)
- ☐ PySpark fundamentals: DataFrames, transformations vs. actions, lazy evaluation
- ☐ PySpark optimization: partitioning, broadcast joins, caching, skew handling
- ☐ Shell/Bash scripting for pipeline glue
- ★ Git workflows: branching, PRs, rebasing, resolving conflicts *(promoted from ☑ via Phase 0 Q8 — 8.5/10)*
- ☐ Unit testing with `pytest`; testing data pipelines (great_expectations, dbt tests)
- ☐ Logging, error handling, retry logic, idempotency in pipelines
- ☐ Scala basics (optional but valued for Spark-heavy shops)

---

## Pillar 2 — Databases & SQL

- ☐ Advanced SQL: window functions, CTEs, recursive queries, pivot/unpivot
- ☐ Query optimization: execution plans, indexes, statistics
- ☐ Index types: B-tree, hash, bitmap, covering, partial — when each helps
- ☐ Transactions, isolation levels, ACID, MVCC
- ☐ Normalization (1NF–3NF, BCNF) and when to denormalize
- ☐ OLTP vs. OLAP workloads and engine differences
- ☐ Relational engines: PostgreSQL, SQL Server
- ☐ NoSQL families: document (MongoDB), key-value (Redis), wide-column (Cassandra), graph (Neo4j)
- ☐ Database internals: storage layouts (row vs. columnar), buffer pools, WAL

---

## Pillar 3 — Data Modeling & Warehousing Theory

- ◐ Dimensional modeling: facts, dimensions, grain *(theory partially absorbed; applies in Phase 1)*
- ◐ Star schema vs. snowflake schema *(designing in Phase 1)*
- ☐ Slowly Changing Dimensions (Type 1, 2, 3, 6)
- ☐ Data Vault 2.0 basics (hubs, links, satellites)
- ☐ One Big Table (OBT) and when it beats star schemas
- ★ Medallion architecture (bronze/silver/gold) — *applied as schemas in Phase 0; promoted via Phase 0 Q3 — 8.5/10*
- ☐ Data contracts and schema evolution
- ☐ Surrogate keys vs. natural keys

---

## Pillar 4 — Data Warehousing Platforms

- ☑ Snowflake: architecture (storage/compute separation, micro-partitions, virtual warehouses)
- ☐ Snowflake features: Time Travel, Zero-Copy Cloning, Streams, Tasks, Snowpipe
- ☑ Snowflake cost management: warehouse sizing, auto-suspend, resource monitors
- ★ Snowflake RBAC patterns: functional vs access roles *(promoted from ☑ via Phase 0 Q10 — 8.5/10; defended design choices clearly)*
- ☐ BigQuery fundamentals (slots, partitioning, clustering)
- ☐ Redshift fundamentals
- ☐ Databricks Lakehouse / Delta Lake: ACID on object storage, OPTIMIZE, Z-ORDER

---

## Pillar 5 — Data Pipelines & Orchestration

- ☐ Batch vs. streaming vs. micro-batch — trade-offs
- ☑ ETL vs. ELT — why ELT dominates modern stacks
- ◐ Apache Airflow: DAGs, operators, sensors, XComs, hooks, connections *(platform up; DAGs in Phase 4)*
- ☐ Airflow patterns: idempotent tasks, backfills, SLAs, dynamic DAGs
- ☐ dbt: models, refs, sources, tests, snapshots, macros, materializations
- ☐ dbt project structure and layering (staging / intermediate / marts)
- ☐ Prefect or Dagster (awareness of alternatives)

---

## Pillar 6 — Streaming & Event-Driven Systems

*(No items started — Project 2 territory.)*

- ☐ Kafka architecture: brokers, topics, partitions, consumer groups, offsets
- ☐ Producer/consumer guarantees: at-most-once, at-least-once, exactly-once
- ☐ Schema Registry and Avro for event evolution
- ☐ Kafka Connect and Kafka Streams
- ☐ Spark Structured Streaming
- ☐ Flink fundamentals (awareness)
- ☐ Change Data Capture (CDC): Debezium, log-based vs. query-based

---

## Pillar 7 — Cloud Computing

- ☐ Cloud fundamentals: IaaS vs. PaaS vs. SaaS, regions, AZs
- ★ IAM principles: least privilege, roles, policies, service accounts *(promoted from ☑ via Phase 0 Q10 — 8.5/10)*
- ☐ Networking basics: VPCs, subnets, security groups, private endpoints

### AWS

- ☑ S3: storage classes, lifecycle policies, versioning, event notifications *(versioning + bucket basics applied; lifecycle revisited in Project 3)*
- ☐ EC2, EMR (Spark on AWS)
- ☐ Glue: crawlers, jobs, Data Catalog
- ☐ Lambda for event-driven ETL
- ☐ Kinesis (Data Streams, Firehose)
- ☐ Redshift
- ☐ Step Functions for orchestration

### Azure

- ☐ ADLS Gen2, Blob Storage
- ☐ Azure Data Factory (pipelines, linked services, datasets)
- ☐ Synapse Analytics
- ☐ Event Hubs, Azure Functions
- ☐ Databricks on Azure

---

## Pillar 8 — Infrastructure & DevOps for Data

- ☑ Docker: images, containers, Dockerfiles, volumes, networks
- ☑ Docker Compose for local data stacks
- ☐ Kubernetes fundamentals: pods, deployments, services
- ☐ Terraform: providers, resources, state, modules
- ☐ CI/CD for data: GitHub Actions for dbt, Airflow DAGs, Terraform

---

## Pillar 9 — Data Quality, Governance & Observability

- ☐ Data quality dimensions: accuracy, completeness, consistency, timeliness, uniqueness, validity
- ☐ Testing with Great Expectations or dbt tests
- ☐ Data observability concepts (freshness, volume, schema, lineage, distribution)
- ☐ Data catalogs and lineage tools (DataHub, Amundsen, Unity Catalog)
- ☐ PII handling, GDPR/CCPA basics, column-level security, masking

---

## Pillar 10 — Systems Design & Trade-offs

- ☐ CAP theorem and PACELC
- ☐ Idempotency, exactly-once semantics, and why it's hard
- ☐ Partitioning and sharding strategies
- ☐ Caching layers and when they backfire
- ☐ Cost vs. latency vs. freshness trade-offs in pipeline design
- ☐ Designing for backfills and reprocessing from day one

---

## Gaps Log (Concept Gaps to Revisit)

Concepts where understanding is incomplete or imprecise. Updated as gaps are identified during synthesis drills and resolved through follow-up work.

| # | Concept | Identified | Status | Re-test plan |
|---|---|---|---|---|
| 1 | AWS STS detailed mechanics — credential triple names, session token semantics | Phase 0 (Q1 grading) | Open | Revisit Phase 2 ingestion |
| 2 | Snowflake RBAC user/role distinction | Phase 0 (debugging) | ✅ Closed | Locked in via hands-on debugging |
| 3 | Functional Role vs Access Role — labeling layers correctly | Phase 0 (interview Q) | Open | Revisit Phase 3 with new scenario |
| 4 | Three-layer authorization model in cross-cloud requests | Phase 0 (Q1 grading) | Open | Revisit Phase 2 |

---

## Phase Completion Log

| Phase | Completed | Synthesis drill avg | Key deliverable |
|---|---|---|---|
| 0 — Platform Foundation | 2026-04-29 | 7.45/10 (re-drill pending Q2/Q4/Q6) | Working Snowflake + AWS + Airflow stack on GitHub |
| 1 — Data Source & Exploration | — | — | — |
| 2 — Ingestion Layer | — | — | — |
| 3 — dbt Transformations | — | — | — |
| 4 — Orchestration with Airflow | — | — | — |
| 5 — CI/CD with GitHub Actions | — | — | — |
| 6 — Documentation & Polish | — | — | — |
