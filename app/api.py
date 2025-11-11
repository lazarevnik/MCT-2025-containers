from fastapi import FastAPI, Request
from app.core import ping, visits

api = FastAPI()


@api.get("/ping")
def api_ping(req: Request) -> str:
    return ping(req.client.host, req.client.port)


@api.get("/visits")
def api_visits(req: Request) -> int:
    return visits(req.client.host, req.client.port)
