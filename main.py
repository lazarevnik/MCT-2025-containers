#! ./venv/bin/fastapi dev
from typing import Union

from fastapi import FastAPI
from fastapi import Request

app = FastAPI()

@app.get("/ping")
def ping_pong(request : Request):
    ip = request.client.host
    print(ip)
    return "pong"

@app.get('/visits')
def print_visits():
    return 2