from fastapi import FastAPI, Request
from db import get_db
from fastapi.responses import PlainTextResponse

app = FastAPI()

@app.get("/ping",
         response_class=PlainTextResponse)
async def ping(request: Request):
    ip = request.client.host
    conn = await get_db()
    await conn.execute("INSERT INTO visits(ip) VALUES($1)", ip)
    return 'pong'

@app.get("/visits")
async def visits():
    conn = await get_db()
    row = await conn.fetchrow("SELECT COUNT(*) AS c FROM visits")
    return row["c"]

@app.get("/")
async def root():
    return {"status" : "ok"}