import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def app_client():
    return client

def test_root(app_client):
    response = app_client.get("/")
    assert response.status_code == 200
    assert response.text == "Hello, World!"

def test_ping(app_client):
    response = app_client.get("/ping")
    assert response.status_code == 200
    assert response.text == "pong"

def test_visits(app_client):
    response = app_client.get("/visits")
    assert response.status_code == 200
