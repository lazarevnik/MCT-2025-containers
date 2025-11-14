import pytest
from fastapi.testclient import TestClient
from main import app, get_db_connection, get_redis_connection

client = TestClient(app)

def test_ping():
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"message": "pong"}

def test_visits_initial():
    r = get_redis_connection()
    r.delete("total_visits")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM visits;")
    conn.commit()
    cur.close()
    conn.close()

    response = client.get("/visits")
    assert response.status_code == 200
    assert response.json()["visits"] == 0

def test_visits_after_ping():
    r = get_redis_connection()
    r.delete("total_visits")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM visits;")
    conn.commit()
    cur.close()
    conn.close()

    client.get("/ping")

    response = client.get("/visits")
    assert response.status_code == 200
    assert response.json()["visits"] == 1

def test_redis_and_db_consistency():
    r = get_redis_connection()
    r.delete("total_visits")

    conn1 = get_db_connection()
    cur1 = conn1.cursor()
    cur1.execute("DELETE FROM visits;")
    conn1.commit()
    cur1.close()
    conn1.close()

    client.get("/ping")
    client.get("/ping")

    assert r.get("total_visits") == "2"

    conn2 = get_db_connection()
    cur2 = conn2.cursor()
    cur2.execute("SELECT COUNT(*) FROM visits;")
    db_count = cur2.fetchone()[0]
    cur2.close()
    conn2.close()

    assert db_count == 2
