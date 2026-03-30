# Basket Craft Sales Pipeline — Design Spec

## Overview

ELT pipeline that extracts data from the Basket Craft MySQL database, loads all 8 tables into a local PostgreSQL instance (Docker), and transforms them into a `monthly_sales_summary` table for a sales dashboard.

## Approach

**Pure Python + SQL Scripts** — Python handles extract and load; standalone `.sql` files handle transformation inside PostgreSQL.

## Source: MySQL (db.isba.co)

8 tables, full extraction each run:

| Table | Rows | Used in Transform |
|-------|------|-------------------|
| orders | ~32K | No (order-level totals, no product breakdown) |
| order_items | ~40K | Yes (per-item pricing + product FK) |
| products | 4 | Yes (product_name = category) |
| order_item_refunds | ~1.7K | Yes (refund amounts) |
| users | ~31K | No (future use) |
| employees | 20 | No (future use) |
| website_sessions | ~472K | No (future use) |
| website_pageviews | ~1.2M | No (future use) |

Data range: March 2023 – March 2026.

## Destination: PostgreSQL (Docker)

### Raw Layer

All 8 MySQL tables mirrored with `raw_` prefix. Truncated and reloaded each run.

- `raw_orders` — order_id PK, created_at, website_session_id, user_id, primary_product_id, items_purchased, price_usd, cogs_usd
- `raw_order_items` — order_item_id PK, created_at, order_id, product_id, is_primary_item, price_usd, cogs_usd
- `raw_products` — product_id PK, created_at, product_name, description
- `raw_order_item_refunds` — order_item_refund_id PK, created_at, order_item_id, refund_amount_usd
- `raw_users` — user_id PK, first_name, last_name, email, password_salt, password_hash, billing/shipping address fields, created_at
- `raw_employees` — employee_id PK, first_name, last_name, department, salary, email
- `raw_website_sessions` — website_session_id PK, created_at, user_id, is_repeat_session, utm_source, utm_campaign, utm_content, device_type, http_referer
- `raw_website_pageviews` — website_pageview_id PK, created_at, website_session_id, pageview_url

### Analytics Mart: monthly_sales_summary

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PK | Auto-increment |
| year_month | DATE | First day of month (e.g. 2026-01-01) |
| product_name | VARCHAR(100) | From raw_products (acts as category) |
| total_revenue | DECIMAL(12,2) | SUM(oi.price_usd) — gross |
| total_refunds | DECIMAL(12,2) | SUM(r.refund_amount_usd) |
| net_revenue | DECIMAL(12,2) | total_revenue - total_refunds |
| order_count | INTEGER | COUNT(DISTINCT order_id) |
| avg_order_value | DECIMAL(10,2) | net_revenue / order_count |
| total_cogs | DECIMAL(12,2) | SUM(oi.cogs_usd) |
| gross_profit | DECIMAL(12,2) | net_revenue - total_cogs |
| margin_pct | DECIMAL(5,2) | gross_profit / NULLIF(net_revenue, 0) * 100 |
| updated_at | TIMESTAMP | Last pipeline run |

**Unique constraint:** `(year_month, product_name)` — enables idempotent upserts.

### Transform SQL

```sql
INSERT INTO monthly_sales_summary
    (year_month, product_name, total_revenue, total_refunds, net_revenue,
     order_count, avg_order_value, total_cogs, gross_profit, margin_pct, updated_at)
SELECT
    DATE_TRUNC('month', oi.created_at)::DATE       AS year_month,
    p.product_name,
    SUM(oi.price_usd)                              AS total_revenue,
    COALESCE(SUM(r.refund_amount_usd), 0)          AS total_refunds,
    SUM(oi.price_usd) - COALESCE(SUM(r.refund_amount_usd), 0)
                                                    AS net_revenue,
    COUNT(DISTINCT oi.order_id)                     AS order_count,
    (SUM(oi.price_usd) - COALESCE(SUM(r.refund_amount_usd), 0))
        / NULLIF(COUNT(DISTINCT oi.order_id), 0)   AS avg_order_value,
    SUM(oi.cogs_usd)                               AS total_cogs,
    (SUM(oi.price_usd) - COALESCE(SUM(r.refund_amount_usd), 0)) - SUM(oi.cogs_usd)
                                                    AS gross_profit,
    ((SUM(oi.price_usd) - COALESCE(SUM(r.refund_amount_usd), 0)) - SUM(oi.cogs_usd))
        / NULLIF(SUM(oi.price_usd) - COALESCE(SUM(r.refund_amount_usd), 0), 0) * 100
                                                    AS margin_pct,
    NOW()                                           AS updated_at
FROM raw_order_items oi
JOIN raw_products p ON p.product_id = oi.product_id
LEFT JOIN raw_order_item_refunds r ON r.order_item_id = oi.order_item_id
GROUP BY 1, 2
ON CONFLICT (year_month, product_name)
DO UPDATE SET
    total_revenue   = EXCLUDED.total_revenue,
    total_refunds   = EXCLUDED.total_refunds,
    net_revenue     = EXCLUDED.net_revenue,
    order_count     = EXCLUDED.order_count,
    avg_order_value = EXCLUDED.avg_order_value,
    total_cogs      = EXCLUDED.total_cogs,
    gross_profit    = EXCLUDED.gross_profit,
    margin_pct      = EXCLUDED.margin_pct,
    updated_at      = EXCLUDED.updated_at;
```

