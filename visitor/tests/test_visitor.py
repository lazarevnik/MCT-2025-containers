import pytest
import os
from unittest.mock import patch, MagicMock
import sys

sys.path.append('..')
from visitor import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_db_session():
    with patch('visitor.SessionLocal') as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        yield mock_session


@pytest.fixture
def mock_redis():
    with patch('visitor.redis_client') as mock_redis_client:
        yield mock_redis_client


class TestVisitorApp:

    def test_home_route(self, client, mock_db_session):
        mock_db_session.query.return_value.count.return_value = 10
        mock_db_session.query.return_value.distinct.return_value.count.return_value = 5

        response = client.get('/')

        assert response.status_code == 200
        assert 'Всего посещений: 10' in response.data.decode()
        assert 'Уникальных посетителей: 5' in response.data.decode()
        mock_db_session.close.assert_called_once()

    def test_ping_route(self, client, mock_db_session, mock_redis):
        response = client.get('/ping')

        assert response.status_code == 200
        assert response.data.decode() == 'pong'

        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.close.assert_called_once()

        mock_redis.delete.assert_called_once_with("visits_count")

    def test_visits_route_with_cache(self, client, mock_redis):
        mock_redis.get.return_value = "15"

        response = client.get('/visits')

        assert response.status_code == 200
        assert response.data.decode() == '15'
        mock_redis.get.assert_called_once_with("visits_count")

    def test_visits_route_without_cache(self, client, mock_db_session, mock_redis):
        mock_redis.get.return_value = None
        mock_db_session.query.return_value.count.return_value = 20

        response = client.get('/visits')

        assert response.status_code == 200
        assert response.data.decode() == '20'

        mock_redis.set.assert_called_once_with("visits_count", 20)
        mock_db_session.close.assert_called_once()

    @patch.dict(
        os.environ,
        {
            'POSTGRES_USER': 'test_user',
            'POSTGRES_PASSWORD': 'test_pass',
            'POSTGRES_HOST': 'test_host',
            'POSTGRES_PORT': '5433',
            'POSTGRES_DB': 'test_db',
            'REDIS_HOST': 'test_redis',
            'REDIS_PORT': '6380',
        },
    )
    def test_environment_variables(self):
        import importlib
        import visitor

        importlib.reload(visitor)

        assert visitor.DB_USER == 'test_user'
        assert visitor.DB_PASS == 'test_pass'
        assert visitor.DB_HOST == 'test_host'
        assert visitor.DB_PORT == '5433'
        assert visitor.DB_NAME == 'test_db'
        assert visitor.REDIS_HOST == 'test_redis'
        assert visitor.REDIS_PORT == '6380'

    def test_home_route_handles_db_errors(self, client, mock_db_session):
        mock_db_session.query.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            client.get('/')

    def test_visits_route_handles_db_errors(self, client, mock_db_session, mock_redis):
        mock_redis.get.return_value = None
        mock_db_session.query.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            client.get('/visits')


if __name__ == '__main__':
    pytest.main([__file__])
