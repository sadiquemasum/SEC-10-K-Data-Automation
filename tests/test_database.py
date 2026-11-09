
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError

import app.database as database


def test_get_db_yields_session_and_closes_it():
    mock_db = MagicMock()

    with patch.object(database, "SessionLocal", return_value=mock_db):
        db_generator = database.get_db()

        db = next(db_generator)

        assert db is mock_db

        db_generator.close()

        mock_db.close.assert_called_once()


def test_get_db_closes_session_after_exception():
    mock_db = MagicMock()

    with patch.object(database, "SessionLocal", return_value=mock_db):
        db_generator = database.get_db()

        next(db_generator)

        with pytest.raises(RuntimeError, match="Test error"):
            db_generator.throw(RuntimeError("Test error"))

        mock_db.close.assert_called_once()


def test_check_database_connection_returns_true():
    mock_connection = MagicMock()
    mock_connection.execute.return_value.scalar.return_value = 1

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_connection

    with patch.object(
        database.engine,
        "connect",
        return_value=mock_context,
    ):
        result = database.check_database_connection()

    assert result is True
    mock_connection.execute.assert_called_once()


def test_check_database_connection_returns_false_when_query_fails():
    mock_connection = MagicMock()
    mock_connection.execute.return_value.scalar.return_value = 0

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_connection

    with patch.object(
        database.engine,
        "connect",
        return_value=mock_context,
    ):
        result = database.check_database_connection()

    assert result is False


def test_check_database_connection_handles_sqlalchemy_error():
    with patch.object(
        database.engine,
        "connect",
        side_effect=SQLAlchemyError("Connection failed"),
    ):
        result = database.check_database_connection()

    assert result is False
