from fastapi import FastAPI, Request
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from datetime import datetime
from db import RequestDb, Base

app = FastAPI()
engine = create_engine("postgresql+psycopg://user:pass@db:5432/posdb", echo=True)
Base.metadata.create_all(engine)

@app.get("/")
def main():
    return "Server is running"

@app.get("/ping")
def ping(request: Request):
    global engine
    ip = request.client.host
    with Session(engine) as session:
        incoming_request = RequestDb(ip=ip, time=datetime.now(), request="ping")
        session.add(incoming_request)
        session.commit()
    return "pong" 

@app.get("/visits")
def visits(request: Request):
    global engine
    ip = request.client.host
    with Session(engine) as session:
        incoming_request = RequestDb(ip=ip, time=datetime.now(), request="visits")
        count = session.query(RequestDb).filter(RequestDb.request == "ping").count()
        session.add(incoming_request)
        session.commit()
    return count

