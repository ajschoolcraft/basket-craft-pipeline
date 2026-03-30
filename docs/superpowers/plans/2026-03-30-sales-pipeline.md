# Basket Craft Sales Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an ELT pipeline that extracts 8 tables from a MySQL source, loads them into PostgreSQL raw staging tables, and transforms them into a `monthly_sales_summary` analytics table.

**Architecture:** Python scripts handle extract and load (MySQL → PostgreSQL raw_* tables). SQL files executed by Python handle transformation inside PostgreSQL. Docker Compose runs PostgreSQL and the pipeline container.

**Tech Stack:** Python 3.12, SQLAlchemy, pandas, pymysql, psycopg2-binary, python-dotenv, Docker, PostgreSQL 16

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `requirements.txt` | Create | Python dependencies |
| `Dockerfile` | Create | Pipeline container image |
| `docker-compose.yml` | Create | Postgres + pipeline services |
| `.env` | Modify | Add Postgres credentials alongside existing MySQL creds |
| `sql/create_raw_tables.sql` | Create | DDL for all 8 raw_* staging tables |
| `sql/create_summary_table.sql` | Create | DDL for monthly_sales_summary with unique constraint |
| `sql/transform_monthly_sales.sql` | Create | Aggregation upsert query |
| `pipeline/__init__.py` | Create | Package marker |
| `pipeline/config.py` | Create | Load .env, build connection strings |
| `pipeline/extract.py` | Create | Read all 8 MySQL tables into DataFrames |
| `pipeline/load.py` | Create | Truncate & reload raw_* tables in Postgres |
| `pipeline/transform.py` | Create | Execute SQL transform files against Postgres |
| `run_pipeline.py` | Create | Entry point: extract → load → transform |
| `tests/__init__.py` | Create | Test package marker |
| `tests/test_config.py` | Create | Tests for config module |
| `tests/test_extract.py` | Create | Tests for extract module |
| `tests/test_load.py` | Create | Tests for load module |
| `tests/test_transform.py` | Create | Tests for transform module |
| `tests/test_pipeline_integration.py` | Create | End-to-end integration test |

---

### Task 1: Docker & Infrastructure Setup

**Files:**
- Modify: `.env`
- Create: `requirements.txt`
- Create: `Dockerfile`
- Create: `docker-compose.yml`

- [ ] **Step 1: Add Postgres credentials to .env**

Add Postgres destination credentials below the existing MySQL credentials in `.env`:

```
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=basket_craft
POSTGRES_PASSWORD=basket_craft_pw
POSTGRES_DB=basket_craft_dw
```

Note: `POSTGRES_HOST=postgres` refers to the Docker Compose service name. For running tests or the pipeline locally outside Docker, use `localhost`.

- [ ] **Step 2: Create requirements.txt**

```
sqlalchemy==2.0.40
pymysql==1.1.2
psycopg2-binary==2.9.10
pandas==2.2.3
python-dotenv==1.1.0
pytest==8.3.5
```

- [ ] **Step 3: Create Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pipeline/ pipeline/
COPY sql/ sql/
COPY run_pipeline.py .

CMD ["python", "run_pipeline.py"]
```

- [ ] **Step 4: Create docker-compose.yml**

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./sql/create_raw_tables.sql:/docker-entrypoint-initdb.d/01-create_raw_tables.sql
      - ./sql/create_summary_table.sql:/docker-entrypoint-initdb.d/02-create_summary_table.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 5

  pipeline:
    build: .
    env_file: .env
    environment:
      POSTGRES_HOST: postgres
    depends_on:
      postgres:
        condition: service_healthy
    profiles:
      - run

volumes:
  pgdata:
```

- [ ] **Step 5: Commit**

```bash
git add .env requirements.txt Dockerfile docker-compose.yml
git commit -m "feat: add Docker infrastructure and dependencies"
```

---

### Task 2: SQL Schema Files

**Files:**
- Create: `sql/create_raw_tables.sql`
- Create: `sql/create_summary_table.sql`
- Create: `sql/transform_monthly_sales.sql`

- [ ] **Step 1: Create sql/create_raw_tables.sql**