## Project Structure

```
basket-craft-pipeline/
    docker-compose.yml        — Postgres + pipeline containers
    Dockerfile                — pipeline container image
    .env                      — MySQL source + Postgres destination credentials
    requirements.txt          — Python dependencies
    pipeline/
        __init__.py
        config.py             — load .env, build connection strings
        extract.py            — read all 8 tables from MySQL
        load.py               — truncate & reload into raw_* tables
        transform.py          — execute SQL files against Postgres
    sql/
        create_raw_tables.sql — DDL for raw_* staging tables
        create_summary_table.sql — DDL for monthly_sales_summary
        transform_monthly_sales.sql — the aggregation upsert query
    run_pipeline.py           — entry point: extract -> load -> transform
```

## Infrastructure

### Docker Compose Services

**postgres:**
- Image: `postgres:16`
- Port: `5432:5432`
- Volume: `pgdata` (named, persistent across restarts)
- Init: `sql/create_*.sql` run on first startup

**pipeline:**
- Build: `./Dockerfile`
- Command: `python run_pipeline.py`
- Depends on: `postgres`
- Profile: `run` (not started by default with `docker compose up`)

### Usage

```bash
# First time — start Postgres, create tables
docker compose up -d postgres

# Run the pipeline (manually, whenever needed)
docker compose run pipeline

# Query results
docker compose exec postgres psql -U basket_craft -c "SELECT * FROM monthly_sales_summary;"
```

## Pipeline Execution Flow

1. **Load config** — read `.env`, build MySQL + Postgres connection strings
2. **Extract** — connect to MySQL, read all 8 tables into memory (pandas DataFrames)
3. **Load** — for each table: TRUNCATE `raw_*`, then INSERT extracted data into Postgres
4. **Transform** — execute `transform_monthly_sales.sql` against Postgres
5. **Log summary** — print row counts, elapsed time, success/failure status

## Error Handling

- **Fail fast** — if extract fails, load and transform don't run; previous raw data stays intact
- **Atomic loads** — each table's truncate + insert runs in a transaction; mid-load failure rolls back that table
- **Exit codes** — exit 0 on success, exit 1 on failure
- **Logging** — Python `logging` module, timestamped INFO/ERROR to stdout with row counts and elapsed time per step

## Dependencies

- `sqlalchemy` — database engine abstraction for both MySQL and Postgres
- `pymysql` — MySQL driver
- `psycopg2-binary` — PostgreSQL driver
- `pandas` — used to shuttle data between databases during extract/load
- `python-dotenv` — load `.env` credentials

## Decisions Log

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| Pattern | ELT | Modern; preserves raw data; transforms in SQL |
| Extraction | Full table, all 8 tables | Small data volume (~1.5M total rows); raw layer enables future dashboards |
| Revenue metrics | Gross + Net | Dashboard needs both; refunds table available |
| Margin metrics | COGS, gross profit, margin % | cogs_usd available on order_items; low effort, high value |
| Aggregation key | product_name + month | Products serve as categories (only 4 products) |
| Triggering | Manual | `docker compose run pipeline` on demand |
| Infrastructure | Docker Compose | Postgres + pipeline container; reproducible, portable |
| Error handling | Basic logging | Manual runs mean user is watching stdout |
| Approach | Pure Python + SQL | Simplest option; dbt/orchestrator overkill for this scope |
