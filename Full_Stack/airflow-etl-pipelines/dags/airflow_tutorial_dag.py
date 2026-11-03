# ----------------------------------------------------------------
# tutorial.py
# Airflow 3.0 TaskFlow API — Tutorial DAG
# Demonstrates a dependency-free ETL flow:
# Extract → Transform → Quality Check → Load
# ----------------------------------------------------------------

from airflow.decorators import dag, task
from datetime import datetime, timedelta

# ----------------------------------------------------------------
# DAG Definition
# ----------------------------------------------------------------
@dag(
    dag_id="tutorial",
    description="Tutorial DAG showing a simple ETL flow (no external dependencies)",
    start_date=datetime.utcnow() - timedelta(days=5),  # 5-day backfill
    schedule="@daily",
    catchup=True,
    max_active_runs=1,
    tags=["tutorial", "etl"],
)
def tutorial_etl_dag():
    """
    Educational ETL DAG for students.
    Runs daily and backfills 5 days.
    Each task only logs text — no APIs, no databases, no external dependencies.
    """

    @task(retries=1, retry_delay=timedelta(minutes=1))
    def extract(execution_date=None):
        print(f"\n--- EXTRACT ({execution_date.date()}) ---")
        print("Pretend we fetch raw data here (API call, DB query, etc).")
        records = [f"record_{i}_{execution_date.date()}" for i in range(1, 6)]
        print(f"Extracted records: {records}")
        return records

    @task(retries=1, retry_delay=timedelta(minutes=1))
    def transform(records: list, execution_date=None):
        print(f"\n--- TRANSFORM ({execution_date.date()}) ---")
        print("Pretend we clean or enrich the raw data here.")
        transformed = [r.upper() for r in records]
        print(f"Transformed records: {transformed}")
        return transformed

    @task(retries=1, retry_delay=timedelta(minutes=1))
    def quality_check(records: list, execution_date=None):
        print(f"\n--- QUALITY CHECK ({execution_date.date()}) ---")
        if not records:
            raise ValueError("No records to load!")
        print(f"Quality check passed: {len(records)} records ready for load.")
        return records

    @task(retries=1, retry_delay=timedelta(minutes=1))
    def load(records: list, execution_date=None):
        print(f"\n--- LOAD ({execution_date.date()}) ---")
        print("Pretend we load the records into a warehouse or database.")
        print(f"Loaded {len(records)} records successfully.")
        return "Load complete."

    # DAG flow: extract → transform → quality_check → load
    raw = extract()
    clean = transform(raw)
    checked = quality_check(clean)
    load(checked)

# ----------------------------------------------------------------
# DAG Exposure
# ----------------------------------------------------------------
tutorial_dag = tutorial_etl_dag()