```sql
-- Raw staging tables: mirrors of MySQL source tables
-- Truncated and reloaded each pipeline run

CREATE TABLE IF NOT EXISTS raw_orders (
    order_id            INTEGER PRIMARY KEY,
    created_at          TIMESTAMP NOT NULL,
    website_session_id  INTEGER,
    user_id             INTEGER,
    primary_product_id  INTEGER,
    items_purchased     SMALLINT NOT NULL,
    price_usd           DECIMAL(6,2) NOT NULL,
    cogs_usd            DECIMAL(6,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_order_items (
    order_item_id   INTEGER PRIMARY KEY,
    created_at      TIMESTAMP NOT NULL,
    order_id        INTEGER,
    product_id      INTEGER,
    is_primary_item SMALLINT NOT NULL,
    price_usd       DECIMAL(6,2) NOT NULL,
    cogs_usd        DECIMAL(6,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_products (
    product_id   INTEGER PRIMARY KEY,
    created_at   TIMESTAMP NOT NULL,
    product_name VARCHAR(50) NOT NULL,
    description  TEXT
);

CREATE TABLE IF NOT EXISTS raw_order_item_refunds (
    order_item_refund_id INTEGER PRIMARY KEY,
    created_at           TIMESTAMP NOT NULL,
    order_item_id        INTEGER,
    refund_amount_usd    DECIMAL(6,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_users (
    user_id                 INTEGER PRIMARY KEY,
    first_name              TEXT,
    last_name               TEXT,
    email                   TEXT,
    password_salt           TEXT,
    password_hash           TEXT,
    billing_street_address  TEXT,
    billing_city            TEXT,
    billing_state           TEXT,
    billing_postal_code     TEXT,
    billing_country         TEXT,
    shipping_street_ddress  TEXT,
    shipping_city           TEXT,
    shipping_state          TEXT,
    shipping_postal_code    TEXT,
    shipping_country        TEXT,
    created_at              TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_employees (
    employee_id INTEGER PRIMARY KEY,
    first_name  VARCHAR(50),
    last_name   VARCHAR(50),
    department  VARCHAR(50),
    salary      DECIMAL(10,2),
    email       VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS raw_website_sessions (
    website_session_id INTEGER PRIMARY KEY,
    created_at         TIMESTAMP NOT NULL,
    user_id            INTEGER,
    is_repeat_session  SMALLINT NOT NULL,
    utm_source         VARCHAR(12),
    utm_campaign       VARCHAR(20),
    utm_content        VARCHAR(15),
    device_type        VARCHAR(15),
    http_referer       VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS raw_website_pageviews (
    website_pageview_id INTEGER PRIMARY KEY,
    created_at          TIMESTAMP NOT NULL,
    website_session_id  INTEGER,
    pageview_url        VARCHAR(50) NOT NULL
);
```

- [ ] **Step 2: Create sql/create_summary_table.sql**

```sql
CREATE TABLE IF NOT EXISTS monthly_sales_summary (
    id              SERIAL PRIMARY KEY,
    year_month      DATE NOT NULL,
    product_name    VARCHAR(100) NOT NULL,
    total_revenue   DECIMAL(12,2) NOT NULL,
    total_refunds   DECIMAL(12,2) NOT NULL,
    net_revenue     DECIMAL(12,2) NOT NULL,
    order_count     INTEGER NOT NULL,
    avg_order_value DECIMAL(10,2) NOT NULL,
    total_cogs      DECIMAL(12,2) NOT NULL,
    gross_profit    DECIMAL(12,2) NOT NULL,
    margin_pct      DECIMAL(5,2) NOT NULL,
    updated_at      TIMESTAMP NOT NULL,
    UNIQUE (year_month, product_name)
);
```

- [ ] **Step 3: Create sql/transform_monthly_sales.sql**

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

- [ ] **Step 4: Verify Postgres starts and tables are created**

```bash
docker compose up -d postgres
docker compose exec postgres psql -U basket_craft -d basket_craft_dw -c "\dt"
```

Expected: all 9 tables listed (8 raw_* + monthly_sales_summary).

- [ ] **Step 5: Commit**

