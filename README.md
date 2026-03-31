# Basket Craft Sales Pipeline

An ELT pipeline that extracts transactional data from a MySQL source database, loads it into PostgreSQL staging tables, and transforms it into a monthly sales summary for analytics.

## What It Does

The pipeline pulls 8 tables from the Basket Craft MySQL database (orders, order items, products, refunds, users, employees, website sessions, and pageviews), stages them as `raw_*` tables in PostgreSQL, then aggregates them into a `monthly_sales_summary` table with metrics like revenue, refunds, COGS, gross profit, and margin by product and month.

The pipeline is idempotent — safe to run repeatedly without duplicating data.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Access to the MySQL source at `db.isba.co`

## Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/ajschoolcraft/basket-craft-pipeline.git
   cd basket-craft-pipeline
   ```

2. **Configure environment variables**

   Create a `.env` file with your MySQL and Postgres credentials:

   ```
   MYSQL_HOST=db.isba.co
   MYSQL_PORT=3306
   MYSQL_USER=analyst
   MYSQL_PASSWORD=your_password
   MYSQL_DATABASE=basket_craft

   POSTGRES_HOST=postgres
   POSTGRES_PORT=5432
   POSTGRES_USER=basket_craft
   POSTGRES_PASSWORD=basket_craft_pw
   POSTGRES_DB=basket_craft_dw
   ```

3. **Start PostgreSQL**

   ```bash
   docker compose up -d postgres
   ```

   This starts a Postgres 16 container and automatically creates the raw staging tables and summary table via init scripts.

## Running the Pipeline

```bash
docker compose run --rm pipeline
```

Expected output:

```
2026-03-31 19:15:37 INFO Starting pipeline run
2026-03-31 19:15:37 INFO Extracting 8 tables from MySQL...
2026-03-31 19:15:40 INFO   orders: 32,313 rows
2026-03-31 19:15:42 INFO   order_items: 40,025 rows
...
2026-03-31 19:18:02 INFO Running transform: transform_monthly_sales.sql
2026-03-31 19:18:02 INFO Transform complete: transform_monthly_sales.sql
2026-03-31 19:18:02 INFO Pipeline complete in 145.0s
```

## Querying Results

Connect to Postgres and explore the summary table:

```bash
docker compose exec postgres psql -U basket_craft -d basket_craft_dw
```

```sql
SELECT year_month, product_name, net_revenue, order_count, margin_pct
FROM monthly_sales_summary
ORDER BY year_month, product_name;
```

## Running Tests

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v
```

## Project Structure

```
├── run_pipeline.py          # Entry point: extract → load → transform
├── pipeline/
│   ├── config.py            # Connection URLs and source table list
│   ├── extract.py           # Read MySQL tables into DataFrames
│   ├── load.py              # Truncate and reload raw_* Postgres tables
│   └── transform.py         # Execute SQL transform against Postgres
├── sql/
│   ├── create_raw_tables.sql       # DDL for 8 raw staging tables
│   ├── create_summary_table.sql    # DDL for monthly_sales_summary
│   └── transform_monthly_sales.sql # Aggregation upsert query
├── tests/                   # Unit tests (mocked) + integration test docs
├── docker-compose.yml       # Postgres + pipeline services
├── Dockerfile               # Pipeline container image
└── requirements.txt         # Python dependencies
```
