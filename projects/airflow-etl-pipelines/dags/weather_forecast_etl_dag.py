# Standard library imports
from datetime import datetime, timedelta, timezone, date
import pandas as pd
import os
import json

# Airflow imports with fallback for local testing
try:
    from airflow.decorators import dag, task
    from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
except Exception:
    # no-op decorators for local import/testing when Airflow isn't present
    def dag(*args, **kwargs):
        def _decor(fn):
            return fn
        return _decor

    def task(*args, **kwargs):
        def _decor(fn):
            return fn
        return _decor


# ============================================================================
# CONFIGURATION SECTION - Edit these values as needed
# ============================================================================

# Target earliest date to fetch weather data from
TARGET_START_DATE = date(2024, 11, 1)

# Track the earliest date we've fetched (will be updated by the DAG)
# Set to None to start fresh, or provide a date string like "2024-11-01"
EARLIEST_FETCHED_DATE = "2024-11-01"  # This will be updated automatically

# City configuration: List of cities with coordinates
# Each entry is a dict with: name, latitude, longitude
CITIES = [
    {"name": "New York-NY", "latitude": 40.712776, "longitude": -74.005974},
    {"name": "Los Angeles-CA", "latitude": 34.052235, "longitude": -118.243683},
    {"name": "Chicago-IL", "latitude": 41.878113, "longitude": -87.629799},
    {"name": "Houston-TX", "latitude": 29.760427, "longitude": -95.369804},
    {"name": "Phoenix-AZ", "latitude": 33.448376, "longitude": -112.074036},
    {"name": "Philadelphia-PA", "latitude": 39.952583, "longitude": -75.165222},
    {"name": "San Antonio-TX", "latitude": 29.424122, "longitude": -98.493629},
    {"name": "San Diego-CA", "latitude": 32.715736, "longitude": -117.161087},
    {"name": "Dallas-TX", "latitude": 32.776665, "longitude": -96.796988},
    {"name": "San Jose-CA", "latitude": 37.338207, "longitude": -121.88633},
]

# ============================================================================


