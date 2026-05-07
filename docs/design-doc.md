# NYC Taxi ELT — Dimensional Model Design

> **Status:** Phase 1 schema design complete. Schema evolution investigation pending (Step 3).
> **Last updated:** Phase 1 (Data Source & Exploration)
> **Author:** Bryan Talavera

---

## 1. Project Context

This project ingests NYC Taxi & Limousine Commission (TLC) trip records into a Snowflake-based analytical warehouse using an ELT pattern (Python → S3 → Snowflake → dbt → marts). The dimensional model in this document is the **target schema** that downstream marts and analytics queries will run against.

The model is intentionally simple — one fact table, five dimensions — but the design decisions reflect production-grade reasoning about grain, SCD types, role-playing dimensions, and analytical trade-offs.

---

## 2. Source Data

| Property | Value |
|---|---|
| **Publisher** | NYC Taxi & Limousine Commission |
| **URL pattern** | `https://d37ci6vzurychx.cloudfront.net/trip-data/{type}_tripdata_{YYYY}-{MM}.parquet` |
| **Format** | Parquet (columnar, compressed) |
| **Partitioning** | One file per (taxi type, year, month) |
| **Update cadence** | Monthly, with ~3 month lag for data quality finalization |
| **Initial scope** | Yellow Taxi only (highest volume, longest history, best documentation) |
| **Pilot dataset** | `yellow_tripdata_2024-01.parquet` (~3M rows, ~50MB) |

**Note on naming convention:** The TLC's predictable filename pattern (`{type}_tripdata_{YYYY}-{MM}`) enables a single Python function to construct URLs for any month/year, which simplifies Phase 2 ingestion significantly. This is a reusable principle: predictable naming is design surface for automation.

---

## 3. Target Schema

```mermaid
erDiagram
    fct_trips }o--|| dim_vendor : "vendor_sk"
    fct_trips }o--|| dim_location : "pickup_location_sk"
    fct_trips }o--|| dim_location : "dropoff_location_sk"
    fct_trips }o--|| dim_ratecode : "ratecode_id"
    fct_trips }o--|| dim_payment_type : "payment_type_id"
    fct_trips }o--|| dim_date : "pickup_date_key"
    fct_trips }o--|| dim_date : "dropoff_date_key"

    fct_trips {
        int trip_id PK
        int vendor_sk FK
        int pickup_location_sk FK
        int dropoff_location_sk FK
        int ratecode_id FK
        int payment_type_id FK
        int pickup_date_key FK
        int dropoff_date_key FK
        timestamp tpep_pickup_datetime
        timestamp tpep_dropoff_datetime
        int passenger_count "degenerate"
        varchar store_and_fwd_flag "degenerate"
        double trip_distance "measure"
        double fare_amount "measure"
        double tip_amount "measure"
        double tolls_amount "measure"
        double total_amount "measure"
    }

    dim_vendor {
        int vendor_sk PK
        int vendor_id NK
        varchar vendor_name
        date valid_from
        date valid_to
        boolean is_current
    }

    dim_location {
        int location_sk PK
        int location_id NK
        varchar borough
        varchar zone
        varchar service_zone
        date valid_from
        date valid_to
        boolean is_current
    }

    dim_ratecode {
        int ratecode_id PK
        varchar description
        boolean is_airport_rate
    }

    dim_payment_type {
        int payment_type_id PK
        varchar payment_name
        boolean is_electronic
    }

    dim_date {
        int date_key PK
        date full_date
        int year
        int quarter
        int month
        int day_of_month
        int day_of_week
        varchar day_name
        boolean is_weekend
        boolean is_holiday
        varchar holiday_name
    }
```

**Pattern:** Star schema. Fact at center, dimensions one join away. `dim_location` and `dim_date` are role-playing — referenced twice each (pickup vs. dropoff).

---

## 4. Grain

> **`fct_trips` grain: one row per completed taxi trip.**

Evidence supporting this grain:
- Each row records a single trip event (one pickup, one dropoff)
- Per-trip measurements (`fare_amount`, `tip_amount`, `trip_distance`) align with one event
- No multi-trip aggregations or pre-rollups embedded in the source

**What this grain supports:**
- Per-trip metrics (avg fare, longest trip, most expensive route)
- Aggregations to higher levels (per day, per zone, per vendor) via `GROUP BY`
- Time-series analysis at any granularity ≥ trip-level

