from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from datetime import datetime
from initdb.db import RequestDb
import redis

app = FastAPI()
engine = create_engine("postgresql+psycopg://user:pass@db:5432/posdb", echo=True)

pool = redis.ConnectionPool(host='redis', port=6379, db=0)
r = redis.Redis(connection_pool=pool)

with Session(engine) as session:
    count = session.query(RequestDb).filter(RequestDb.request == "ping").count()
    r.set("visits", count)

@app.get("/")
def main():
    return "Server is running"

@app.get("/ping", response_class=PlainTextResponse)
def ping(request: Request):
    global engine
    ip = request.client.host
    with Session(engine) as session:
        incoming_request = RequestDb(ip=ip, time=datetime.now(), request="ping")
        session.add(incoming_request)
        session.commit()
        r.incr("visits")
    return "pong"

@app.get("/visits")
def visits(request: Request):
    return r.get("visits")

