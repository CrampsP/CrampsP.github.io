from datetime import datetime, timedelta, timezone
from airflow.decorators import dag, task
import pandas as pd
# (optional) import shared helpers

@dag(
    dag_id="your_dag_id",
    schedule="@daily",
    start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
    catchup=True,
    tags=["example"]
)
def your_dag():
    @task()
    def extract():
        # call open_meteo_fetcher.fetch_all to run fetching and concatenation
        from open_meteo_fetcher import fetch_all
        combined_path = fetch_all()
        return combined_path

    @task()
    def transform(data):
        # `data` is the path to the combined CSV returned by extract()
        df = pd.read_csv(data, index_col=0)
        # perform any transformations here; currently pass-through
        return df

    @task()
    def load(data):
        result = data
        return result


    # wiring
    combined = extract()
    transformed = transform(combined)
    load(transformed)

# register / instantiate DAG
dag = your_dag()