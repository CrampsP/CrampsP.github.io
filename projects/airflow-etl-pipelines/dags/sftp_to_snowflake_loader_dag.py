# DAG: sftp_latest_data_to_snowflake.py
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
    dag_id="sftp_latest_to_snowflake",
    schedule=None,
    start_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    tags=["sftp", "snowflake", "etl"],
)
def sftp_latest_to_snowflake():
    """
    ETL DAG:
    1. Open SFTP connection (once, reused)
    2. Find latest available date by scanning backwards
    3. Download all CSV files for that date
    4. Combine into a single DataFrame
    5. Load to Snowflake
    6. Close connection
    """
    
    @task()
    def setup_connection():
        """Open SFTP connection and return success status."""
        logger.info("\n" + "="*60)
        logger.info("SETUP: Opening SFTP connection...")
        logger.info("="*60)
        sftp = get_or_create_sftp_connection()
        return {"connection_status": "open"}
    
    @task()
    def find_latest_date(setup_result):
        """Find the latest available date with data."""
        logger.info("\n" + "="*60)
        logger.info("FIND: Scanning for latest available date...")
        logger.info("="*60)
        sftp = get_or_create_sftp_connection()
        
        latest_date = find_latest_available_date(sftp, max_lookback_days=30)
        
        if latest_date is None:
            raise Exception("No available data found within lookback period")
        
        date_str = latest_date.strftime("%Y-%m-%d")
        logger.info(f"Latest date: {date_str}")
        return {"latest_date": date_str, "date_obj": latest_date}
    
    @task()
    def extract_and_combine(find_result):
        """Download all CSV files for latest date and combine into DataFrame."""
        logger.info("\n" + "="*60)
        logger.info("EXTRACT: Downloading and combining CSVs...")
        logger.info("="*60)
        sftp = get_or_create_sftp_connection()
        
        latest_date = find_result["date_obj"]
        df = download_and_combine_csvs(sftp, latest_date)
        
        if df is None or df.empty:
            raise Exception("No data extracted")
        
        # Serialize to JSON for Airflow (can't pass DataFrames directly)
        return {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "date": find_result["latest_date"],
        }
    
    @task()
    def load_to_snowflake(extract_result):
        """Load the combined DataFrame to Snowflake."""
        logger.info("\n" + "="*60)
        logger.info("LOAD: Loading to Snowflake...")
        logger.info("="*60)
        
        # Re-extract the DataFrame for upload (in a real scenario, you'd pass the data differently)
        sftp = get_or_create_sftp_connection()
        
        # Reconstruct the date from extract_result
        date_str = extract_result["date"]
        local_dir = date_str
        
        # Re-load the CSVs from the local directory we downloaded earlier
        csv_files = [f for f in os.listdir(local_dir) if f.lower().endswith('.csv')]
        dfs = []
        for filename in csv_files:
            local_path = os.path.join(local_dir, filename)
            df = pd.read_csv(local_path)
            dfs.append(df)
        
        combined_df = pd.concat(dfs, ignore_index=True) if dfs else None
        
        if combined_df is None or combined_df.empty:
            logger.error("No data to load")
            return {"status": "no_data"}
        
        # Connect to Snowflake and load
        try:
            from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
            hook = SnowflakeHook(snowflake_conn_id="snowflake_default")
            conn = hook.get_conn()
            cursor = conn.cursor()
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {e}")
            raise
        
        try:
            target_table = "SNOWBEARAIR_DB.RAW.SFTP_LATEST_DATA"
            
            # Create table if not exists (adjust columns based on your CSV structure)
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {target_table} (
                    LOADED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
                    LOADED_DATE DATE
                )
            """)
            logger.info(f"✅ Table {target_table} ready")
            
            # Insert data
            def bulk_insert_csv(df_in, table, cursor):
                """Insert DataFrame rows into Snowflake."""
                if df_in.empty:
                    return 0
                
                # Sanitize: replace NaN with None
                safe_df = df_in.copy().where(pd.notnull(df_in), None)
                
                # Get column names
                cols = list(safe_df.columns)
                col_list = ", ".join(cols)
                placeholders = ", ".join(["%s"] * len(cols))
                
                sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
                
                rows = [tuple(safe_df[c].iloc[i] for c in cols) for i in range(len(safe_df))]
                cursor.executemany(sql, rows)
                return len(rows)
            
            n_rows = bulk_insert_csv(combined_df, target_table, cursor)
            conn.commit()
            
            logger.info(f"✅ Inserted {n_rows} rows into {target_table}")
            
            # Verify
            cursor.execute(f"SELECT COUNT(*) FROM {target_table}")
            total = cursor.fetchone()[0]
            logger.info(f"Total rows in {target_table}: {total}")
            
            return {
                "status": "success",
                "rows_inserted": n_rows,
                "total_rows": total,
                "table": target_table,
            }
        
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.exception(f"Snowflake load failed: {e}")
            raise
        
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
    
    @task(trigger_rule="all_done")
    def cleanup(load_result):
        """Close SFTP connection at the end."""
        logger.info("\n" + "="*60)
        logger.info("CLEANUP: Closing SFTP connection...")
        logger.info("="*60)
        close_sftp_connection()
    
    # Wire the DAG
    setup = setup_connection()
    find = find_latest_date(setup)
    extract = extract_and_combine(find)
    load = load_to_snowflake(extract)
    cleanup(load)


dag = sftp_latest_to_snowflake()
