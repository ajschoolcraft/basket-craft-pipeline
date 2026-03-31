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
