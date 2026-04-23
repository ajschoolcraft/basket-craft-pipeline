# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Basket Craft Sales Pipeline — an ELT pipeline that extracts 8 tables from a MySQL source (`db.isba.co`), loads them into PostgreSQL raw staging tables, and transforms them into a `monthly_sales_summary` analytics table. A separate Snowflake loader replicates the raw tables into Snowflake for cloud-based analytics.

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

# Load raw tables from Postgres into Snowflake
python load_snowflake.py

# dbt commands (must export .env vars first)
export $(grep -v '^#' .env | xargs)
dbt deps          # install dbt packages (dbt-utils)
dbt build         # run all models + tests in DAG order
dbt run           # build models only (no tests)
dbt test          # run tests only
dbt docs generate # generate documentation site
dbt docs serve    # serve docs at http://localhost:8080
```

## Architecture

The pipeline follows a three-phase ELT pattern orchestrated by `run_pipeline.py`:

1. **Extract** (`pipeline/extract.py`) — reads all 8 MySQL tables into pandas DataFrames using `pd.read_sql_table()`
2. **Load** (`pipeline/load.py`) — for each table, TRUNCATEs the corresponding `raw_*` Postgres table and reloads via `df.to_sql()`, each table in its own transaction
3. **Transform** (`pipeline/transform.py`) — executes `sql/transform_monthly_sales.sql`, which aggregates `raw_order_items` × `raw_products` × `raw_order_item_refunds` into `monthly_sales_summary` using an INSERT...ON CONFLICT upsert

`pipeline/config.py` provides connection URL builders and the `SOURCE_TABLES` list that drives extract and load.

### Snowflake Loader

`load_snowflake.py` is a standalone script that reads the 8 `raw_*` tables from Postgres and loads them into Snowflake using truncate-and-reload. It uses `snowflake-connector-python[pandas]` with `write_pandas` for bulk loading.

- **Target:** `SNOWFLAKE_DATABASE`.`SNOWFLAKE_SCHEMA` (e.g. `basket_craft.raw`)
- **Tables:** Same 8 `RAW_*` tables (uppercase Snowflake convention), DDL in `sql/create_snowflake_raw_tables.sql`
- **Credentials:** Snowflake env vars in `.env` — `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`, `SNOWFLAKE_DATABASE`, `SNOWFLAKE_SCHEMA`, `SNOWFLAKE_WAREHOUSE`, and optionally `SNOWFLAKE_ROLE`
- **Postgres source:** Uses the same `POSTGRES_*` env vars as the main pipeline

### dbt Transformation Layer

dbt (with the Snowflake adapter) handles all transformations on top of the raw Snowflake tables. Profile lives at `~/.dbt/profiles.yml` using `env_var()` to read Snowflake credentials from `.env`.

**Project structure:**
- `dbt_project.yml` — project config, profile reference, schema routing
- `packages.yml` — dbt package dependencies (`dbt-utils`)
- `macros/generate_schema_name.sql` — overrides dbt's default schema concatenation so `+schema: staging` creates a `staging` schema (not `analytics_staging`)
- `models/staging/` — 8 views in `basket_craft.staging`, one per raw table. Light cleaning: boolean casts (`is_primary_item`, `is_repeat_session`), column renames (`shipping_street_ddress` → `shipping_street_address`, `created_at` → `refunded_at`), whitespace trimming, computed `profit_usd`
- `models/staging/sources.yml` — declares the 8 raw tables as dbt sources
- `models/staging/schema.yml` — column-level tests (unique, not_null, relationships)
- `models/marts/` — star schema tables in `basket_craft.analytics`

**Star schema (designed for Maya, Head of Merchandising — product profitability):**
- `fct_monthly_product_performance` — grain: month × product × device type × billing region. Measures: revenue, refunds, net revenue, COGS, gross profit, margin %, avg order value, order count
- `dim_products` — product_id, product_name, product_added_at
- `dim_date` — year_month, year, quarter, month_number, month_name (derived from order data, not a date spine)
- `dim_device` — device_type (mobile, desktop)
- `dim_region` — billing_state, billing_country
- `monthly_sales_summary` — legacy summary (month × product, no device/region splits)
- `models/marts/schema.yml` — includes `dbt_utils.unique_combination_of_columns` test on the fact table's composite grain

**Testing:** 40 data tests total — primary key uniqueness/not-null on every model, referential integrity via `relationships` tests, composite grain uniqueness on the fact table. All run via `dbt build`.

### Idempotency

The pipeline is safe to re-run: raw tables are truncated before reload, and the summary table uses an upsert on `(year_month, product_name)`. The Snowflake loader is also idempotent — it truncates each Snowflake table before reloading. dbt models are idempotent by design — views are `CREATE OR REPLACE`, tables are dropped and recreated.

### Database Schema

**Postgres (local pipeline):**
- **8 raw staging tables** (`raw_orders`, `raw_order_items`, `raw_products`, `raw_order_item_refunds`, `raw_users`, `raw_employees`, `raw_website_sessions`, `raw_website_pageviews`) — created by `sql/create_raw_tables.sql` via Docker init scripts
- **1 analytics table** (`monthly_sales_summary`) — created by `sql/create_summary_table.sql`

**Snowflake (3 schemas in `basket_craft` database):**
- `raw` — 8 `RAW_*` tables loaded by `load_snowflake.py`
- `staging` — 8 `STG_*` views managed by dbt
- `analytics` — 6 tables managed by dbt (4 dimensions, 1 fact, 1 legacy summary)

### Docker

- `postgres` service starts automatically and runs init SQL on first boot
- `pipeline` service is behind the `run` profile — only starts via `docker compose run`
- Postgres data persists in a `pgdata` volume

## Testing

Unit tests mock all database calls (SQLAlchemy engines/connections). Integration testing is manual — run the pipeline against Docker Postgres and verify via psql queries (documented in `tests/test_pipeline_integration.py`).

## Environment

Credentials live in `.env` (gitignored). `POSTGRES_HOST` is `postgres` inside Docker and `localhost` when running locally. Snowflake credentials (`SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`, etc.) are also in `.env`. dbt reads these via `env_var()` in `~/.dbt/profiles.yml` — you must `export` them before running dbt commands.

## Design Decisions

- **`generate_schema_name` macro:** Overrides dbt's default behavior of prepending the target schema. Without it, `+schema: staging` would create `analytics_staging` instead of `staging`.
- **No `unique` test on `stg_users.email`:** The source data has 2,597 duplicate emails — this is legitimate (shared accounts), not a data quality issue. `user_id` is the true primary key.
- **`dim_date` from data, not a date spine:** Maya only needs months that have order activity, so `dim_date` is derived from `stg_orders` rather than generated with `dbt_utils.date_spine`.
- **Uppercase SQL in mart models:** Matches the repo convention used in `sql/` directory.
