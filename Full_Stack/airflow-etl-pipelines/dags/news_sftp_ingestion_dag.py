# DAG: sftp_download_dag.py
# Opens SFTP connection once, finds the latest available date (scanning backwards from today),
# downloads all CSV files for that date into a single DataFrame, and loads to Snowflake.
from datetime import datetime, timedelta, timezone
import os
import logging
import pandas as pd
from dotenv import load_dotenv
import paramiko

try:
    from airflow.decorators import dag, task
except Exception:
    def dag(*args, **kwargs):
        def _decor(fn):
            return fn
        return _decor

    def task(*args, **kwargs):
        def _decor(fn):
            return fn
        return _decor

load_dotenv(".env")

SFTP_HOST = os.getenv("SFTP_HOST")
SFTP_PORT = int(os.getenv("SFTP_PORT"))
SFTP_USER = os.getenv("SFTP_USER")
SFTP_PASSWORD = os.getenv("SFTP_PASSWORD")
SFTP_DIR = os.getenv("SFTP_DIR")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Global connection objects (persistent across tasks)
_ssh_connection = None
_sftp_connection = None


def get_or_create_sftp_connection():
    """Get or create a persistent SFTP connection."""
    global _ssh_connection, _sftp_connection
    
    if _sftp_connection is not None:
        logger.info("Reusing existing SFTP connection.")
        return _sftp_connection
    
    logger.info("Creating new SFTP connection...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SFTP_HOST, port=SFTP_PORT, username=SFTP_USER, password=SFTP_PASSWORD)
    logger.info("✅ SSH connection established.")
    
    sftp = ssh.open_sftp()
    logger.info("✅ SFTP session established.")
    
    _ssh_connection = ssh
    _sftp_connection = sftp
    return sftp


def close_sftp_connection():
    """Close the persistent SFTP connection."""
    global _ssh_connection, _sftp_connection
    
    try:
        if _sftp_connection:
            _sftp_connection.close()
            logger.info("🔒 SFTP session closed.")
    except Exception:
        pass
    
    try:
        if _ssh_connection:
            _ssh_connection.close()
            logger.info("🔒 SSH connection closed.")
    except Exception:
        pass
    
    _ssh_connection = None
    _sftp_connection = None


def find_latest_available_date(sftp, max_lookback_days=30):
    """
    Scan backwards from today to find the latest date with available data.
    Checks if the remote folder exists for each date.
    Returns a datetime.date object or None if no date found.
    """
    logger.info(f"Scanning for latest available date (max lookback: {max_lookback_days} days)...")
    
    for days_back in range(0, max_lookback_days):
        check_date = (datetime.utcnow().date() - timedelta(days=days_back))
        date_str = check_date.strftime("%Y-%m-%d")
        remote_folder = f"{SFTP_DIR}/{date_str}"
        
        try:
            listing = sftp.listdir(remote_folder)
            if listing:  # Folder exists and has files
                logger.info(f"✅ Found data for {date_str} with {len(listing)} entries")
                return check_date
            else:
                logger.info(f"📂 Folder exists but empty: {date_str}")
        except IOError:
            logger.info(f"⏭️ No folder for {date_str}, continuing...")
    
    logger.warning("❌ No available data found within lookback period")
    return None


def download_and_combine_csvs(sftp, target_date):
    """
    Download all CSV files for the target date and combine into a single DataFrame.
    Returns a DataFrame or None if no CSVs found.
    """
    date_str = target_date.strftime("%Y-%m-%d")
    remote_folder = f"{SFTP_DIR}/{date_str}"
    local_dir = date_str
    
    logger.info(f"Downloading CSV files from {remote_folder}...")
    
    try:
        listing = sftp.listdir(remote_folder)
    except IOError:
        logger.error(f"Remote folder does not exist: {remote_folder}")
        return None
    
    # Filter only CSV files
    csv_files = [f for f in listing if f.lower().endswith('.csv')]
    
    if not csv_files:
        logger.warning(f"No CSV files found in {remote_folder}")
        return None
    
    logger.info(f"Found {len(csv_files)} CSV files: {csv_files}")
    
    os.makedirs(local_dir, exist_ok=True)
    
    dfs = []
    for filename in csv_files:
        remote_path = f"{remote_folder}/{filename}"
        local_path = os.path.join(local_dir, filename)
        
        try:
            logger.info(f"⬇️ Downloading: {remote_path}")
            sftp.get(remote_path, local_path)
            
            # Read CSV into DataFrame
            df = pd.read_csv(local_path)
            logger.info(f"✅ Loaded {filename}: {len(df)} rows, {len(df.columns)} columns")
            dfs.append(df)
        
        except Exception as e:
            logger.error(f"❌ Failed to download/read {filename}: {e}")
    
    if not dfs:
        logger.warning("No CSVs successfully loaded")
        return None
    
    # Combine all DataFrames
    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"\n✅ Combined DataFrame: {len(combined_df)} rows, {len(combined_df.columns)} columns")
    logger.info(f"Columns: {list(combined_df.columns)}")
    logger.info(f"\nFirst 5 rows:\n{combined_df.head()}")
    
    return combined_df


