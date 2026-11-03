# Standard library imports
from datetime import datetime, timedelta, timezone, date
import pandas as pd
import os
import sys
from dateutil import tz

# Add parent directory to path for utils import
sys.path.insert(0, os.path.dirname(__file__))

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


@dag(
    dag_id="final_stock_dagV3",
    # Run every Sunday at 12:00 PM (noon) Mountain Time (19:00 UTC)
    schedule="0 19 * * 0",
    start_date=datetime(2024, 10, 15, 18, 0, tzinfo=timezone.utc),
    catchup=True,
    description="Stock ETL: Backfill from 10/15/2024 → Transform → Load to Snowflake. Runs weekly Sundays at 12 PM Idaho time",
    tags=["stock", "etl", "snowflake", "mongodb"],
    default_args={
        "owner": "airflow",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    doc_md="""
    ## Stock ETL Pipeline - Final (Airflow 3.0)
    
    Complete ETL pipeline for stock data with automatic backfilling and weekly scheduled runs:
    
    1. **Extract**: Fetches stock data from MongoDB via SSH tunnel for the execution date
    2. **Transform**: Structures data for Snowflake ingestion
    3. **Load**: Upserts data into Snowflake using MERGE (no duplicates)
    
    ### Schedule
    - **Weekly**: Every Sunday at 12:00 PM Mountain Time (19:00 UTC)
    - **Backfill**: From October 15, 2024 to current date (first run only)
    - **After backfill**: Runs every Sunday automatically, fetching that week's data
    
    ### Features
    - Single SSH tunnel connection (reused across all tasks)
    - MERGE operation ensures no duplicate data
    - Automatic catchup on first enable
    """,
)
def v3_stock_etl_pipeline():
    """
    ONE-DAY TEST pipeline for stock data:
    1. Extract: Fetch yesterday's stock data from MongoDB
    2. Transform: Clean and structure data into DataFrames
    3. Load: Upsert data into Snowflake tables
    """
    
    @task(
        retries=3,
        retry_delay=timedelta(minutes=2),
        execution_timeout=timedelta(minutes=30),
    )
    def extract(data_interval_start):
        """
        Extract stock data from MongoDB via SSH tunnel for the execution date.
        Uses data_interval_start (execution date) to query the correct day.
        Sets up SSH tunnel connection, fetches data, and returns DataFrame.
        """
        from utils import get_persistent_ssh_tunnel, get_mongo_client_cloud
        from dotenv import load_dotenv
        from pymongo import MongoClient
        
        load_dotenv()
        
        print("\n" + "="*60)
        print("SETUP: Opening persistent SSH tunnel connection...")
        print("="*60)
        
        try:
            tunnel = get_persistent_ssh_tunnel()
            print(f"✓ SSH tunnel connected on port {tunnel.local_bind_port}")
        except Exception as e:
            print(f"✗ Failed to setup connection: {str(e)}")
            raise
        
        print("\n" + "="*60)
        print("EXTRACT: Fetching stock data")
        print("="*60)
        
        try:
            # Connect to MongoDB
            client = get_mongo_client_cloud(tunnel)
            print("✓ MongoDB client connected")
            
            # Get database and collection
            db_name = os.getenv("MONGO_DB", "stock-data-db")
            collection_name = os.getenv("MONGO_COLLECTION", "price")
            collection = client[db_name][collection_name]
            print(f"✓ Connected to {db_name}.{collection_name}")
            
            # Use execution_date to determine which day to fetch
            # data_interval_start is the execution date passed by Airflow
            fetch_date = data_interval_start.date()
            
            start_iso = f"{fetch_date.strftime('%Y-%m-%d')}T00:00:00Z"
            end_iso = f"{fetch_date.strftime('%Y-%m-%d')}T23:59:59Z"
            
            query = {
                "datetime": {
                    "$gte": start_iso,
                    "$lte": end_iso
                }
            }
            
            print(f"\nQuerying for date: {fetch_date}")
            print(f"Query range: {start_iso} to {end_iso}")
            
            # Fetch documents
            documents = list(collection.find(query))
            print(f"✓ Retrieved {len(documents)} documents")
            
            if not documents:
                print("❌ No documents found for yesterday")
                return {"status": "no_data", "message": "No data found for yesterday"}
            
            # Convert to DataFrame
            df = pd.DataFrame(documents)
            
            # Remove MongoDB's _id field
            if '_id' in df.columns:
                df = df.drop('_id', axis=1)
            
            print(f"\n{'='*60}")
            print(f"EXTRACT COMPLETE!")
            print(f"{'='*60}")
            print(f"Combined DataFrame has {len(df)} rows and {len(df.columns)} columns")
            print(f"Date: {fetch_date}")
            print(f"\nColumn names: {list(df.columns)}")
            print(f"DataFrame shape: {df.shape}")
            print(f"\nFirst 5 rows of extracted data:")
            print(df.head())
            print(f"{'='*60}\n")
            
            return df
            
        except Exception as e:
            print(f"Error during extraction: {str(e)[:100]}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    @task(
        retries=2,
        retry_delay=timedelta(minutes=1),
        execution_timeout=timedelta(minutes=15),
    )
    def transform(df) -> pd.DataFrame:
        """
        Transform: Clean and prepare raw stock DataFrame for Snowflake RAW schema.
        Expected columns: symbol, datetime, open, high, low, close, volume
        Transformed to: SYMBOL, DATE, OPEN, HIGH, LOW, CLOSE, VOLUME
        """
        print(f"\n{'='*60}")
        print(f"TRANSFORM STARTING")
        print(f"{'='*60}")
        print(f"Input type: {type(df)}")
        
        # Handle case where extract returned a status dict instead of DataFrame
        if isinstance(df, dict):
            if df.get("status") in ["no_data", "error"]:
                print(f"Cannot transform: {df.get('message')}")
                return df
        
        print(f"Transforming {len(df)} rows")
        print(f"Input DataFrame columns: {list(df.columns)}")
        print(f"Input DataFrame shape: {df.shape}")
        print(f"\nFirst 3 rows BEFORE transformation:")
        print(df.head(3))
        
        # Convert datetime column (ISO format: "2025-07-17T00:00:00Z") to DATE object
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
            # Extract just the date part as a Python date object
            df['DATE'] = df['datetime'].dt.date
            # Drop the original datetime column since we have DATE
            df = df.drop('datetime', axis=1)
        
        # Standardize column names to uppercase for Snowflake
        df.columns = [col.upper() for col in df.columns]
        
        # Ensure numeric columns are proper types
        numeric_cols = ['OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove any rows with null dates or symbols (primary keys)
        if 'DATE' in df.columns and 'SYMBOL' in df.columns:
            before_count = len(df)
            df = df.dropna(subset=['DATE', 'SYMBOL'])
            after_count = len(df)
            if before_count != after_count:
                print(f"Removed {before_count - after_count} rows with null DATE or SYMBOL")
        
        print(f"\n{'='*60}")
        print(f"TRANSFORM COMPLETE!")
        print(f"{'='*60}")
        print(f"Transformed DataFrame has {len(df)} rows and {len(df.columns)} columns")
        print(f"\nColumn names after transform: {list(df.columns)}")
        print(f"DataFrame shape: {df.shape}")
        print(f"\nFirst 5 rows AFTER transformation:")
        print(df.head())
        print(f"\nData types:")
        print(df.dtypes)
        print(f"{'='*60}\n")
        
        return df

    @task(
        retries=3,
        retry_delay=timedelta(minutes=3),
        execution_timeout=timedelta(minutes=20),
    )
    def load(df) -> dict:
        """
        Load: Connect to Snowflake and upsert data into RAW.STOCK_DATA table using MERGE.
        Single table with all stock data.
        """
        print(f"\n{'='*60}")
        print(f"LOAD STARTING")
        print(f"{'='*60}")
        print(f"Input type: {type(df)}")
        
        # Handle case where transform returned a status dict instead of DataFrame
        if isinstance(df, dict) and df.get("status") in ["no_data", "error"]:
            print("No data to load")
            return {"status": "no_data", "message": df.get('message', 'No new data to load')}
        
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
        target_table = "SNOWBEARAIR_DB.RAW.PAYNES_STOCK"
        
        # Temp table name
        suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        tmp_table = f"TEMP_STOCK_DATA_{suffix}"
        
        try:
            # --- CREATE TARGET TABLE IF NOT EXISTS ---
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {target_table} (
                    DATE DATE,
                    SYMBOL VARCHAR,
                    OPEN FLOAT,
                    HIGH FLOAT,
                    LOW FLOAT,
                    CLOSE FLOAT,
                    VOLUME INT,
                    PRIMARY KEY (DATE, SYMBOL)
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
                placeholders = ", ".join(["%s"] * len(cols))
                col_list = ", ".join(cols)
                sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
                rows = [tuple(safe_df[c].iloc[i] for c in cols) for i in range(len(safe_df))]
                cursor.executemany(sql, rows)
                return len(rows)
            
            # Columns for insert
            cols = [
                "DATE", "SYMBOL", "OPEN", "HIGH", "LOW", "CLOSE", "VOLUME"
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
                ON t.DATE = s.DATE AND t.SYMBOL = s.SYMBOL
                WHEN MATCHED THEN UPDATE SET
                    OPEN = s.OPEN,
                    HIGH = s.HIGH,
                    LOW = s.LOW,
                    CLOSE = s.CLOSE,
                    VOLUME = s.VOLUME
                WHEN NOT MATCHED THEN INSERT (
                    DATE, SYMBOL, OPEN, HIGH, LOW, CLOSE, VOLUME
                ) VALUES (
                    s.DATE, s.SYMBOL, s.OPEN, s.HIGH, s.LOW, s.CLOSE, s.VOLUME
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

    @task(
        trigger_rule="all_done",  # Runs even if upstream tasks fail
        execution_timeout=timedelta(minutes=5),
    )
    def cleanup_connection():
        """
        Close the persistent SSH tunnel at the end of the DAG execution.
        Uses trigger_rule='all_done' to ensure it runs even if other tasks fail.
        This task closes the tunnel that was opened in the extract task.
        """
        from utils import close_persistent_ssh_tunnel
        
        print("\n" + "="*60)
        print("CLEANUP: Closing persistent SSH tunnel connection...")
        print("="*60)
        close_persistent_ssh_tunnel()
        print("="*60 + "\n")
    
    # Wire the tasks together (Airflow 3.0 TaskFlow API)
    raw_df = extract()
    transformed_df = transform(raw_df)
    load_result = load(transformed_df)
    cleanup = cleanup_connection()
    
    # Ensure cleanup runs AFTER load completes (and all other tasks done)
    # This is the ONLY place where cleanup is called - at the very end
    [raw_df, transformed_df, load_result] >> cleanup


# Instantiate the DAG
dag = v3_stock_etl_pipeline()
