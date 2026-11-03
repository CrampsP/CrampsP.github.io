# Student Airflow Template

This is a ready-to-run Apache Airflow + Docker environment designed for classroom use. Students can use this to run Airflow DAGs that connect to MongoDB and process stock data.

## Before You Start

1. Clone the repo or click "Use this template"
2. Open the cloned repo in VS Code

3. Run the scripts/generate_fernet_key.py script to generate a fernet key. This key is used to encrypt sensitive data in Airflow, such as passwords and connection strings. You can run this script in your terminal or command prompt.

you might need to install the `cryptography` library if you don't have it already. You can do this by running:
```bash
pip install cryptography
```

Then, run the script:
```bash
python scripts/generate_fernet_key.py
```
4. Copy the generated fernet key and paste it into the `example.env` file in the `FERNET_KEY` variable. Then rename the file to just `.env` (remove the `editme` part).

5. Make sure you have Docker and Docker Compose installed on your machine. You can download them from the official Docker website. Here is the link: https://docs.docker.com/get-docker/


## ✅ Getting Airflow Started

1. In that VS Code Terminal Run:

```bash
docker compose up --build -d
```

2. Open [http://localhost:8080](http://localhost:8080)

Login with:
- **Username:** `airflow`
- **Password:** `airflow`


## shut down

```bash
docker compose down
```

<!-- https://airflow.apache.org/docs/apache-airflow/stable/tutorial/index.html -->
<!-- https://airflow.apache.org/docs/apache-airflow/stable/tutorial/fundamentals.html -->
<!-- https://www.youtube.com/watch?v=ouERCRRvkFQ -->
<!-- https://www.youtube.com/watch?v=RXWYPZ3T9ys -->