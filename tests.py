import pytest
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from server import app, AppMode

client = TestClient(app)

def test_ping_with_database():
    app.state.mode = AppMode.PROD
    app.state.database = "postgresql://test"
    with patch("server.psycopg2.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        response = client.get("/ping")
        assert response.status_code == 200
        assert response.text == "pong"
        mock_conn.cursor.assert_called_once()
        
def test_visits_dev_mode():
    app.state.mode = AppMode.DEV
    app.state.database = "postgresql://test"
    response = client.get("/visits")
    assert response.status_code == 200
    assert response.text == "-1"

def test_visits_prod_mode_success():
    app.state.mode = AppMode.PROD
    app.state.database = "postgresql://test"
    with patch("server.psycopg2.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            mock_cur = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cur
            mock_cur.fetchone.return_value = [5]

            response = client.get("/visits")
            
            assert response.status_code == 200
            assert response.text == "5"

def test_visits_prod_mode_database_error():
    app.state.mode = AppMode.PROD
    app.state.database = "postgresql://test"
    with patch("server.psycopg2.connect") as mock_connect:
        mock_connect.side_effect = Exception("DB error")
        response = client.get("/visits")
        assert response.status_code == 200
        assert response.text == "0"

def test_ping_without_database():
    app.state.mode = AppMode.PROD
    app.state.database = ""
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.text == "pong"
    
def test_visits_no_database():
    app.state.mode = AppMode.PROD
    app.state.database = ""
    response = client.get("/visits")
    assert response.status_code == 200
    assert response.text == "0"

def test_insert_visit_without_database():
    app.state.mode = AppMode.PROD
    app.state.database = ""
    from server import insert_visit
    insert_visit("127.0.0.1")

def test_count_visits_without_database():
    app.state.mode = AppMode.PROD
    app.state.database = ""
    from server import count_visits
    result = count_visits()
    assert result.text == "0"