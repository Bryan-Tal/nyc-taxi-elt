# nyc-taxi-elt
Batch ELT Pipeline ingesting and processing data from NYC TLC commission.

**Stack:**
- Snowflake (ingests raw data)
- dbt (transforms data into star schema)
- Airflow (orchestrates daily runs)
- Docker (containerization)
- Github Actions (runs CI tests on every PR)
