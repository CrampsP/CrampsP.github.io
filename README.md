# Spencer Payne – Data Science Portfolio

Data science student at BYU–Idaho working across statistics (R), Python, machine learning, data engineering, and business intelligence.

**Live site:** https://crampsp.github.io

## Featured projects

| Project | What it shows | Stack |
|---|---|---|
| [Airflow ETL pipelines](projects/airflow-etl-pipelines/) | Scheduled pipelines that pull weather (Open-Meteo), stock (MongoDB), and SFTP data, transform it, and upsert into Snowflake with backfill support | Python, Apache Airflow 3, Docker, Snowflake, MongoDB |
| [Portlight system monitor](projects/portlight-system-monitor/) | Local, Docker-based Windows network and security dashboard with a token-authenticated collector and tests | Python, PowerShell, Docker, JavaScript |
| [Surfboard sales analysis](projects/surfboard-sales-analysis/) | Loading and combining eight months of retail sales exports for analysis | Python, Polars |

## Coursework

Organized by course in [`coursework/`](coursework/). Highlights:

- **Statistics (R):** [Math 325 analyses](coursework/math-325-intermediate-statistics/analyses/), including t-tests, Wilcoxon, ANOVA, Kruskal-Wallis, chi-squared, and linear and logistic regression. Also [Math 326 designed experiments](coursework/math-326-design-of-experiments/case-studies/).
- **Data wrangling and visualization (R / tidyverse):** [DS 350 weekly projects](coursework/ds-350-data-wrangling-and-visualization/), covering spatial data with `sf`, string and regex work, time series, and chart recreation.
- **Python data science:** [DS 250 client reports](coursework/ds-250-data-science-programming/) (SQL on the Lahman baseball database, missing data in JSON).
- **Machine learning:** [notebooks](coursework/machine-learning-notebooks/) for regression, a neural network, a CNN image classifier, and a transformer language model.
- **Business intelligence:** [Power BI dashboards](coursework/ba-315-business-intelligence-power-bi/).
- **Software fundamentals:** [CSE 111 Python programs with pytest tests](coursework/cse-111-python-programming/).

See [coursework/README.md](coursework/README.md) for the full index.

## Repository layout

```
├── projects/          Standalone projects (best place to start)
├── coursework/        Course work grouped by class
├── docs/              file-manifest.csv: original file name → new location
├── *.qmd, _quarto.yml Quarto source for the portfolio website
└── .github/workflows  Builds and publishes the site to GitHub Pages
```

The website is built with [Quarto](https://quarto.org). Only the site pages are rendered; `projects/` and `coursework/` hold source files and are excluded from the site build.
