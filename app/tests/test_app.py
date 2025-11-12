import pytest
from unittest.mock import MagicMock, patch

def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Hello! Use /ping and /visits endpoints.' in response.data

def test_ping_route(client):
    with patch('app.get_db_connection') as mock_db, \
         patch('app.get_redis_connection') as mock_redis, \
         patch('app.update_visits_cache') as mock_update_cache:

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_db.return_value = mock_conn

        response = client.get('/ping')
        
        assert response.status_code == 200
        assert response.data == b'pong'

def test_visits_route_with_cache(client):
    with patch('app.get_redis_connection') as mock_redis, \
         patch('app.get_db_connection') as mock_db:

        mock_redis.return_value.get.return_value = '42'

        response = client.get('/visits')
        
        assert response.status_code == 200
        assert response.data == b'42'

def test_visits_route_without_cache(client):
    with patch('app.get_redis_connection') as mock_redis, \
         patch('app.get_db_connection') as mock_db, \
         patch('app.update_visits_cache') as mock_update_cache:

        mock_redis.return_value.get.return_value = None

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [25]
        mock_db.return_value = mock_conn

        response = client.get('/visits')
        
        assert response.status_code == 200

def test_visits_cache_route(client):
    with patch('app.get_redis_connection') as mock_redis:
        mock_redis.return_value.get.return_value = '30'

        response = client.get('/visits/cache')
        
        assert response.status_code == 200
        assert response.data == b'From cache: 30'

def test_clear_cache_route(client):
    with patch('app.get_redis_connection') as mock_redis:
        response = client.get('/cache/clear')
        
        assert response.status_code == 200
        assert response.data == b'Cache cleared'
        mock_redis.return_value.delete.assert_called_once_with('visits_count')


def test_update_visits_cache_with_count(client):
    with patch('app.get_redis_connection') as mock_redis:
        from app import update_visits_cache
        update_visits_cache(50)
        
        mock_redis.return_value.set.assert_called_once_with('visits_count', 50, ex=300)

def test_update_visits_cache_without_count(client):
    with patch('app.get_db_connection') as mock_db, \
         patch('app.get_redis_connection') as mock_redis:

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [100]
        mock_db.return_value = mock_conn

        from app import update_visits_cache
        update_visits_cache()

def test_get_visits_count_redis_error(client):
    with patch('app.get_redis_connection') as mock_redis, \
         patch('app.get_db_connection') as mock_db, \
         patch('app.update_visits_cache') as mock_update_cache:

        mock_redis.return_value.get.side_effect = Exception("Redis error")

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [77]
        mock_db.return_value = mock_conn

        from app import get_visits_count
        result = get_visits_count()

def test_update_visits_cache_db_error(client):
    with patch('app.get_db_connection') as mock_db, \
         patch('app.get_redis_connection') as mock_redis:

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("DB error")
        mock_db.return_value = mock_conn

        from app import update_visits_cache
        update_visits_cache()