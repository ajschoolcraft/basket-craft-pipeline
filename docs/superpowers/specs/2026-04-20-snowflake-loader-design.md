# Snowflake Raw Table Loader — Design Spec

## Overview

Standalone Python script that reads the 8 `raw_*` staging tables from PostgreSQL (Docker or AWS RDS) and loads them into a Snowflake `RAW` schema. This extends the existing pipeline's data availability into Snowflake for cloud-based analytics without modifying the core ELT pipeline.

## Approach

**Standalone script (`load_snowflake.py`)** — runs independently from the main MySQL → Postgres → transform pipeline. Reuses existing `pipeline/config.py` for Postgres connection and table list. Uses `snowflake-connector-python[pandas]` with `write_pandas` for optimized bulk loading.

## Source: PostgreSQL (configurable)

Reads all 8 `raw_*` tables via SQLAlchemy + pandas, same pattern as existing `extract.py`. Source is controlled by existing `POSTGRES_*` env vars, so it works against both local Docker Postgres and AWS RDS without code changes.

| Table | Approx Rows |
|-------|-------------|
| raw_orders | ~32K |
| raw_order_items | ~40K |
| raw_products | 4 |
| raw_order_item_refunds | ~1.7K |
| raw_users | ~31K |
| raw_employees | 20 |
| raw_website_sessions | ~472K |
| raw_website_pageviews | ~1.2M |

## Destination: Snowflake

### Connection

Username + password authentication via env vars:

| Env Var | Example |
|---------|---------|
| `SNOWFLAKE_ACCOUNT` | `QQTELQE-XT10264` |
| `SNOWFLAKE_USER` | `ajschoolcraft` |
| `SNOWFLAKE_PASSWORD` | (secret) |
| `SNOWFLAKE_DATABASE` | `basket_craft` |
| `SNOWFLAKE_SCHEMA` | `raw` |
| `SNOWFLAKE_WAREHOUSE` | `basket_craft_wh` |

### Raw Tables

All 8 tables mirrored with `RAW_` prefix, uppercase identifiers per Snowflake convention. Schemas match the existing PostgreSQL `create_raw_tables.sql` with one type change:

- `TIMESTAMP` → `TIMESTAMP_NTZ` (timezone-naive, matching Postgres behavior)

DDL lives in `sql/create_snowflake_raw_tables.sql`.

### Load Strategy

**Truncate and reload** — for each table:

1. `TRUNCATE TABLE IF EXISTS RAW_<TABLE>` via Snowflake cursor
2. Uppercase all DataFrame column names (Snowflake identifier convention)
3. `write_pandas(conn, df, table_name)` for bulk insert

This matches the existing Postgres load pattern and is idempotent.

### Why `write_pandas`

Snowflake's `write_pandas` stages data as compressed Parquet via `PUT`, then `COPY INTO` the target table. This is significantly faster than row-by-row inserts, especially for `raw_website_pageviews` (~1.2M rows). It requires the `[pandas]` extra of the connector package.

## Project Structure (new files only)

```
basket-craft-pipeline/
    load_snowflake.py                     — standalone entry point
    sql/
        create_snowflake_raw_tables.sql   — Snowflake DDL for raw tables
```

## Execution Flow

1. **Load config** — read `.env`, build Postgres URL + Snowflake connection params
2. **Extract from Postgres** — read all 8 `raw_*` tables into pandas DataFrames
3. **Connect to Snowflake** — authenticate via username/password
4. **Load to Snowflake** — for each table: TRUNCATE, then bulk insert via `write_pandas`
5. **Log summary** — row counts per table, total elapsed time, success/failure

## Error Handling

- **Fail fast** — if Postgres extraction fails, Snowflake load doesn't start
- **Connection cleanup** — Snowflake connection closed in `finally` block
- **Exit codes** — exit 0 on success, exit 1 on failure
- **Logging** — same timestamped INFO/ERROR pattern as `run_pipeline.py`

## Dependencies

New:
- `snowflake-connector-python[pandas]==3.14.0` — Snowflake connector with `write_pandas` support (brings in `pyarrow` transitively)

Existing (reused):
- `sqlalchemy`, `psycopg2-binary`, `pandas`, `python-dotenv`

## Usage

```bash
# One-time: create Snowflake tables
# Run sql/create_snowflake_raw_tables.sql in Snowflake worksheet after USE DATABASE/SCHEMA

# Load data
source .venv/bin/activate
python load_snowflake.py
```

## Decisions Log

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| Integration | Standalone script | Snowflake load is a separate concern; avoids coupling to core ELT pipeline |
| Auth method | Username + password | Simplest; matches project's env var credential pattern |
| Load strategy | Truncate and reload | Matches existing Postgres pattern; idempotent; simple |
| Bulk loader | `write_pandas` | Stages as Parquet internally; much faster than row inserts for large tables |
| Timestamp type | `TIMESTAMP_NTZ` | Matches Postgres timezone-naive `TIMESTAMP`; avoids conversion surprises |
| Identifiers | Uppercase | Snowflake default; `write_pandas` expects column names to match table DDL |