```bash
git add sql/
git commit -m "feat: add SQL schema and transform files"
```

---

### Task 3: Config Module

**Files:**
- Create: `pipeline/__init__.py`
- Create: `pipeline/config.py`
- Create: `tests/__init__.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Create pipeline/__init__.py**

```python
```

(Empty file — package marker only.)

- [ ] **Step 2: Create tests/__init__.py**

```python
```

(Empty file — package marker only.)

- [ ] **Step 3: Write failing test for config**

Create `tests/test_config.py`:

```python
import os
from unittest.mock import patch


def test_get_mysql_url_builds_connection_string():
    env = {
        "MYSQL_HOST": "myhost",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "myuser",
        "MYSQL_PASSWORD": "mypass",
        "MYSQL_DATABASE": "mydb",
    }
    with patch.dict(os.environ, env, clear=False):
        from pipeline.config import get_mysql_url

        url = get_mysql_url()
        assert url == "mysql+pymysql://myuser:mypass@myhost:3306/mydb"


def test_get_postgres_url_builds_connection_string():
    env = {
        "POSTGRES_HOST": "pghost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "pguser",
        "POSTGRES_PASSWORD": "pgpass",
        "POSTGRES_DB": "pgdb",
    }
    with patch.dict(os.environ, env, clear=False):
        from pipeline.config import get_postgres_url

        url = get_postgres_url()
        assert url == "postgresql+psycopg2://pguser:pgpass@pghost:5432/pgdb"


def test_get_source_tables_returns_all_eight():
    from pipeline.config import SOURCE_TABLES

    assert len(SOURCE_TABLES) == 8
    assert "orders" in SOURCE_TABLES
    assert "order_items" in SOURCE_TABLES
    assert "products" in SOURCE_TABLES
    assert "order_item_refunds" in SOURCE_TABLES
    assert "users" in SOURCE_TABLES
    assert "employees" in SOURCE_TABLES
    assert "website_sessions" in SOURCE_TABLES
    assert "website_pageviews" in SOURCE_TABLES
```

- [ ] **Step 4: Run test to verify it fails**

```bash
source .venv/bin/activate
pip install -r requirements.txt
pytest tests/test_config.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.config'`

- [ ] **Step 5: Implement pipeline/config.py**

```python
import os

from dotenv import load_dotenv

load_dotenv()

SOURCE_TABLES = [
    "orders",
    "order_items",
    "products",
    "order_item_refunds",
    "users",
    "employees",
    "website_sessions",
    "website_pageviews",
]


def get_mysql_url():
    return (
        f"mysql+pymysql://{os.environ['MYSQL_USER']}:{os.environ['MYSQL_PASSWORD']}"
        f"@{os.environ['MYSQL_HOST']}:{os.environ['MYSQL_PORT']}"
        f"/{os.environ['MYSQL_DATABASE']}"
    )


def get_postgres_url():
    return (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
        f"@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}"
        f"/{os.environ['POSTGRES_DB']}"
    )
```

- [ ] **Step 6: Run test to verify it passes**

```bash
pytest tests/test_config.py -v
```

Expected: 3 passed.

- [ ] **Step 7: Commit**

```bash
git add pipeline/__init__.py pipeline/config.py tests/__init__.py tests/test_config.py
git commit -m "feat: add config module with MySQL and Postgres URL builders"
```

---

### Task 4: Extract Module

**Files:**
- Create: `pipeline/extract.py`
- Create: `tests/test_extract.py`

- [ ] **Step 1: Write failing test for extract**

Create `tests/test_extract.py`:

