# Spencer Payne – Data Science Portfolio

[![Website](https://img.shields.io/badge/Portfolio-crampsp.github.io-18bc9c)](https://crampsp.github.io)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Spencer%20Payne-0A66C2)](https://www.linkedin.com/in/spencer-payne-95090428b)

Data Science student at BYU–Idaho, specializing in business analytics. I work in **Python, R, and SQL** across statistics, data wrangling, visualization, machine learning, and data engineering.

**👉 The best way to see this work is the live site: [crampsp.github.io](https://crampsp.github.io)**. Every project there has a written summary, charts, and code.

## Highlights

| Project | Skills shown |
|---|---|
| [Automated ETL pipelines](Full_Stack/airflow-etl-pipelines/) | Apache Airflow 3, Docker, Snowflake `MERGE` upserts, MongoDB over SSH, SFTP, backfills |
| [Portlight network dashboard](Full_Stack/portlight-system-monitor/) | Python server, PowerShell collector, hardened Docker container, JavaScript UI, 14 tests |
| [King County home price model](Machine_Learning/housing-price-prediction.qmd) | Feature engineering, XGBoost, R² ≈ 0.90 on held-out data |
| [Newly reported Medicaid drugs](Story_Telling/medicaid-drug-reporting.qmd) | Live public data from CMS, tidyverse, data storytelling |
| [Caffeine and reaction time](Statistical_Analysis/two-way-anova-analysis.Rmd) | Experiment design, two-way ANOVA, assumption checks |
| [Baseball relationships in SQL](Data_Exploration/baseball-sql-relationships.qmd) | SQL on SQLite, pandas, Lets-Plot |

## Repository layout

Each folder matches a section of the website. The project pages sit at the top of each folder, and supporting code and coursework sit in subfolders.

```
├── Statistical_Analysis/   Hypothesis tests, regression, designed experiments (R)
│   └── coursework/         Math 221D, Math 325, Math 326 notebooks and practice
├── Data_Cleansing/         Multi-format import, reshaping, missing data
├── Data_Exploration/       SQL, joins, and exploratory analysis
├── Story_Telling/          Visual reports
│   └── coursework/         DS 350 weekly work, BA 315 Power BI dashboards
├── Machine_Learning/       Model write-ups
│   └── notebooks/          Original Jupyter/Colab notebooks
├── Full_Stack/             Engineering projects
│   ├── airflow-etl-pipelines/
│   ├── portlight-system-monitor/
│   └── coursework/         CSE 111 Python, AI 101–102
├── Competition/            Timed coding challenges and contests
├── index.qmd, resume.qmd   Home and resume pages
└── _quarto.yml             Site configuration
```

## How the site is built

The site is built with [Quarto](https://quarto.org) and published to GitHub Pages by a GitHub Actions workflow on every push to `main`. Analyses are run locally and their results are stored in `_freeze/`, so the published pages always match the code without re-running anything on GitHub.

To rebuild locally (R 4.4+ and Python 3.11+):

```bash
quarto render
```

[docs/file-manifest.csv](docs/file-manifest.csv) maps original course file names to their place in this repo.