@dag(
    dag_id="sftp_download_dag",
    schedule="0 19 * * 0",  # Every Sunday at 12:00 PM Mountain Time (19:00 UTC)
    start_date=datetime(2025, 9, 1, tzinfo=timezone.utc),5
    catchup=True,
    max_active_runs=1,  # Only 1 backfill run at a time to avoid rate limiting
    tags=["sftp", "snowflake", "etl"],
)
def sftp_download_dag():
    """
    ETL DAG with Backfill and Weekly Scheduling:
    1. Extract: Open SFTP connection, find latest date, download all CSV files
    2. Transform: Combine CSVs into a single DataFrame
    3. Load: Insert data into Snowflake and close connection    
    Schedule: Every Sunday at 12:00 PM Mountain Time (19:00 UTC)
    With catchup=True, Airflow will automatically backfill all dates from 9-1-2025 onwards.
    """
    
    @task()
    def extract():
        """
        Extract: Open SFTP connection ONCE, scan ALL available dates, download ALL CSV files.
        Returns combined DataFrame with data from all available days.
        """
        logger.info("\n" + "="*60)
        logger.info("EXTRACT: Opening SFTP connection and downloading ALL data...")
        logger.info("="*60)
        
        # Small delay to be respectful to the SFTP server
        import time
        time.sleep(2)
        
        # Get or create persistent SFTP connection (ONE connection for all downloads)
        sftp = get_or_create_sftp_connection()
        
        logger.info("🔓 Connection opened. Scanning for all available dates...")
        
        # Scan SFTP_DIR for all available date folders
        all_dfs = []
        total_files_downloaded = 0
        dates_processed = []
        
        try:
            all_items = sftp.listdir(SFTP_DIR)
            logger.info(f"Found {len(all_items)} items in {SFTP_DIR}")
        except IOError as e:
            logger.error(f"Failed to list SFTP_DIR: {e}")
            return {"status": "error", "error": str(e)}
        
        # Filter to date-like folders (YYYY-MM-DD format)
        import re
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        date_folders = sorted([item for item in all_items if date_pattern.match(item)], reverse=True)
        
        logger.info(f"Found {len(date_folders)} date folders: {date_folders[:5]}{'...' if len(date_folders) > 5 else ''}")
        
        # Download ALL CSVs from ALL date folders
        for date_folder in date_folders:
            remote_folder = f"{SFTP_DIR}/{date_folder}"
            local_dir = date_folder
            
            try:
                listing = sftp.listdir(remote_folder)
            except IOError:
                logger.info(f"⏭️ Skipping {date_folder} (folder error)")
                continue
            
            # Filter only CSV files
            csv_files = [f for f in listing if f.lower().endswith('.csv')]
            
            if not csv_files:
                logger.info(f"📂 {date_folder}: no CSVs")
                continue
            
            logger.info(f"📥 {date_folder}: downloading {len(csv_files)} CSV files")
            
            os.makedirs(local_dir, exist_ok=True)
            
            for filename in csv_files:
                remote_path = f"{remote_folder}/{filename}"
                local_path = os.path.join(local_dir, filename)
                
                try:
                    logger.info(f"   ⬇️ {filename}")
                    sftp.get(remote_path, local_path)
                    
                    # Read CSV into DataFrame
                    df = pd.read_csv(local_path)
                    all_dfs.append(df)
                    total_files_downloaded += 1
                    
                except Exception as e:
                    logger.error(f"   ❌ Failed {filename}: {e}")
            
            dates_processed.append(date_folder)
        
        if not all_dfs:
            logger.warning("❌ No CSVs downloaded from any date folder")
            return {"status": "no_data", "total_files": 0}
        
        # Combine ALL DataFrames into one
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        logger.info(f"\n✅ EXTRACTION COMPLETE")
        logger.info(f"   Files downloaded: {total_files_downloaded}")
        logger.info(f"   Date folders scanned: {len(dates_processed)}")
        logger.info(f"   Combined DataFrame: {len(combined_df)} rows, {len(combined_df.columns)} columns")
        logger.info(f"   Columns: {list(combined_df.columns)}")
        
        return {
            "status": "success",
            "total_files": total_files_downloaded,
            "dates_processed": dates_processed,
            "row_count": len(combined_df),
            "column_count": len(combined_df.columns),
            "columns": list(combined_df.columns),
            "data": combined_df.to_dict('records'),  # Serialize for Airflow
        }
    
    @task()
    def transform(extract_result):
        """
        Transform: Standardize DataFrame structure for all downloaded data.
        - Convert columns to UPPERCASE
        - Convert DATETIME column from Unix timestamp to readable datetime
        Returns cleaned DataFrame ready for loading.
        """
        logger.info("\n" + "="*60)
        logger.info("TRANSFORM: Preparing ALL data for Snowflake...")
        logger.info("="*60)
        
        # Skip if no data
        if extract_result.get("status") in ["no_data", "error"]:
            logger.info(f"Skipping transform - status: {extract_result['status']}")
            return extract_result
        
        # Reconstruct DataFrame from serialized data
        data = extract_result.get("data", [])
        if not data:
            logger.warning("No data to transform")
            return {"status": "no_data"}
        
        df = pd.DataFrame(data)
        
        # Standardize columns to uppercase
        df.columns = [col.upper() for col in df.columns]
        
        # Convert DATETIME column from Unix timestamp to datetime
        if "DATETIME" in df.columns:
            logger.info("Converting DATETIME column from Unix timestamp to datetime...")
            try:
                # Convert Unix timestamp (seconds) to datetime
                df["DATETIME"] = pd.to_datetime(df["DATETIME"], unit='s', utc=True)
                logger.info(f"✅ DATETIME converted. Sample values:\n{df['DATETIME'].head(3)}")
            except Exception as e:
                logger.warning(f"Failed to convert DATETIME column: {e}")
        
        logger.info(f"Transformed DataFrame: {len(df)} rows, {len(df.columns)} columns")
        logger.info(f"Columns: {list(df.columns)}")
        logger.info(f"First 3 rows:\n{df.head(3)}")
        
        return {
            "status": "success",
            "total_files": extract_result.get("total_files", 0),
            "dates_processed": extract_result.get("dates_processed", []),
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "data": df.to_dict('records'),  # Serialize for Airflow
        }
    
    @task()
    def load(transform_result):
        """
        Load: Insert ALL data into Snowflake and close SFTP connection.
        """
        logger.info("\n" + "="*60)
        logger.info("LOAD: Loading ALL data to Snowflake...")
        logger.info("="*60)
        
        # Skip if no data
        if transform_result.get("status") in ["no_data", "error"]:
            logger.info(f"Skipping load - status: {transform_result['status']}")
            logger.info("Closing SFTP connection...")
            close_sftp_connection()
            return {"status": transform_result["status"]}
        
        # Reconstruct DataFrame from serialized data
        data = transform_result.get("data", [])
        if not data:
            logger.warning("No data to load")
            close_sftp_connection()
            return {"status": "no_data"}
        
        combined_df = pd.DataFrame(data)
        
        logger.info(f"Loading {len(combined_df)} rows into Snowflake")
        logger.info(f"DataFrame columns: {list(combined_df.columns)}")
        logger.info(f"Files processed: {transform_result.get('total_files', 0)}")
        logger.info(f"Dates processed: {len(transform_result.get('dates_processed', []))} date folders")
        
        # Connect to Snowflake and load
        try:
            from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
            hook = SnowflakeHook(snowflake_conn_id="snowflake_default")
            conn = hook.get_conn()
            cursor = conn.cursor()
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {e}")
            close_sftp_connection()
            raise
        
        try:
            # Target table
            target_table = "SNOWBEARAIR_DB.RAW.PAYNES_NEWS"
            suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
            tmp_table = f"TEMP_SFTP_DATA_{suffix}"
            
            # Build CREATE TABLE statement dynamically based on DataFrame columns
            def get_snowflake_type(dtype):
                if pd.api.types.is_datetime64_any_dtype(dtype):
                    return "TIMESTAMP_NTZ"
                elif pd.api.types.is_integer_dtype(dtype):
                    return "INT"
                elif pd.api.types.is_float_dtype(dtype):
                    return "FLOAT"
                else:
                    return "VARCHAR"
            
            # Build column definitions
            col_defs = []
            for col in combined_df.columns:
                snowflake_type = get_snowflake_type(combined_df[col].dtype)
                col_defs.append(f"{col} {snowflake_type}")
            
            create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {target_table} (
                    {', '.join(col_defs)}
                )
            """
            
            logger.info(f"Creating table with SQL:\n{create_table_sql}")
            cursor.execute(create_table_sql)
            logger.info(f"✅ Table {target_table} ready")
            
            # --- CREATE TEMP TABLE (LIKE target) ---
            cursor.execute(f"CREATE TEMPORARY TABLE {tmp_table} LIKE {target_table}")
            logger.info(f"✅ Temp table {tmp_table} created")
            
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
            
            # Use all available columns
            cols = list(combined_df.columns)
            
            logger.info(f"Columns to insert: {cols}")
            logger.info(f"First 3 rows being inserted into temp table:")
            logger.info(combined_df[cols].head(3))
            
            n_rows = bulk_insert(combined_df, tmp_table, cols)
            logger.info(f"✅ Inserted {n_rows} rows into temp table {tmp_table}")
            
            # --- INSERT TEMP -> TARGET ---
            logger.info(f"Executing INSERT from {tmp_table} into {target_table}...")
            
            insert_sql = f"INSERT INTO {target_table} SELECT * FROM {tmp_table}"
            cursor.execute(insert_sql)
            
            conn.commit()
            logger.info("✅ Transaction committed")
            
            # Verify
            cursor.execute(f"SELECT COUNT(*) FROM {target_table}")
            total = cursor.fetchone()[0]
            logger.info(f"Total rows in {target_table}: {total}")
            
            # Show sample
            cursor.execute(f"SELECT * FROM {target_table} LIMIT 3")
            sample_rows = cursor.fetchall()
            logger.info(f"Sample rows from {target_table}:")
            for row in sample_rows:
                logger.info(row)
            
            # Drop temp table
            cursor.execute(f"DROP TABLE IF EXISTS {tmp_table}")
            
            logger.info(f"\n{'='*60}")
            logger.info(f"LOAD COMPLETE!")
            logger.info(f"{'='*60}")
            logger.info(f"  - Total files downloaded: {transform_result.get('total_files', 0)}")
            logger.info(f"  - Date folders processed: {len(transform_result.get('dates_processed', []))}")
            logger.info(f"  - Rows inserted into temp: {n_rows}")
            logger.info(f"  - Total rows in {target_table}: {total}")
            logger.info(f"{'='*60}\n")
            
            result = {
                "status": "success",
                "rows_inserted": n_rows,
                "total_rows": total,
                "total_files": transform_result.get('total_files', 0),
                "dates_processed": len(transform_result.get('dates_processed', [])),
                "table": target_table,
            }
        
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.exception(f"Snowflake load failed: {e}")
            result = {"status": "error", "error": str(e)}
        
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
            
            # Always close SFTP connection at the end
            logger.info("\n" + "="*60)
            logger.info("CLEANUP: Closing SFTP connection (used for ALL files)...")
            logger.info("="*60)
            close_sftp_connection()
        
        return result
    
    # Wire the 3 tasks together
    extracted = extract()
    transformed = transform(extracted)
    load(transformed)


dag = sftp_download_dag()
