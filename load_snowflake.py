import logging
import os
import sys
import time

import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from sqlalchemy import create_engine

from dotenv import load_dotenv

load_dotenv(override=True)

from pipeline.config import SOURCE_TABLES, get_postgres_url

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

RAW_TABLES = [f"raw_{t}" for t in SOURCE_TABLES]


def get_snowflake_connection():
    params = {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "password": os.environ["SNOWFLAKE_PASSWORD"],
        "database": os.environ["SNOWFLAKE_DATABASE"],
        "schema": os.environ["SNOWFLAKE_SCHEMA"],
        "warehouse": os.environ["SNOWFLAKE_WAREHOUSE"],
    }
    if os.environ.get("SNOWFLAKE_ROLE"):
        params["role"] = os.environ["SNOWFLAKE_ROLE"]
    return snowflake.connector.connect(**params)


def extract_from_postgres(postgres_url):
    logger.info("Extracting %d raw tables from PostgreSQL...", len(RAW_TABLES))
    engine = create_engine(postgres_url)
    tables = {}
    with engine.connect() as conn:
        for table_name in RAW_TABLES:
            df = pd.read_sql_table(table_name, con=conn)
            tables[table_name] = df
            logger.info("  %s: %s rows", table_name, f"{len(df):,}")
    engine.dispose()
    return tables


def load_to_snowflake(tables):
    logger.info("Loading %d tables into Snowflake...", len(tables))
    conn = get_snowflake_connection()
    try:
        for table_name, df in tables.items():
            sf_table = table_name.upper()
            conn.cursor().execute(f"TRUNCATE TABLE IF EXISTS {sf_table}")
            if len(df) > 0:
                df.columns = [c.upper() for c in df.columns]
                write_pandas(conn, df, sf_table)
            logger.info("  %s: %s rows loaded", sf_table, f"{len(df):,}")
    finally:
        conn.close()


def main():
    start = time.time()
    logger.info("Starting Snowflake load")

    try:
        postgres_url = get_postgres_url()
        tables = extract_from_postgres(postgres_url)
        load_to_snowflake(tables)

        elapsed = time.time() - start
        logger.info("Snowflake load complete in %.1fs", elapsed)
        sys.exit(0)

    except Exception:
        elapsed = time.time() - start
        logger.exception("Snowflake load failed (elapsed: %.1fs)", elapsed)
        sys.exit(1)


if __name__ == "__main__":
    main()
