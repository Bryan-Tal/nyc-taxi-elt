import duckdb

# # Point at the Parquet file. DuckDB doesn't load it — just queries it directly.
# result = duckdb.sql("""
#     DESCRIBE SELECT *
#     FROM 'data/raw/yellow_tripdata_2024-01.parquet'
# """)

# print(result)


# result = duckdb.sql("""
#     SELECT store_and_fwd_flag, COUNT(*) AS trip_count
#     FROM 'data/raw/yellow_tripdata_2024-01.parquet'
#     GROUP BY store_and_fwd_flag
# """)
# print(result)



# for year in [2015, 2019, 2024]:
#     print(f"\n========== {year} ==========")
#     duckdb.sql(f"""
#         DESCRIBE SELECT *
#         FROM 'data/raw/yellow_tripdata_{year}-01.parquet'
#     """).show()
# Check 2015 congestion_surcharge values
# duckdb.sql("""
#     SELECT congestion_surcharge, COUNT(*) AS row_count
#     FROM 'data/raw/yellow_tripdata_2015-01.parquet'
#     GROUP BY congestion_surcharge
#     ORDER BY row_count DESC
# """).show()

# duckdb.sql("""
#     SELECT airport_fee, COUNT(*) AS row_count
#     FROM 'data/raw/yellow_tripdata_2015-01.parquet'
#     GROUP BY airport_fee
#     ORDER BY row_count DESC
# """).show()

duckdb.sql("""
    SELECT COUNT(*) AS rows_with_fractional_passenger_count
    FROM 'data/raw/yellow_tripdata_2019-01.parquet'
    WHERE passenger_count - FLOOR(passenger_count) != 0
""").show()