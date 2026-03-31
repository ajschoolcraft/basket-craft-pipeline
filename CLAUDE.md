# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Basket Craft Sales Pipeline — an ELT pipeline that extracts 8 tables from a MySQL source (`db.isba.co`), loads them into PostgreSQL raw staging tables, and transforms them into a `monthly_sales_summary` analytics table.

## Commands

```bash
# Start Postgres (must be running before pipeline or tests)
docker compose up -d postgres

# Run the full pipeline (extract → load → transform)
docker compose run --rm pipeline

# Run all unit tests
source .venv/bin/activate
pytest tests/ -v

# Run a single test file
pytest tests/test_config.py -v

# Run a single test
pytest tests/test_config.py::test_get_mysql_url_builds_connection_string -v

# Install dependencies (in virtualenv)
pip install -r requirements.txt

# Query Postgres directly
docker compose exec postgres psql -U basket_craft -d basket_craft_dw
```

## Architecture

The pipeline follows a three-phase ELT pattern orchestrated by `run_pipeline.py`:

1. **Extract** (`pipeline/extract.py`) — reads all 8 MySQL tables into pandas DataFrames using `pd.read_sql_table()`
2. **Load** (`pipeline/load.py`) — for each table, TRUNCATEs the corresponding `raw_*` Postgres table and reloads via `df.to_sql()`, each table in its own transaction
3. **Transform** (`pipeline/transform.py`) — executes `sql/transform_monthly_sales.sql`, which aggregates `raw_order_items` × `raw_products` × `raw_order_item_refunds` into `monthly_sales_summary` using an INSERT...ON CONFLICT upsert

`pipeline/config.py` provides connection URL builders and the `SOURCE_TABLES` list that drives extract and load.

### Idempotency

The pipeline is safe to re-run: raw tables are truncated before reload, and the summary table uses an upsert on `(year_month, product_name)`.

### Database Schema

- **8 raw staging tables** (`raw_orders`, `raw_order_items`, `raw_products`, `raw_order_item_refunds`, `raw_users`, `raw_employees`, `raw_website_sessions`, `raw_website_pageviews`) — created by `sql/create_raw_tables.sql` via Docker init scripts
- **1 analytics table** (`monthly_sales_summary`) — created by `sql/create_summary_table.sql`

### Docker

- `postgres` service starts automatically and runs init SQL on first boot
- `pipeline` service is behind the `run` profile — only starts via `docker compose run`
- Postgres data persists in a `pgdata` volume

## Testing

Unit tests mock all database calls (SQLAlchemy engines/connections). Integration testing is manual — run the pipeline against Docker Postgres and verify via psql queries (documented in `tests/test_pipeline_integration.py`).

## Environment

Credentials live in `.env` (gitignored). `POSTGRES_HOST` is `postgres` inside Docker and `localhost` when running locally.
