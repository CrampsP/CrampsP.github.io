# Airflow ETL Pipelines

Apache Airflow 3 pipelines, run in Docker, that extract data from external sources, clean it with pandas, and load it into Snowflake.

## Pipelines

| DAG file | Source → destination | Schedule |
|---|---|---|
| [`weather_forecast_etl_dag.py`](dags/weather_forecast_etl_dag.py) | Open-Meteo API (10 US cities) → Snowflake, upserted with `MERGE` and backfilled to a target start date | Weekly (Sun 19:00 UTC) |
| [`stock_market_etl_dag.py`](dags/stock_market_etl_dag.py) | MongoDB (through an SSH tunnel) → Snowflake `RAW.STOCK_DATA`, upserted with `MERGE` | Weekly |
| [`news_sftp_ingestion_dag.py`](dags/news_sftp_ingestion_dag.py) | SFTP server (latest dated CSV drop) → Snowflake table created from the DataFrame schema | Weekly |
| [`sftp_to_snowflake_loader_dag.py`](dags/sftp_to_snowflake_loader_dag.py) | SFTP → Snowflake bulk insert, split into four tasks | Manual |
| [`weekly_backfill_catchup_dag.py`](dags/weekly_backfill_catchup_dag.py) | Demonstrates `catchup` and backfill behavior | Weekly |

The shared connection helpers in [`dags/utils.py`](dags/utils.py) cover Snowflake (password or key-pair auth), the MongoDB SSH tunnel, and the Finnhub API key.

## Layout

```
dags/          Production DAGs
docs/          Airflow 3 setup, scheduling/catch-up notes, quick reference, changelog
prototypes/    Early weather-pipeline prototype and sample output
archive/       Earlier DAG versions kept to show how the pipelines evolved
scripts/       Fernet key generator, MongoDB SSH tunnel helper
tests/         SFTP connectivity tests
```

## Running locally

See [SETUP.md](SETUP.md). In short: copy `example.env` to `.env` and fill in the values, generate a Fernet key with `python scripts/generate_fernet_key.py`, then run `docker compose up`.

All credentials are read from environment variables. None are stored in this repository.

*Built for a BYU–Idaho data engineering course. The Docker and compose scaffold came from the course template (MIT License).*
