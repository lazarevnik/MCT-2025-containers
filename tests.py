import pytest
import os
import sys

sys.path.append(os.path.dirname(__file__))

from mini_app import app, get_visits_count, log_request

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_ping_endpoint(client):
    response = client.get('/ping')
    assert response.status_code == 200
    assert response.data.decode() == 'pong'

def test_visits_endpoint(client):
    response = client.get('/visits')
    assert response.status_code == 200
    visits_count = int(response.data.decode())
    assert isinstance(visits_count, int)

def test_home_endpoint(client):
    response = client.get('/')
    assert response.status_code == 200
    assert 'Welcome' in response.data.decode()

def test_requests_endpoint(client):
    response = client.get('/requests')
    assert response.status_code == 200

def test_cache_clear_endpoint(client):
    response = client.get('/cache/clear')
    assert response.status_code == 200

def test_visits_count_function():
    count = get_visits_count()
    assert isinstance(count, int)
    assert count >= 0

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=mini_app', '--cov-report=term-missing'])