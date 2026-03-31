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
