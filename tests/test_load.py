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