**What this grain does NOT support:**
- Per-passenger analysis (multiple passengers share one trip; no per-passenger detail)
- Per-segment route analysis (one row covers the entire trip; no waypoints)
- Per-driver-shift analysis (no driver or shift identifiers in source)

A future fact table at a different grain (e.g., `fct_trip_segments` from a GPS feed) could complement this without replacing it.

---

## 5. Modeling Decisions

### 5.1 Star vs. Snowflake Schema → Star

Modern columnar warehouses (Snowflake, BigQuery, Redshift) compress repeated dimension values efficiently, removing the storage advantage that historically motivated snowflake schemas. The query simplicity of star (one join per dimension, no sub-dimension navigation) is the dominant analytical advantage and the reason star is the default choice for analytical warehouses today.

For our scale (~260 zones, ~5 boroughs), the storage delta from normalizing `dim_location` would be measured in kilobytes while every borough-level filter would gain an extra join. Cost-benefit clearly favors flat.

### 5.2 Column Classifications

Each non-measure column was evaluated against three tests: cardinality, stability, descriptive richness. Failing any pushes the column toward a degenerate-dimension or measure classification.

| Column | Classification | Reasoning |
|---|---|---|
| `VendorID` | **Dimension table** (`dim_vendor`) | Real company entities; vendor name and metadata are useful in reports |
| `PULocationID` / `DOLocationID` | **Dimension table** (`dim_location`, role-playing) | 260 distinct values; rich attributes (borough, zone, service zone) |
| `RatecodeID` | **Dimension table** (`dim_ratecode`) | 6 values, but each rate type has meaningful attributes (description, airport flag) |
| `payment_type` | **Dimension table** (`dim_payment_type`) | 6 values with category attributes (electronic vs cash) |
| `passenger_count` | **Degenerate dimension** | Tiny cardinality; no attributes worth attaching; aggregated frequently |
| `store_and_fwd_flag` | **Degenerate dimension** | Boolean Y/N; no descriptive richness |
| `tpep_pickup_datetime` / `tpep_dropoff_datetime` | **References to `dim_date`** + preserved for sub-day analysis | Date attributes via dimension; raw timestamp retained for hour/minute precision |
| `fare_amount`, `tip_amount`, `tolls_amount`, `total_amount`, `trip_distance`, etc. | **Pure measures** | Continuous numeric values aggregated in queries |

### 5.3 SCD Type Per Dimension

SCD type is determined by what *changes*, not by what's *added*. Adding new dimension rows (new payment types, new locations) is a routine INSERT, not an SCD operation. SCD types address **changes to existing rows' attributes**.

| Dimension | SCD Type | Reasoning |
|---|---|---|
| `dim_location` | **Type 2** | Zone names can change (e.g., NYC redrawing zones). Historical accuracy matters for long-history trip analysis. |
| `dim_vendor` | **Type 2** | Vendor names change over years (acquisitions, rebrands). Multi-decade analysis demands historical fidelity. |
| `dim_ratecode` | **Type 1** | Rate code description changes are cosmetic (e.g., "JFK" → "JFK Airport"). Semantic meaning unchanged; overwriting is acceptable. |
| `dim_payment_type` | **Type 1** | Payment label changes are cosmetic. New payment types (e.g., crypto) would be new INSERTs, not SCD changes. |
| `dim_date` | **Type 0** | Calendar attributes are fixed once defined. 2024-01-15 is permanently a Monday. |

### 5.4 Surrogate Keys (Type 2 Dimensions Only)

Type 2 dimensions (`dim_location`, `dim_vendor`) require surrogate keys because the natural key (`location_id`, `vendor_id`) appears in multiple rows — one per version. The fact table's foreign key must point to the surrogate (`location_sk`) so each fact row matches exactly the dimension version active at the event time.

