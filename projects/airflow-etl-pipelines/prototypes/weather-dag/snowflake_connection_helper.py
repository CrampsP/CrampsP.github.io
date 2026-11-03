import os
import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import snowflake.connector

# optional extras
from dotenv import load_dotenv
import logging


# -------------------------------------------------------------------
# Snowflake_keypair
# -------------------------------------------------------------------
def get_snowflake_connection(schema: str = None):
    """
    Connect to Snowflake using ONLY key-pair authentication.
    Requires one of:
      - SNOWFLAKE_PRIVATE_KEY_PATH
      - SNOWFLAKE_PRIVATE_KEY_B64
    Optional:
      - SNOWFLAKE_PRIVATE_KEY_PASSPHRASE
    """
    common = dict(
        user=os.getenv("SNOWFLAKE_USER"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        role=os.getenv("SNOWFLAKE_ROLE"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "RAW_WH"),
        database=os.getenv("SNOWFLAKE_DATABASE", "RAW"),
        schema=schema or os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
    )

    key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")
    key_b64  = os.getenv("SNOWFLAKE_PRIVATE_KEY_B64")
    key_pass = os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE")

    if not key_path and not key_b64:
        raise ValueError(
            "❌ Must set SNOWFLAKE_PRIVATE_KEY_PATH or SNOWFLAKE_PRIVATE_KEY_B64 in environment"
        )

    if key_path:
        with open(key_path, "rb") as f:
            key_pem = f.read()
    else:
        key_pem = base64.b64decode(key_b64)

    private_key = serialization.load_pem_private_key(
        key_pem,
        password=(key_pass.encode() if key_pass else None),
        backend=default_backend(),
    ).private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    return snowflake.connector.connect(private_key=private_key, **common)


# -------------------------------------------------------------------
# Get table names from schema
# -------------------------------------------------------------------
def get_table_names(connection=None, schema: str = None, database: str = None):
    """
    Get a list of table names from a Snowflake schema.
    
    Parameters:
    -----------
    connection : snowflake.connector.connection (optional)
        Existing Snowflake connection. If None, will create a new connection.
    schema : str (optional)
        Schema name to query. If None, uses the schema from environment variables.
    database : str (optional)
        Database name to query. If None, uses the database from environment variables.
    
    Returns:
    --------
    list of str
        List of table names in the specified schema
    """
    # Create connection if not provided
    close_connection = False
    if connection is None:
        connection = get_snowflake_connection(schema=schema)
        close_connection = True
    
    try:
        cursor = connection.cursor()
        
        # Build the SHOW TABLES query
        if database and schema:
            query = f"SHOW TABLES IN {database}.{schema}"
        elif schema:
            query = f"SHOW TABLES IN SCHEMA {schema}"
        else:
            query = "SHOW TABLES"
        
        # Execute the query
        cursor.execute(query)
        
        # Fetch all results
        results = cursor.fetchall()
        
        # Extract table names from the results (name is the second column, index 1)
        table_names = [row[1] for row in results]
        
        cursor.close()
        
        return table_names
        
    finally:
        # Close connection only if we created it
        if close_connection:
            connection.close()


# -------------------------------------------------------------------
# Main example usage
# -------------------------------------------------------------------
if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    
    # Example 1: Get tables from default schema (from environment variables)
    print("=" * 60)
    print("Tables in default schema:")
    print("=" * 60)
    
    try:
        tables = get_table_names()
        for table in tables:
            print(f"  - {table}")
        print(f"\nTotal tables found: {len(tables)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 2: Get tables from a specific schema using an existing connection
    print("\n" + "=" * 60)
    print("Tables using existing connection:")
    print("=" * 60)
    
    try:
        conn = get_snowflake_connection()
        schema_name = os.getenv("SNOWFLAKE_SCHEMA", "RAW")
        database_name = os.getenv("SNOWFLAKE_DATABASE", "SNOWBEARAIR_DB")
        
        tables = get_table_names(connection=conn, schema=schema_name, database=database_name)
        for table in tables:
            print(f"  - {table}")
        print(f"\nTotal tables found: {len(tables)}")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")