@dag(
    dag_id="final_weather_dagV2",
    # Run every Sunday at 12:00 PM (noon) Mountain Time (19:00 UTC)
    schedule="0 19 * * 0",
    start_date=datetime(2025, 10, 26, 18, 0, tzinfo=timezone.utc),
    catchup=True,
    description="Complete weather ETL: Extract from OpenMeteo API → Transform → Load to Snowflake",
    tags=["weather", "etl", "snowflake", "openmeteo"],
    default_args={
        "owner": "airflow",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    doc_md="""
    ## Weather ETL Pipeline v2 (Airflow 3.0)
    
    This DAG performs a complete ETL process for weather data:
    
    1. **Extract**: Fetches weather data from OpenMeteo API for configured cities
    2. **Transform**: Structures data into fact and dimension tables
    3. **Load**: Upserts data into Snowflake using MERGE statements
    
    ### Configuration
    Edit the configuration variables at the top of this file to customize:
    - Target start date for historical data
    - List of cities with coordinates
    
    ### Schedule
    Runs weekly on Sundays at 12:00 UTC
    """,
)
def dev_weather_etl_pipeline_v2():
    """
    Complete ETL pipeline for weather data:
    1. Extract: Fetch weather data from OpenMeteo API for multiple cities
    2. Transform: Clean and structure data into DataFrames
    3. Load: Upsert data into Snowflake tables
    """
    
    @task(
        retries=3,
        retry_delay=timedelta(minutes=2),
        execution_timeout=timedelta(minutes=30),
    )
    def extract(dag_run=None):
        """
        Extract weather data from OpenMeteo API for configured cities.
        Fetches historical data from TARGET_START_DATE to yesterday.
        Dates with existing data in Snowflake will be replaced by MERGE statement.
        """
        # Import OpenMeteo libraries
        from openmeteopy import OpenMeteo
        from openmeteopy.daily import DailyHistorical
        from openmeteopy.options import HistoricalOptions
        import time
        import re
        from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
        
        # Fetch data from TARGET_START_DATE to yesterday
        today = date.today()
        fetch_start_date = TARGET_START_DATE
        fetch_end_date = today - timedelta(days=1)
        
        print(f"Fetching data from {fetch_start_date} to {fetch_end_date}")
        
        # Create a single date range for the entire period
        date_ranges = [(fetch_start_date, fetch_end_date)]
        print(f"Will fetch 1 date range: {fetch_start_date} to {fetch_end_date}")
        print(f"This covers approximately {(fetch_end_date - fetch_start_date).days} days")
        
        # Fetch data for missing date ranges and store in memory
        all_dataframes = []
        daily = DailyHistorical()
        
        # Helper to fetch with retries
        def fetch_with_retries(opts, max_retries=6, backoff_base=2.0):
            attempt = 0
            while attempt < max_retries:
                attempt += 1
                try:
                    meteod = OpenMeteo(opts, None, daily.all())
                    dfd = meteod.get_pandas()
                    return dfd
                except BaseException as e:
                    wait = backoff_base * (2 ** (attempt - 1))
                    error_msg = str(e)[:80]
                    print(f"Attempt {attempt}/{max_retries} failed: {error_msg}")
                    if attempt < max_retries:
                        print(f"Retrying in {wait:.1f}s...")
                        time.sleep(wait)
                    else:
                        print(f"Giving up after {max_retries} attempts for this city")
                        return None
        
        for range_start, range_end in date_ranges:
            print(f"\nFetching date range: {range_start} to {range_end}")
            
            # Fetch data for each city in this date range
            for idx, city_config in enumerate(CITIES, start=1):
                city_name = city_config["name"]
                latitude = city_config["latitude"]
                longitude = city_config["longitude"]
                
                print(f"Processing #{idx}: {city_name} (lat={latitude}, long={longitude})")
                
                # Set up fetch options
                options = HistoricalOptions(
                    latitude=latitude,
                    longitude=longitude,
                    start_date=range_start,
                    end_date=range_end,
                )
                
                dfd = fetch_with_retries(options, max_retries=6, backoff_base=2.0)
                
                if dfd is None:
                    print(f"Skipping city #{idx} due to repeated fetch errors")
                else:
                    try:
                        print(f"Retrieved {len(dfd)} rows for {city_name}")
                    except Exception:
                        pass
                    
                    # Add metadata columns to DataFrame
                    dfd = dfd.copy()
                    dfd["city_idx"] = idx
                    dfd["city_name"] = city_name
                    dfd["latitude"] = latitude
                    dfd["longitude"] = longitude
                    dfd["source_file"] = f"API_{range_start}_{range_end}_{city_name}"
                    
                    all_dataframes.append(dfd)
                    print(f"Added {len(dfd)} rows to DataFrame for {city_name}")
                
                # Increased rate limiting to be respectful to the API
                time.sleep(3.0)
        
        # Concatenate all DataFrames into one combined DataFrame
        if not all_dataframes:
            print("No data was fetched. Returning empty status.")
            return {"status": "no_data", "message": "No data fetched from API"}
        
        combined_df = pd.concat(all_dataframes, axis=0, ignore_index=False)
        print(f"\n{'='*60}")
        print(f"EXTRACT COMPLETE!")
        print(f"{'='*60}")
        print(f"Combined DataFrame has {len(combined_df)} rows and {len(combined_df.columns)} columns")
        print(f"Date range: {fetch_start_date} to {fetch_end_date}")
        print(f"Number of cities: {len(CITIES)}")
        print(f"Expected rows: {len(CITIES)} cities × {(fetch_end_date - fetch_start_date).days + 1} days = {len(CITIES) * ((fetch_end_date - fetch_start_date).days + 1)}")
        print(f"\nColumn names: {list(combined_df.columns)}")
        print(f"\nDataFrame shape: {combined_df.shape}")
        print(f"\nFirst 5 rows of extracted data:")
        print(combined_df.head())
        print(f"\nDataFrame info:")
        print(combined_df.info())
        print(f"{'='*60}\n")
        
        # Return the DataFrame directly (no CSV files)
        return combined_df

    @task(
        retries=2,
        retry_delay=timedelta(minutes=1),
        execution_timeout=timedelta(minutes=15),
    )
    def transform(df) -> pd.DataFrame:
        """
        Transform: Clean and prepare raw weather DataFrame for Snowflake RAW schema.
        Returns single DataFrame ready for loading.
        """
        print(f"\n{'='*60}")
        print(f"TRANSFORM STARTING")
        print(f"{'='*60}")
        print(f"Input type: {type(df)}")
        
        # Handle case where extract returned a status dict instead of DataFrame
        if isinstance(df, dict):
            if df.get("status") == "complete":
                print("No new data to transform")
                return {"status": "no_data"}
            elif df.get("status") == "no_data":
                print("No data was fetched")
                return {"status": "no_data"}
        
        print(f"Transforming {len(df)} rows")
        print(f"Input DataFrame columns: {list(df.columns)}")
        print(f"Input DataFrame shape: {df.shape}")
        print(f"\nFirst 3 rows BEFORE transformation:")
        print(df.head(3))
        
        # Normalize index to 'time' and derive DATE column
        if (df.index.name or "").lower() != "time" and "time" in df.columns:
            df = df.set_index("time")
        
        idx = pd.to_datetime(df.index, errors="coerce")
        # Convert to date object (not string) for Snowflake DATE type
        df["DATE"] = idx.date if hasattr(idx, 'date') else idx.dt.date
        
        # Convert datetime columns
        for col in ["sunrise", "sunset"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        
        # Coerce numeric columns
        numeric_cols = [
            "temperature_2m_max", "temperature_2m_min", "apparent_temperature_max",
            "apparent_temperature_min", "precipitation_sum", "precipitation_hours",
            "snowfall_sum", "windspeed_10m_max", "windgusts_10m_max",
            "winddirection_10m_dominant", "shortwave_radiation_sum",
            "et0_fao_evapotranspiration", "weathercode", "rain_sum",
            "latitude", "longitude"
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        # Ensure city_idx is integer
        if "city_idx" in df.columns:
            df["city_idx"] = pd.to_numeric(df["city_idx"], errors="coerce").astype("Int64")
        
        print(f"\n{'='*60}")
        print(f"TRANSFORM COMPLETE!")
        print(f"{'='*60}")
        print(f"Transformed DataFrame has {len(df)} rows and {len(df.columns)} columns")
        print(f"\nColumn names after transform: {list(df.columns)}")
        print(f"DataFrame shape: {df.shape}")
        print(f"\nFirst 5 rows AFTER transformation:")
        print(df.head())
        print(f"\nSample of key columns:")
        key_cols = ['DATE', 'city_idx', 'city_name', 'temperature_2m_max', 'precipitation_sum']
        available_cols = [col for col in key_cols if col in df.columns]
        if available_cols:
            print(df[available_cols].head())
        print(f"\nData types:")
        print(df.dtypes)
        print(f"{'='*60}\n")
        
        # Return single DataFrame
        return df

    @task(
        retries=3,
        retry_delay=timedelta(minutes=3),
        execution_timeout=timedelta(minutes=20),
    )
    def load(df) -> dict:
        """
        Load: Connect to Snowflake and upsert data into RAW.PAYNES_WEATHER table using MERGE.
        Single table with all weather data - organize into data warehouse later with Snowflake SQL.
        """
        print(f"\n{'='*60}")
        print(f"LOAD STARTING")
        print(f"{'='*60}")
        print(f"Input type: {type(df)}")
        
        # Handle case where transform returned a status dict instead of DataFrame
        if isinstance(df, dict) and df.get("status") == "no_data":
            print("No data to load")
            return {"status": "no_data", "message": "No new data to load"}
        
        print(f"Loading {len(df)} rows into Snowflake")
        print(f"DataFrame columns: {list(df.columns)}")
        print(f"DataFrame shape: {df.shape}")
        print(f"\nFirst 3 rows to be loaded:")
        print(df.head(3))
        
        # Connect to Snowflake (Airflow 3.0 compatible)
        try:
            hook = SnowflakeHook(snowflake_conn_id="snowflake_default")
            conn = hook.get_conn()
            cursor = conn.cursor()
        except Exception as e:
            raise Exception(f"Failed to connect to Snowflake: {str(e)}")
        
        # Target table
        target_table = "SNOWBEARAIR_DB.RAW.PAYNES_WEATHER"
        
        # Temp table name
        suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        tmp_table = f"TEMP_PAYNES_WEATHER_{suffix}"
        
        try:
            # --- CREATE TARGET TABLE IF NOT EXISTS ---
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {target_table} (
                    DATE DATE,
                    CITY_IDX INT,
                    CITY_NAME VARCHAR,
                    LATITUDE FLOAT,
                    LONGITUDE FLOAT,
                    TEMPERATURE_2M_MAX FLOAT,
                    TEMPERATURE_2M_MIN FLOAT,
                    APPARENT_TEMPERATURE_MAX FLOAT,
                    APPARENT_TEMPERATURE_MIN FLOAT,
                    PRECIPITATION_SUM FLOAT,
                    PRECIPITATION_HOURS FLOAT,
                    SUNRISE TIMESTAMP_NTZ,
                    SUNSET TIMESTAMP_NTZ,
                    SNOWFALL_SUM FLOAT,
                    WINDSPEED_10M_MAX FLOAT,
                    WINDGUSTS_10M_MAX FLOAT,
                    WINDDIRECTION_10M_DOMINANT FLOAT,
                    SHORTWAVE_RADIATION_SUM FLOAT,
                    ET0_FAO_EVAPOTRANSPIRATION FLOAT,
                    WEATHERCODE INT,
                    RAIN_SUM FLOAT,
                    SOURCE_FILE VARCHAR,
                    PRIMARY KEY (DATE, CITY_IDX)
                )
            """)
            
            # --- CREATE TEMP TABLE (LIKE target) ---
            cursor.execute(f"CREATE TEMPORARY TABLE {tmp_table} LIKE {target_table}")
            
            # --- BULK INSERT INTO TEMP TABLE ---
            def bulk_insert(df_in: pd.DataFrame, table: str, cols: list) -> int:
                """Insert DataFrame rows into table, handling NaNs as None."""
                if df_in.empty:
                    return 0
                safe_df = df_in.copy().where(pd.notnull(df_in), None)
                
                # Convert timestamp columns to strings for Snowflake compatibility
                timestamp_cols = ["SUNRISE", "SUNSET"]
                for col in timestamp_cols:
                    if col in safe_df.columns:
                        safe_df[col] = safe_df[col].astype(str).replace("NaT", "None")
                        # Replace "None" strings with actual None
                        safe_df[col] = safe_df[col].apply(lambda x: None if x == "None" else x)
                
                placeholders = ", ".join(["%s"] * len(cols))
                col_list = ", ".join(cols)
                sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
                rows = [tuple(safe_df[c].iloc[i] for c in cols) for i in range(len(safe_df))]
                cursor.executemany(sql, rows)
                return len(rows)
            
            # Columns for insert
            cols = [
                "DATE", "CITY_IDX", "CITY_NAME", "LATITUDE", "LONGITUDE",
                "TEMPERATURE_2M_MAX", "TEMPERATURE_2M_MIN",
                "APPARENT_TEMPERATURE_MAX", "APPARENT_TEMPERATURE_MIN",
                "PRECIPITATION_SUM", "PRECIPITATION_HOURS",
                "SUNRISE", "SUNSET", "SNOWFALL_SUM",
                "WINDSPEED_10M_MAX", "WINDGUSTS_10M_MAX", "WINDDIRECTION_10M_DOMINANT",
                "SHORTWAVE_RADIATION_SUM", "ET0_FAO_EVAPOTRANSPIRATION",
                "WEATHERCODE", "RAIN_SUM", "SOURCE_FILE"
            ]
            
            # Rename columns to uppercase for Snowflake
            df_up = df.rename(columns=str.upper)
            
            print(f"\nDataFrame columns after uppercase: {list(df_up.columns)}")
            print(f"Columns to insert: {cols}")
            print(f"\nChecking for column mismatches...")
            missing_cols = [c for c in cols if c not in df_up.columns]
            if missing_cols:
                print(f"WARNING: Missing columns: {missing_cols}")
            print(f"\nFirst 3 rows being inserted into temp table:")
            print(df_up.head(3))
            
            n_rows = bulk_insert(df_up, tmp_table, cols)
            print(f"\nInserted {n_rows} rows into temp table {tmp_table}")
            
            # --- MERGE TEMP -> TARGET ---
            print(f"\nExecuting MERGE from {tmp_table} into {target_table}...")
            merge_result = cursor.execute(f"""
                MERGE INTO {target_table} t
                USING {tmp_table} s
                ON t.DATE = s.DATE AND t.CITY_IDX = s.CITY_IDX
                WHEN MATCHED THEN UPDATE SET
                    CITY_NAME = s.CITY_NAME,
                    LATITUDE = s.LATITUDE,
                    LONGITUDE = s.LONGITUDE,
                    TEMPERATURE_2M_MAX = s.TEMPERATURE_2M_MAX,
                    TEMPERATURE_2M_MIN = s.TEMPERATURE_2M_MIN,
                    APPARENT_TEMPERATURE_MAX = s.APPARENT_TEMPERATURE_MAX,
                    APPARENT_TEMPERATURE_MIN = s.APPARENT_TEMPERATURE_MIN,
                    PRECIPITATION_SUM = s.PRECIPITATION_SUM,
                    PRECIPITATION_HOURS = s.PRECIPITATION_HOURS,
                    SUNRISE = s.SUNRISE,
                    SUNSET = s.SUNSET,
                    SNOWFALL_SUM = s.SNOWFALL_SUM,
                    WINDSPEED_10M_MAX = s.WINDSPEED_10M_MAX,
                    WINDGUSTS_10M_MAX = s.WINDGUSTS_10M_MAX,
                    WINDDIRECTION_10M_DOMINANT = s.WINDDIRECTION_10M_DOMINANT,
                    SHORTWAVE_RADIATION_SUM = s.SHORTWAVE_RADIATION_SUM,
                    ET0_FAO_EVAPOTRANSPIRATION = s.ET0_FAO_EVAPOTRANSPIRATION,
                    WEATHERCODE = s.WEATHERCODE,
                    RAIN_SUM = s.RAIN_SUM,
                    SOURCE_FILE = s.SOURCE_FILE
                WHEN NOT MATCHED THEN INSERT (
                    DATE, CITY_IDX, CITY_NAME, LATITUDE, LONGITUDE,
                    TEMPERATURE_2M_MAX, TEMPERATURE_2M_MIN,
                    APPARENT_TEMPERATURE_MAX, APPARENT_TEMPERATURE_MIN,
                    PRECIPITATION_SUM, PRECIPITATION_HOURS,
                    SUNRISE, SUNSET, SNOWFALL_SUM,
                    WINDSPEED_10M_MAX, WINDGUSTS_10M_MAX, WINDDIRECTION_10M_DOMINANT,
                    SHORTWAVE_RADIATION_SUM, ET0_FAO_EVAPOTRANSPIRATION,
                    WEATHERCODE, RAIN_SUM, SOURCE_FILE
                ) VALUES (
                    s.DATE, s.CITY_IDX, s.CITY_NAME, s.LATITUDE, s.LONGITUDE,
                    s.TEMPERATURE_2M_MAX, s.TEMPERATURE_2M_MIN,
                    s.APPARENT_TEMPERATURE_MAX, s.APPARENT_TEMPERATURE_MIN,
                    s.PRECIPITATION_SUM, s.PRECIPITATION_HOURS,
                    s.SUNRISE, s.SUNSET, s.SNOWFALL_SUM,
                    s.WINDSPEED_10M_MAX, s.WINDGUSTS_10M_MAX, s.WINDDIRECTION_10M_DOMINANT,
                    s.SHORTWAVE_RADIATION_SUM, s.ET0_FAO_EVAPOTRANSPIRATION,
                    s.WEATHERCODE, s.RAIN_SUM, s.SOURCE_FILE
                )
            """)
            
            # Get merge statistics
            rows_inserted = merge_result.fetchone()[0] if merge_result else 0
            print(f"MERGE statement executed successfully")
            print(f"Rows affected by MERGE: {rows_inserted}")
            
            conn.commit()
            print("Transaction committed")
            
            # Verify data was loaded
            cursor.execute(f"SELECT COUNT(*) FROM {target_table}")
            total_count = cursor.fetchone()[0]
            print(f"Total rows in {target_table}: {total_count}")
            
            # Show sample of loaded data
            cursor.execute(f"SELECT * FROM {target_table} LIMIT 5")
            sample_rows = cursor.fetchall()
            print(f"\nSample rows from {target_table}:")
            for row in sample_rows:
                print(row)
            
            # Drop temp table
            cursor.execute(f"DROP TABLE IF EXISTS {tmp_table}")
            
            print(f"\n{'='*60}")
            print(f"LOAD COMPLETE!")
            print(f"{'='*60}")
            print(f"  - Inserted {n_rows} rows into temp table")
            print(f"  - Merged into {target_table}")
            print(f"  - Total rows in target table: {total_count}")
            print(f"{'='*60}\n")
            
            return {
                "status": "success",
                "rows_inserted": n_rows,
                "total_rows": total_count,
                "table": target_table
            }
        
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            raise Exception(f"Snowflake load failed: {str(e)}")
        
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass

    # Wire the tasks together (Airflow 3.0 TaskFlow API)
    raw_df = extract()
    transformed_df = transform(raw_df)
    load_result = load(transformed_df)


# Instantiate the DAG
dag = dev_weather_etl_pipeline_v2()
