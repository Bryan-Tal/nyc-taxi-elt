import duckdb

# Point at the Parquet file. DuckDB doesn't load it — just queries it directly.
result = duckdb.sql("""
    DESCRIBE SELECT *
    FROM 'data/raw/yellow_tripdata_2024-01.parquet'
""")

print(result)


result = duckdb.sql("""
    SELECT store_and_fwd_flag, COUNT(*) AS trip_count
    FROM 'data/raw/yellow_tripdata_2024-01.parquet'
    GROUP BY store_and_fwd_flag
""")
print(result)
