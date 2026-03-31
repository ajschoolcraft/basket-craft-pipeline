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
