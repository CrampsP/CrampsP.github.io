"""
Test script: Connect to SFTP, download all files for two days ago, print DataFrame.
Reuses the same connection pattern as staging/sftp_test.py.
"""
import os
import logging
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
import paramiko

# Load env (same as staging/sftp_test.py and the DAG)
load_dotenv(".env")

# Read SFTP settings
SFTP_HOST = os.getenv("SFTP_HOST")
SFTP_PORT = int(os.getenv("SFTP_PORT"))
SFTP_USER = os.getenv("SFTP_USER")
SFTP_PASSWORD = os.getenv("SFTP_PASSWORD")
SFTP_DIR = os.getenv("SFTP_DIR")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


def download_and_print_for_two_days_ago():
    """Download all files for two days ago and print a pandas DataFrame."""
    
    # Calculate target date (two days ago)
    target_date = (datetime.utcnow().date() - timedelta(days=7))
    date_str = target_date.strftime("%Y-%m-%d")
    remote_folder = f"{SFTP_DIR}/{date_str}"
    local_dir = date_str
    
    logger.info(f"Target date: {date_str}")
    logger.info(f"Remote folder: {remote_folder}")
    logger.info(f"Local directory: {local_dir}")
    
    rows = []
    ssh = None
    sftp = None
    
    try:
        # Open SSH connection (same as staging/sftp_test.py)
        logger.info("Connecting to SFTP…")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SFTP_HOST, port=SFTP_PORT, username=SFTP_USER, password=SFTP_PASSWORD)
        logger.info("✅ SSH connection established.")
        
        # Open SFTP session
        sftp = ssh.open_sftp()
        logger.info("✅ SFTP session established.")
        
        # Check if remote folder exists
        try:
            listing = sftp.listdir(remote_folder)
            logger.info(f"📂 Remote directory exists: {remote_folder} with {len(listing)} entries")
        except IOError:
            logger.error(f"❌ Remote directory does not exist: {remote_folder}")
            logger.info("No data to display.")
            return
        
        # Ensure local directory exists
        os.makedirs(local_dir, exist_ok=True)
        
        # Download all files
        for name in listing:
            remote_path = f"{remote_folder}/{name}"
            local_path = os.path.join(local_dir, name)
            
            try:
                logger.info(f"⬇️ Downloading: {remote_path} -> {local_path}")
                sftp.get(remote_path, local_path)
                
                local_size = os.path.getsize(local_path)
                remote_size = sftp.stat(remote_path).st_size
                
                rows.append({
                    "filename": name,
                    "remote_path": remote_path,
                    "local_path": local_path,
                    "remote_size_bytes": remote_size,
                    "local_size_bytes": local_size,
                })
                logger.info(f"✅ Downloaded {name}: {local_size} bytes")
            
            except Exception as e:
                logger.error(f"❌ Failed to download {remote_path}: {e}")
                rows.append({
                    "filename": name,
                    "remote_path": remote_path,
                    "local_path": None,
                    "remote_size_bytes": None,
                    "local_size_bytes": None,
                    "error": str(e),
                })
        
        # Build and print DataFrame
        if rows:
            df = pd.DataFrame(rows)
            print("\n" + "="*80)
            print(f"Downloaded files for {date_str}:")
            print("="*80)
            print(df.to_string(index=False))
            print("="*80 + "\n")
            return df
        else:
            logger.info("No files found in remote folder.")
            return pd.DataFrame(rows)
    
    except Exception as e:
        logger.exception(f"❌ SFTP session failed: {e}")
        raise
    
    finally:
        # Clean up connections
        try:
            if sftp:
                sftp.close()
                logger.info("🔒 SFTP session closed.")
        except Exception:
            pass
        
        try:
            if ssh:
                ssh.close()
                logger.info("🔒 SSH connection closed.")
        except Exception:
            pass


if __name__ == "__main__":
    df = download_and_print_for_two_days_ago()
