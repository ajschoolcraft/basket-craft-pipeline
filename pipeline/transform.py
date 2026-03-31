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
