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
