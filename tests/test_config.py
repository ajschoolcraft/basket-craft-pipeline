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
