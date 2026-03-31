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
