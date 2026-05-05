import duckdb

# Point at the Parquet file. DuckDB doesn't load it — just queries it directly.
result = duckdb.sql("""
    DESCRIBE SELECT *
    FROM 'data/raw/yellow_tripdata_2024-01.parquet'
""")

print(result)


result = duckdb.sql("""
    SELECT
        MIN(PULocationID) AS min_id,
        MAX(PULocationID) AS max_id,
        COUNT(DISTINCT PULocationID) AS distinct_count
    FROM 'data/raw/yellow_tripdata_2024-01.parquet'
""")
print(result)