```python
from unittest.mock import patch, MagicMock
import pandas as pd


def test_extract_tables_returns_dict_of_dataframes():
    mock_df = pd.DataFrame({"id": [1, 2], "name": ["a", "b"]})

    with patch("pipeline.extract.pd.read_sql_table", return_value=mock_df) as mock_read:
        with patch("pipeline.extract.create_engine") as mock_engine:
            mock_conn = MagicMock()
            mock_engine.return_value.connect.return_value.__enter__ = MagicMock(
                return_value=mock_conn
            )
            mock_engine.return_value.connect.return_value.__exit__ = MagicMock(
                return_value=False
            )

            from pipeline.extract import extract_tables

            result = extract_tables("mysql+pymysql://fake:fake@fake:3306/fake")

    assert isinstance(result, dict)
    assert len(result) == 8
    assert "orders" in result
    assert "website_pageviews" in result
    assert isinstance(result["orders"], pd.DataFrame)


def test_extract_tables_logs_row_counts(caplog):
    import logging

    mock_df = pd.DataFrame({"id": [1, 2, 3]})

    with caplog.at_level(logging.INFO):
        with patch("pipeline.extract.pd.read_sql_table", return_value=mock_df):
            with patch("pipeline.extract.create_engine") as mock_engine:
                mock_conn = MagicMock()
                mock_engine.return_value.connect.return_value.__enter__ = MagicMock(
                    return_value=mock_conn
                )
                mock_engine.return_value.connect.return_value.__exit__ = MagicMock(
                    return_value=False
                )

                from pipeline.extract import extract_tables

                extract_tables("mysql+pymysql://fake:fake@fake:3306/fake")

    assert any("orders" in record.message and "3" in record.message for record in caplog.records)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_extract.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.extract'`

- [ ] **Step 3: Implement pipeline/extract.py**

```python
import logging

import pandas as pd
from sqlalchemy import create_engine

from pipeline.config import SOURCE_TABLES

logger = logging.getLogger(__name__)


def extract_tables(mysql_url):
    logger.info("Extracting %d tables from MySQL...", len(SOURCE_TABLES))
    engine = create_engine(mysql_url)
    tables = {}
    with engine.connect() as conn:
        for table_name in SOURCE_TABLES:
            df = pd.read_sql_table(table_name, con=conn)
            tables[table_name] = df
            logger.info("  %s: %s rows", table_name, f"{len(df):,}")
    engine.dispose()
    return tables
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_extract.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add pipeline/extract.py tests/test_extract.py
git commit -m "feat: add extract module to read MySQL tables into DataFrames"
```

---

### Task 5: Load Module

**Files:**
- Create: `pipeline/load.py`
- Create: `tests/test_load.py`

- [ ] **Step 1: Write failing test for load**

Create `tests/test_load.py`:

```python
from unittest.mock import patch, MagicMock, call
import pandas as pd


def test_load_tables_calls_truncate_and_to_sql():
    tables = {
        "orders": pd.DataFrame({"order_id": [1, 2]}),
        "products": pd.DataFrame({"product_id": [1]}),
    }

    mock_conn = MagicMock()
    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

    with patch("pipeline.load.create_engine", return_value=mock_engine):
        from pipeline.load import load_tables

        load_tables("postgresql+psycopg2://fake:fake@fake:5432/fake", tables)

    executed_sql = [str(c[0][0]) for c in mock_conn.execute.call_args_list]
    assert any("TRUNCATE" in s and "raw_orders" in s for s in executed_sql)
    assert any("TRUNCATE" in s and "raw_products" in s for s in executed_sql)


def test_load_tables_logs_row_counts(caplog):
    import logging

    tables = {
        "orders": pd.DataFrame({"order_id": [1, 2, 3]}),
    }

    mock_conn = MagicMock()
    mock_engine = MagicMock()
    mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

    with caplog.at_level(logging.INFO):
        with patch("pipeline.load.create_engine", return_value=mock_engine):
            from pipeline.load import load_tables

            load_tables("postgresql+psycopg2://fake:fake@fake:5432/fake", tables)

    assert any("raw_orders" in record.message and "3" in record.message for record in caplog.records)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_load.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.load'`

- [ ] **Step 3: Implement pipeline/load.py**

```python
import logging

from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)


def load_tables(postgres_url, tables):
    logger.info("Loading %d tables into PostgreSQL raw_* tables...", len(tables))
    engine = create_engine(postgres_url)
    for table_name, df in tables.items():
        raw_name = f"raw_{table_name}"
        with engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {raw_name}"))
            df.to_sql(raw_name, con=conn, if_exists="append", index=False)
        logger.info("  %s: %s rows loaded", raw_name, f"{len(df):,}")
    engine.dispose()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_load.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add pipeline/load.py tests/test_load.py
git commit -m "feat: add load module to truncate and reload raw_* tables"
```