Type 1 and Type 0 dimensions could technically use natural keys, but adopting surrogate keys universally provides:
- Consistent fact-table FK pattern across all dimensions
- Source-system independence (if the TLC renumbers payment types, surrogates are stable)
- Multi-source isolation (future Boston taxi data with overlapping IDs wouldn't collide)

### 5.5 Date Dimension Strategy

`dim_date` is **generated programmatically** rather than ingested from a source. Calendar concepts vary by organization (fiscal periods, holidays, business-day definitions) — there's no authoritative external "calendar file" to ingest. Generation is also more flexible: extending the range from 2030 to 2040 is one parameter change, not a data-source negotiation.

Date keys are stored as `INT YYYYMMDD` rather than `DATE` types. This makes joins faster (integer comparison), human-readable (`20240115` is parseable at a glance), and naturally sortable.

### 5.6 Role-Playing Dimensions

Two dimensions are referenced multiple times by `fct_trips`:

- **`dim_location`** — pickup vs dropoff. Same physical table; SQL aliases (`pu`, `do`) disambiguate the role.
- **`dim_date`** — pickup date vs dropoff date. Most trips share the date, but airport pickups and overnight rides span dates.

Storing two physical copies would be wasteful — the dimension's data is identical regardless of role. Aliased joins are the standard pattern.

---

## 6. Trade-offs Considered

| Decision | Alternative considered | Why we chose what we chose |
|---|---|---|
| Star vs snowflake | Normalize `dim_location` into `dim_borough`, `dim_zone`, `dim_service_zone` | Storage savings negligible; query complexity increase real |
| Type 2 for `dim_location` | Type 1 (overwrite) | Multi-year trip analysis requires historical zone names |
| Type 1 for `dim_payment_type` | Type 2 (history) | Payment label changes are cosmetic; SCD2 overhead unjustified |
| Generate `dim_date` | Ingest from external file | No authoritative external calendar exists; generation is more flexible |
| Surrogate keys universally | Natural keys for Type 1/Type 0 | Consistency, source-system independence outweigh trivial storage cost |
| Yellow Taxi first | All four TLC datasets simultaneously | Manage scope; Yellow has most consistent schema across years |

---

## 7. Open Questions

These are deliberately unresolved at the close of Phase 1 schema design and will be addressed in subsequent steps:

- **Schema evolution across years** — pending Step 3 investigation. Specifically: was `Airport_fee` always present, or added in 2024? Did `congestion_surcharge` exist before NYC's congestion-pricing legislation? Answers affect whether ingestion needs schema-tolerance logic.
- **Trip duration** — derived from `tpep_dropoff_datetime - tpep_pickup_datetime`. Where to compute: in the fact table at load time (idempotent, denormalized) or in a derived view (DRY but adds query overhead). Decision in Phase 3.
- **Late-arriving facts** — TLC publishes monthly with corrections occasionally backfilled. Pipeline needs idempotent loads with merge semantics. Detailed in Phase 3.
- **Multi-taxi-type expansion** — Green / FHV / FHVHV have different schemas. Future state may union into one fact table or maintain parallel facts. Not a Phase 1 concern.

---

## 8. Future Work (Phase 2+)

- **Phase 2:** Python ingestion → S3 → Snowflake `RAW` schema via storage integration (Phase 0 foundation)
- **Phase 3:** dbt models transforming `RAW` → `STAGING` → `MARTS`, with SCD2 logic via `snapshots` for `dim_location` and `dim_vendor`
- **Phase 4:** Airflow DAG orchestrating monthly ingestion and dbt builds
- **Phase 5:** GitHub Actions CI/CD for dbt tests and SQL linting
- **Phase 6:** Documentation polish, dbt docs site, dashboard against marts

---

## Appendix A — Naming Conventions

| Object type | Convention | Example |
|---|---|---|
| Fact tables | `fct_<entity>` | `fct_trips` |
| Dimension tables | `dim_<entity>` | `dim_location` |
| Surrogate keys | `<entity>_sk` (INT) | `location_sk`, `vendor_sk` |
| Natural keys | `<entity>_id` (matches source) | `location_id`, `vendor_id` |
| Date keys | `<role>_date_key` (INT YYYYMMDD) | `pickup_date_key` |
| Snowflake schemas | UPPERCASE | `RAW`, `STAGING`, `MARTS`, `SNAPSHOTS` |
| dbt models | `snake_case` | `stg_yellow_trips`, `dim_location` |

---

## Appendix B — Decision Log

| # | Decision | Date | Rationale |
|---|---|---|---|
| 1 | Yellow Taxi as initial scope | Phase 1 | Highest volume, longest history, most stable schema |
| 2 | Star schema (not snowflake) | Phase 1 | Modern columnar warehouses favor query simplicity over storage normalization |
| 3 | Per-trip grain | Phase 1 | Aligns with source data structure; aggregatable to higher levels |
| 4 | SCD2 for location, vendor | Phase 1 | Long-history analytical warehouse requires historical fidelity |
| 5 | Generate `dim_date` | Phase 1 | No authoritative external calendar; flexibility outweighs ingestion |
| 6 | Surrogate keys universally | Phase 1 | Pattern consistency; source-system independence |
