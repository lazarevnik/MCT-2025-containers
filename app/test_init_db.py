import pytest
from unittest.mock import MagicMock, patch
import init_db

@pytest.fixture
def mock_db_connection():
    with patch("init_db.psycopg2.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_connect.return_value = mock_conn
        yield mock_conn, mock_cur

def test_wait_for_postgres_success(monkeypatch):
    mock_conn = MagicMock()
    mock_connect = MagicMock(return_value=mock_conn)
    monkeypatch.setattr("init_db.psycopg2.connect", mock_connect)

    init_db.wait_for_postgres()

    mock_connect.assert_called_once_with(
        host=init_db.DB_HOST,
        user=init_db.SUPER_USER,
        password=init_db.SUPER_PASSWORD,
        dbname="postgres"
    )
    mock_conn.close.assert_called_once()



def test_create_table(mock_db_connection):
    mock_conn, mock_cur = mock_db_connection

    init_db.create_table()

    mock_cur.execute.assert_called_with(
        "\n                CREATE TABLE IF NOT EXISTS visits (\n                    id SERIAL PRIMARY KEY,\n                    ip TEXT NOT NULL\n                );\n            "
    )

@patch("init_db.create_table")
@patch("init_db.grant_privileges")
@patch("init_db.create_user_and_db")
@patch("init_db.wait_for_postgres")
def test_main(mock_wait, mock_create_user, mock_grant, mock_create_table):
    init_db.main()
    mock_wait.assert_called_once()
    mock_create_user.assert_called_once()
    mock_grant.assert_called_once()
    mock_create_table.assert_called_once()