---

### Task 6: Transform Module

**Files:**
- Create: `pipeline/transform.py`
- Create: `tests/test_transform.py`

- [ ] **Step 1: Write failing test for transform**

Create `tests/test_transform.py`:

```python
from unittest.mock import patch, MagicMock
import os


def test_run_transform_executes_sql_file():
    mock_conn = MagicMock()
    mock_engine = MagicMock()
    mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

    fake_sql = "INSERT INTO monthly_sales_summary SELECT 1;"

    with patch("pipeline.transform.create_engine", return_value=mock_engine):
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__ = MagicMock(return_value=MagicMock(read=MagicMock(return_value=fake_sql)))
            mock_open.return_value.__exit__ = MagicMock(return_value=False)

            from pipeline.transform import run_transform

            run_transform("postgresql+psycopg2://fake:fake@fake:5432/fake")

    executed_sql = str(mock_conn.execute.call_args[0][0])
    assert "INSERT INTO monthly_sales_summary" in executed_sql


def test_run_transform_logs_completion(caplog):
    import logging

    mock_conn = MagicMock()
    mock_engine = MagicMock()
    mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

    fake_sql = "INSERT INTO monthly_sales_summary SELECT 1;"

    with caplog.at_level(logging.INFO):
        with patch("pipeline.transform.create_engine", return_value=mock_engine):
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__ = MagicMock(return_value=MagicMock(read=MagicMock(return_value=fake_sql)))
                mock_open.return_value.__exit__ = MagicMock(return_value=False)

                from pipeline.transform import run_transform

                run_transform("postgresql+psycopg2://fake:fake@fake:5432/fake")

    assert any("transform_monthly_sales.sql" in record.message for record in caplog.records)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_transform.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.transform'`

- [ ] **Step 3: Implement pipeline/transform.py**

```python
import logging
from pathlib import Path

from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def run_transform(postgres_url):
    sql_file = SQL_DIR / "transform_monthly_sales.sql"
    logger.info("Running transform: %s", sql_file.name)
    sql = sql_file.read_text()
    engine = create_engine(postgres_url)
    with engine.begin() as conn:
        conn.execute(text(sql))
    engine.dispose()
    logger.info("Transform complete: %s", sql_file.name)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_transform.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add pipeline/transform.py tests/test_transform.py
git commit -m "feat: add transform module to execute SQL files against Postgres"
```

---

### Task 7: Pipeline Entry Point

**Files:**
- Create: `run_pipeline.py`

- [ ] **Step 1: Implement run_pipeline.py**

