# DAG 3.0 / TaskFlow API Guide for Students

## Official References
- [TaskFlow API tutorial — Apache Airflow](https://airflow.apache.org/docs/apache-airflow/stable/tutorial/taskflow.html)
- [DAGs — core concepts](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html)
- [Airflow decorators (`@dag`, `@task`)](https://airflow.apache.org/docs/apache-airflow/stable/_api/airflow/decorators/index.html)

---

## 1. What are `@dag` and `@task`?

- `@dag`: Decorator that turns a Python function into a DAG factory. The decorated function defines tasks and dependencies.
- `@task`: Decorator that wraps a function into an Airflow task. Its return value is pushed to XCom automatically.

These features are part of the Airflow TaskFlow API, which simplifies writing DAGs in a Pythonic style.

---

## 2. DAG File Structure & Code Order

```python
from datetime import datetime, timedelta, timezone
from airflow.decorators import dag, task
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
        ...
        return data

    @task()
    def load(data):
        ...
        return result

    # wiring
    load(extract())

# register / instantiate DAG
dag = your_dag()
```

Key points:
- Task definitions live *inside* the DAG function.
- You express dependencies by calling tasks.
- The DAG function must be called at top level for Airflow to detect the DAG.

---

## 3. Advantages & Differences vs Traditional Operators

- ✅ **Less boilerplate**: No need to create PythonOperator, pass `op_kwargs`, or manually push/pull XComs.
- ✅ **Better readability**: Your tasks look like normal Python functions.
- ✅ **Automatic XCom wiring**: Return values flow to downstream tasks.
- ⚠️ But you still control scheduling, retries, catchup as before via DAG parameters.

---

## 4. Common Pitfalls & Tips

- Not calling the DAG factory at module level → DAG doesn’t load.
- Placing `@task` functions outside the DAG → they won’t belong to it.
- Assuming tasks execute at import time — they don’t; they only build the DAG graph at parse time.
- Overloading the DAG function with logic (e.g., network calls) — only define task functions inside it.

---

## 5. Example + Link to Our Course DAGs

See `stocks_to_mongo_dag_v3.py`, which wraps our existing `fetch_and_insert_stock_data` using `@dag` / `@task`. Use this pattern to refactor future DAGs.
