# NYC Taxi ELT — Data Dictionary

> **Audience:** Anyone querying the warehouse (analysts, engineers, future you).
> **Purpose:** Column-level reference for every table — what each column means, its type, expected values, and edge cases.
> **Companion:** [`design-doc.md`](design-doc.md) explains *why* the schema looks this way.
> **Last updated:** Phase 1 (Data Source & Exploration)

---

## Table of Contents

- [`fct_trips`](#fct_trips) — Fact table
- [`dim_vendor`](#dim_vendor) — Vendor dimension (SCD2)
- [`dim_location`](#dim_location) — Taxi zone dimension (SCD2, role-playing)
- [`dim_ratecode`](#dim_ratecode) — Rate code dimension (SCD1)
- [`dim_payment_type`](#dim_payment_type) — Payment type dimension (SCD1)
- [`dim_date`](#dim_date) — Date dimension (SCD0, role-playing)

---

## `fct_trips`

| Property | Value |
|---|---|
| **Schema** | `MARTS` |
| **Type** | Fact table |
| **Grain** | One row per completed taxi trip |
| **Source** | TLC Yellow Taxi monthly Parquet files |
| **Refresh** | Monthly (with backfill capability for late-arriving corrections) |
| **Approximate volume** | ~3M rows / month, ~36M rows / year |

### Columns

| # | Column | Type | Nullable | Source | Description |
|---|---|---|---|---|---|
| 1 | `trip_id` | INT (surrogate) | No | Generated | Surrogate primary key. Unique per trip. |
| 2 | `vendor_sk` | INT | No | `dim_vendor` | FK to `dim_vendor` — which vendor processed this trip |
| 3 | `pickup_location_sk` | INT | No | `dim_location` | FK to `dim_location` — pickup zone (role: pickup) |
| 4 | `dropoff_location_sk` | INT | No | `dim_location` | FK to `dim_location` — dropoff zone (role: dropoff) |
| 5 | `ratecode_id` | INT | Yes | `dim_ratecode` | FK to `dim_ratecode`. NULL when source value unmapped. |
| 6 | `payment_type_id` | INT | Yes | `dim_payment_type` | FK to `dim_payment_type` |
| 7 | `pickup_date_key` | INT | No | `dim_date` | FK to `dim_date`, format YYYYMMDD (role: pickup) |
| 8 | `dropoff_date_key` | INT | No | `dim_date` | FK to `dim_date`, format YYYYMMDD (role: dropoff) |
| 9 | `tpep_pickup_datetime` | TIMESTAMP | No | source | Trip start timestamp. Preserved for sub-day analysis. |
| 10 | `tpep_dropoff_datetime` | TIMESTAMP | No | source | Trip end timestamp. Preserved for sub-day analysis. |
| 11 | `passenger_count` | INT | Yes | source | Degenerate dimension. Number of passengers (typically 1–6). NULL ~3% of rows. |
| 12 | `store_and_fwd_flag` | VARCHAR(1) | Yes | source | Degenerate dimension. `Y` = trip data buffered locally before forwarding (out-of-cell-range), `N` = sent immediately. |
| 13 | `trip_distance` | DOUBLE | Yes | source | Measure. Trip distance in miles. Edge cases: 0 (immediate cancel), >100 (data error suspected). |
| 14 | `trip_duration_minutes` | DOUBLE | Yes | derived | Measure. Computed from `dropoff - pickup` at load time. Filter outliers (negative, >24h) downstream. |
| 15 | `fare_amount` | DOUBLE | Yes | source | Measure. Base fare before extras. Includes time-and-distance pricing. |
| 16 | `extra` | DOUBLE | Yes | source | Measure. Miscellaneous extras (rush hour, overnight surcharges). |
| 17 | `mta_tax` | DOUBLE | Yes | source | Measure. NYC MTA tax. Typically $0.50 flat. |
| 18 | `tip_amount` | DOUBLE | Yes | source | Measure. Tip amount. Credit-card tips only — cash tips are not recorded. |
| 19 | `tolls_amount` | DOUBLE | Yes | source | Measure. Total tolls paid during trip. |
| 20 | `improvement_surcharge` | DOUBLE | Yes | source | Measure. NYC fare improvement surcharge. |
| 21 | `congestion_surcharge` | DOUBLE | Yes | source | Measure. NYC congestion fee. May be NULL for trips before NYC's congestion pricing introduction. |
| 22 | `airport_fee` | DOUBLE | Yes | source | Measure. Applied at JFK/LGA pickups. May be NULL for pre-2024 data. |
| 23 | `total_amount` | DOUBLE | Yes | source | Measure. Sum of fare components. May not equal sum of parts due to rounding. |

### Notes & gotchas

- **Tip recording bias:** Cash tips are not captured in `tip_amount`. Analyses comparing tip rates by `payment_type` will systematically understate cash tips. Best practice: filter to credit-card payments before computing average tip rates.
- **Date key vs timestamp:** Both are present. Use `pickup_date_key` for joins to `dim_date`; use `tpep_pickup_datetime` for hour/minute precision.
- **Negative measures:** Some `fare_amount` and `total_amount` values are negative — these are dispute/refund records. Filter or aggregate carefully.
- **Schema evolution across years (verified Step 3):** Schema is column-stable from 2015–2024 (same 19 columns), but type drift exists. `congestion_surcharge` (added 2019 policy) and `Airport_fee` (added 2022 policy) are **NULL for all pre-policy data** — analyses must filter by date before aggregating. Pipeline handles type drift via `TRY_CAST` in STAGING; no schema-evolution framework needed. See `design-doc.md` §7 for full type-drift table.

---

## `dim_vendor`

| Property | Value |
|---|---|
| **Schema** | `MARTS` |
| **Type** | Dimension table |
| **SCD type** | **Type 2** (history preserved with valid_from / valid_to) |
| **Source** | Manually maintained; vendor metadata from TLC documentation |
| **Refresh** | Rare (only when vendor names change) |
| **Approximate size** | <10 rows |

### Columns

| Column | Type | Nullable | Description |
|---|---|---|---|
| `vendor_sk` | INT | No | Surrogate primary key. Unique per (vendor_id, version). |
| `vendor_id` | INT | No | Natural key. From source. Values: 1, 2 (occasionally others). |
| `vendor_name` | VARCHAR | No | Full vendor company name (e.g., "Creative Mobile Technologies, LLC"). |
| `vendor_short_name` | VARCHAR | Yes | Abbreviated name for compact display (e.g., "CMT"). |
| `valid_from` | DATE | No | Start of validity window for this version. |
| `valid_to` | DATE | No | End of validity window. `9999-12-31` for current row. |
| `is_current` | BOOLEAN | No | Convenience flag. TRUE for the active row per natural key. |

### Known vendor IDs

| `vendor_id` | Vendor name |
|---|---|
| 1 | Creative Mobile Technologies, LLC |
| 2 | VeriFone Inc. |

---

## `dim_location`

| Property | Value |
|---|---|
| **Schema** | `MARTS` |
| **Type** | Dimension table |
| **SCD type** | **Type 2** (history preserved) |
| **Role-playing** | Yes — referenced as both pickup and dropoff in `fct_trips` |
| **Source** | TLC Taxi Zone Lookup CSV |
| **Refresh** | Rare (when TLC redraws or renames zones) |
| **Approximate size** | ~265 active rows × ~1.2 versions = ~320 total rows over time |

### Columns

| Column | Type | Nullable | Description |
|---|---|---|---|
| `location_sk` | INT | No | Surrogate primary key. Unique per (location_id, version). |
| `location_id` | INT | No | Natural key from TLC. Range: 1–265. |
| `borough` | VARCHAR | No | One of: Manhattan, Brooklyn, Queens, Bronx, Staten Island, EWR, Unknown |
| `zone` | VARCHAR | No | TLC zone name (e.g., "Midtown Center", "JFK Airport"). |
| `service_zone` | VARCHAR | Yes | Service category: Yellow Zone, Boro Zone, Airports, EWR, N/A. |
| `valid_from` | DATE | No | Start of validity window. |
| `valid_to` | DATE | No | End of validity window. `9999-12-31` for current row. |
| `is_current` | BOOLEAN | No | TRUE for the active row per natural key. |

### Notes

- **Special LocationID 264 / 265:** "Unknown" zones used when source data lacks a clear pickup/dropoff location.
- **Role-playing usage:** Joins must alias the dimension distinctly per role (e.g., `JOIN dim_location pu` vs `JOIN dim_location do`).
- **Type 2 join:** Fact table joins via surrogate (`location_sk`), not natural key, to ensure each fact row matches the version active at the trip's date.

---

## `dim_ratecode`

| Property | Value |
|---|---|
| **Schema** | `MARTS` |
| **Type** | Dimension table |
| **SCD type** | **Type 1** (overwrite — descriptions are cosmetic) |
| **Source** | TLC documentation (manual seed) |
| **Refresh** | Rare |
| **Approximate size** | ~6 rows |

### Columns

| Column | Type | Nullable | Description |
|---|---|---|---|
| `ratecode_id` | INT | No | Primary key. Matches source `RatecodeID`. |
| `description` | VARCHAR | No | Human-readable rate type. |
| `is_airport_rate` | BOOLEAN | No | TRUE for JFK and Newark flat-rate codes. |

### Known rate codes

| `ratecode_id` | Description | `is_airport_rate` |
|---|---|---|
| 1 | Standard rate | FALSE |
| 2 | JFK | TRUE |
| 3 | Newark | TRUE |
| 4 | Nassau or Westchester | FALSE |
| 5 | Negotiated fare | FALSE |
| 6 | Group ride | FALSE |
| 99 | (Unknown / source error) | FALSE |

---

## `dim_payment_type`

| Property | Value |
|---|---|
| **Schema** | `MARTS` |
| **Type** | Dimension table |
| **SCD type** | **Type 1** (overwrite) |
| **Source** | TLC documentation (manual seed) |
| **Refresh** | Rare |
| **Approximate size** | ~6 rows |

### Columns

| Column | Type | Nullable | Description |
|---|---|---|---|
| `payment_type_id` | INT | No | Primary key. Matches source `payment_type`. |
| `payment_name` | VARCHAR | No | Human-readable payment method. |
| `is_electronic` | BOOLEAN | No | TRUE for credit-card and electronic payments; FALSE for cash. |

### Known payment types

| `payment_type_id` | Payment name | `is_electronic` |
|---|---|---|
| 1 | Credit card | TRUE |
| 2 | Cash | FALSE |
| 3 | No charge | FALSE |
| 4 | Dispute | FALSE |
| 5 | Unknown | FALSE |
| 6 | Voided trip | FALSE |

### Note on tip analysis

`tip_amount` in `fct_trips` only captures credit-card tips. Cash tips are systematically absent. Use `is_electronic = TRUE` to filter when computing tip-rate metrics.

---

## `dim_date`

| Property | Value |
|---|---|
| **Schema** | `MARTS` |
| **Type** | Dimension table |
| **SCD type** | **Type 0** (static — calendar attributes are fixed) |
| **Role-playing** | Yes — referenced as `pickup_date_key` and `dropoff_date_key` in `fct_trips` |
| **Source** | Generated programmatically (no external file) |
| **Refresh** | Annual (extend forward) |
| **Approximate size** | ~8,000 rows (covers 2009–2030) |

### Columns

| Column | Type | Nullable | Description |
|---|---|---|---|
| `date_key` | INT | No | Primary key. Format YYYYMMDD (e.g., `20240115`). |
| `full_date` | DATE | No | Native DATE for date arithmetic. |
| `year` | INT | No | 4-digit year. |
| `quarter` | INT | No | 1–4. |
| `month` | INT | No | 1–12. |
| `month_name` | VARCHAR | No | "January", "February", etc. |
| `day_of_month` | INT | No | 1–31. |
| `day_of_week` | INT | No | 0=Sunday … 6=Saturday (ISO standard varies; document choice in dbt model). |
| `day_name` | VARCHAR | No | "Monday", "Tuesday", etc. |
| `is_weekend` | BOOLEAN | No | TRUE for Saturday and Sunday. |
| `is_holiday` | BOOLEAN | No | TRUE if date is a US federal holiday. |
| `holiday_name` | VARCHAR | Yes | Holiday name when `is_holiday = TRUE`. |
| `fiscal_quarter` | VARCHAR | No | Format "FYYYQN" (e.g., "FY24Q1"). Fiscal year start configurable. |
| `fiscal_year` | INT | No | Fiscal year integer. |

### Generation strategy

`dim_date` is built by a SQL or Python script that emits one row per date in the desired range. Logic for `is_holiday`, fiscal-period calculations, etc. lives in the generator code — not in fact-table queries. This keeps calendar logic centralized and consistent across all reports.

### Role-playing usage

```sql
SELECT
    pickup_date.day_name AS pickup_day,
    dropoff_date.day_name AS dropoff_day,
    COUNT(*) AS trip_count
FROM fct_trips f
JOIN dim_date pickup_date  ON f.pickup_date_key = pickup_date.date_key
JOIN dim_date dropoff_date ON f.dropoff_date_key = dropoff_date.date_key
WHERE pickup_date.year = 2024
GROUP BY pickup_day, dropoff_day;
```

---

## Cross-Cutting Notes

### NULL handling conventions

- Foreign keys to required dimensions (`vendor_sk`, `pickup_location_sk`, `dropoff_location_sk`, date keys) are **NOT NULL**. Source rows with missing values get a sentinel "Unknown" dimension row rather than NULL.
- Optional measures and degenerate dimensions allow NULL (e.g., `passenger_count`, `airport_fee` for pre-2024 data).
- Tests in `dbt` should enforce these constraints at the model layer.

### Surrogate key conventions

- All surrogate keys are `INT`, generated by dbt's `dbt_utils.generate_surrogate_key` macro or via Snowflake's identity columns.
- Sentinel values: `-1` for "Unknown" (for FK to a sentinel "Unknown" dimension row).

### Data quality rules

A non-exhaustive list of rules dbt tests should enforce in Phase 3:

| Rule | Why |
|---|---|
| `trip_distance >= 0` | Negative distance is data error |
| `tpep_dropoff_datetime > tpep_pickup_datetime` | Dropoff after pickup |
| `fare_amount` finite (not NaN/Inf) | Source quality check |
| All FK keys referentially valid | Star schema integrity |
| `total_amount` ≈ sum of fare components (within tolerance) | Internal consistency |

These are codified in the project's `dbt` test suite in Phase 3.