```python
import logging
import sys
import time

from pipeline.config import get_mysql_url, get_postgres_url
from pipeline.extract import extract_tables
from pipeline.load import load_tables
from pipeline.transform import run_transform

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    start = time.time()
    logger.info("Starting pipeline run")

    try:
        mysql_url = get_mysql_url()
        postgres_url = get_postgres_url()

        tables = extract_tables(mysql_url)
        load_tables(postgres_url, tables)
        run_transform(postgres_url)

        elapsed = time.time() - start
        logger.info("Pipeline complete in %.1fs", elapsed)
        sys.exit(0)

    except Exception:
        elapsed = time.time() - start
        logger.exception("Pipeline failed (elapsed: %.1fs)", elapsed)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify all unit tests still pass**

```bash
pytest tests/ -v
```

Expected: all tests pass (8 total from tasks 3-6).

- [ ] **Step 3: Commit**

```bash
git add run_pipeline.py
git commit -m "feat: add pipeline entry point with logging and error handling"
```

---

### Task 8: Integration Test with Docker

**Files:**
- Create: `tests/test_pipeline_integration.py`

- [ ] **Step 1: Ensure Docker Postgres is running**

```bash
docker compose up -d postgres
```

Wait for healthy status:

```bash
docker compose ps
```

Expected: `postgres` service status is `healthy`.

- [ ] **Step 2: Run the pipeline end-to-end**

```bash
docker compose run --rm pipeline
```

Expected output (similar to):

```
2026-03-30 14:00:01 INFO Starting pipeline run
2026-03-30 14:00:01 INFO Extracting 8 tables from MySQL...
2026-03-30 14:00:02 INFO   orders: 32,313 rows
2026-03-30 14:00:02 INFO   order_items: 40,025 rows
...
2026-03-30 14:00:08 INFO Loading 8 tables into PostgreSQL raw_* tables...
...
2026-03-30 14:00:12 INFO Running transform: transform_monthly_sales.sql
2026-03-30 14:00:12 INFO Transform complete: transform_monthly_sales.sql
2026-03-30 14:00:12 INFO Pipeline complete in 11.2s
```

- [ ] **Step 3: Verify raw tables have data**

```bash
docker compose exec postgres psql -U basket_craft -d basket_craft_dw -c "
SELECT 'raw_orders' AS tbl, COUNT(*) FROM raw_orders
UNION ALL SELECT 'raw_order_items', COUNT(*) FROM raw_order_items
UNION ALL SELECT 'raw_products', COUNT(*) FROM raw_products
UNION ALL SELECT 'raw_order_item_refunds', COUNT(*) FROM raw_order_item_refunds
UNION ALL SELECT 'raw_users', COUNT(*) FROM raw_users
UNION ALL SELECT 'raw_employees', COUNT(*) FROM raw_employees
UNION ALL SELECT 'raw_website_sessions', COUNT(*) FROM raw_website_sessions
UNION ALL SELECT 'raw_website_pageviews', COUNT(*) FROM raw_website_pageviews;
"
```

Expected: row counts match MySQL source (~32K orders, ~40K order_items, 4 products, etc.).

- [ ] **Step 4: Verify monthly_sales_summary has data**

```bash
docker compose exec postgres psql -U basket_craft -d basket_craft_dw -c "
SELECT year_month, product_name, total_revenue, net_revenue, order_count, avg_order_value, gross_profit, margin_pct
FROM monthly_sales_summary
ORDER BY year_month, product_name
LIMIT 20;
"
```

Expected: rows grouped by month and product name, with non-null values for all metrics. Should see 4 products per month (The Original Gift Basket, The Valentine's Gift Basket, The Birthday Gift Basket, The Holiday Gift Basket — only in months after each product's launch).

- [ ] **Step 5: Verify idempotency — run pipeline again**

```bash
docker compose run --rm pipeline
```

Then check row count hasn't doubled:

```bash
docker compose exec postgres psql -U basket_craft -d basket_craft_dw -c "SELECT COUNT(*) FROM monthly_sales_summary;"
```

Expected: same count as after first run (upsert does not create duplicates).

- [ ] **Step 6: Commit integration test notes**

Create `tests/test_pipeline_integration.py` as a record of the manual integration checks:

```python
"""
Integration tests — run manually against Docker.

Prerequisites:
    docker compose up -d postgres
    docker compose run --rm pipeline

Checks:
    1. Pipeline exits 0
    2. Raw tables have expected row counts
    3. monthly_sales_summary has rows grouped by month + product
    4. Running pipeline twice produces same row count (idempotent)
"""
```

```bash
git add tests/test_pipeline_integration.py
git commit -m "feat: add integration test documentation"
```

---

### Task 9: Final Cleanup & Verification

- [ ] **Step 1: Run full unit test suite**

```bash
pytest tests/ -v
```

Expected: all unit tests pass.

- [ ] **Step 2: Verify .gitignore covers all generated files**

Ensure `.env`, `.venv/`, `__pycache__/`, and `.superpowers/` are all in `.gitignore`.

```bash
grep -E "\.env|\.venv|__pycache__|\.superpowers" .gitignore
```

Expected: all four patterns present.

- [ ] **Step 3: Clean up the earlier docs/pipeline-architecture.md**

The brainstorming produced `docs/pipeline-architecture.md` before we had the real schema. Remove it since the spec supersedes it:

```bash
git rm docs/pipeline-architecture.md
git commit -m "chore: remove outdated architecture doc superseded by design spec"
```

- [ ] **Step 4: Final commit — verify clean working tree**

```bash
git status
```

Expected: `nothing to commit, working tree clean`
