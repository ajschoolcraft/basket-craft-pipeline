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
