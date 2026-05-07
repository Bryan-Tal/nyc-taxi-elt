"""
NYC Taxi Yellow Cab — Phase 1 Profiling Script

Purpose:
    Investigate the structure, types, and semantic stability of the NYC TLC
    Yellow Taxi dataset across multiple years before designing the warehouse
    schema. This script captures the queries from Phase 1 Steps 2 and 3:
    profiling a single month's schema and comparing schemas across years to
    surface type drift and semantic drift.

Why DuckDB:
    DuckDB queries Parquet files directly without loading them into memory.
    For ~3M-row monthly files, that's the difference between "instant" and
    "Pandas froze my laptop." The SQL syntax also closely mirrors Snowflake,
    so queries here transfer directly to the warehouse layer in Phase 2+.

Output:
    Schema descriptions, value distributions, and validation queries.
    Findings are documented in docs/design-doc.md §7 (Schema Evolution).

Phase: 1 (Data Source & Exploration), Steps 2 and 3
"""

import duckdb


# =============================================================================
# STEP 2 — First-pass profiling of January 2024 (the schema baseline)
# =============================================================================
# We start with a recent month because it represents the "current" schema —
# the one our STAGING dbt models will treat as canonical. Older years will be
# compared against this baseline in Step 3.

# Query 1: Show the schema (column names + types) without reading any data.
# DESCRIBE reads only the Parquet file's footer metadata — it doesn't scan
# the 3M rows. This is the analog of Pandas' df.info(), but doesn't require
# loading the file.
print("\n========== 2024 SCHEMA ==========")
duckdb.sql("""
    DESCRIBE SELECT *
    FROM 'data/raw/yellow_tripdata_2024-01.parquet'
""").show()


# Query 2: Distribution of store_and_fwd_flag values.
# This column flags trips where the meter buffered data locally before
# uploading (typically out-of-cell-range moments). We expect Y/N only and
# use this query to confirm cardinality is small enough to leave in the
# fact table as a degenerate dimension rather than building dim_store_fwd.
print("\n========== store_and_fwd_flag distribution ==========")
duckdb.sql("""
    SELECT store_and_fwd_flag, COUNT(*) AS trip_count
    FROM 'data/raw/yellow_tripdata_2024-01.parquet'
    GROUP BY store_and_fwd_flag
""").show()


# =============================================================================
# STEP 3 — Schema evolution investigation across years
# =============================================================================
# Goal: Determine whether ingestion needs simple append, type-tolerant
# casting, or full schema-evolution machinery. We sample three widely-spaced
# years to surface any drift pattern.
#
# 2015: pre-LocationID-system in original publication; well before any
#       congestion or airport fee policies existed
# 2019: just after congestion pricing launched (June 2019)
# 2024: current schema baseline


# Query 3: Compare schemas side-by-side across the three years.
# We loop because writing three near-identical queries would obscure the
# comparison. The .show() inside the loop prints each schema immediately.
#
# What we're looking for:
#   - Column adds/drops between years (would force schema-evolution logic)
#   - Type drift on the same column across years (would force casting layer)
#   - Renames (would require column-mapping in ingestion)
for year in [2015, 2019, 2024]:
    print(f"\n========== {year} SCHEMA ==========")
    duckdb.sql(f"""
        DESCRIBE SELECT *
        FROM 'data/raw/yellow_tripdata_{year}-01.parquet'
    """).show()


# Query 4: Verify semantic stability of congestion_surcharge in 2015.
#
# The schema-level inspection (Query 3) showed congestion_surcharge exists
# in 2015 — but that doesn't mean it had data. NYC's congestion pricing
# launched in 2019, so 2015 trips couldn't have been charged. This query
# asks: was the column NULL, zero, or something else for pre-policy data?
#
# This is the "Schema vs Semantics Stability" mental model in action:
# column existence and column meaning can diverge across time.
print("\n========== 2015 congestion_surcharge value distribution ==========")
duckdb.sql("""
    SELECT congestion_surcharge, COUNT(*) AS row_count
    FROM 'data/raw/yellow_tripdata_2015-01.parquet'
    GROUP BY congestion_surcharge
    ORDER BY row_count DESC
""").show()


# Query 5: Same semantic check for airport_fee in 2015.
#
# Airport fees became active in 2022. Like congestion_surcharge, the column
# exists in 2015's republished schema, but should have no real values.
# Confirming this NULL-ness shapes how downstream marts must filter when
# aggregating these columns over multi-year windows.
print("\n========== 2015 airport_fee value distribution ==========")
duckdb.sql("""
    SELECT airport_fee, COUNT(*) AS row_count
    FROM 'data/raw/yellow_tripdata_2015-01.parquet'
    GROUP BY airport_fee
    ORDER BY row_count DESC
""").show()


# Query 6: Validate that DOUBLE → BIGINT cast is safe for passenger_count.
#
# In 2019, passenger_count is stored as DOUBLE; in 2015 and 2024 it's BIGINT.
# Our STAGING layer will cast the 2019 DOUBLE values to BIGINT — but only
# if every value is integer-shaped (e.g., 2.0, not 2.5). A taxi meter
# shouldn't allow fractional passengers, but trust-but-verify: confirm with
# a query before committing to the cast direction.
#
# Expected result: 0 rows. Anything > 0 means we'd lose data on cast and
# the architectural decision needs revisiting.
print("\n========== 2019 fractional passenger_count check ==========")
duckdb.sql("""
    SELECT COUNT(*) AS rows_with_fractional_passenger_count
    FROM 'data/raw/yellow_tripdata_2019-01.parquet'
    WHERE passenger_count - FLOOR(passenger_count) != 0
""").show()