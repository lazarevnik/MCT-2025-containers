from flask import Flask, request
from psql import requests_count, add_ip_request


app = Flask(__name__)

@app.route("/ping", methods=["GET"])
def ping():
    add_ip_request(request.remote_addr)
    return "pong\n"

@app.route("/visits", methods=["GET"])
def visits():
    return f"{requests_count()}\n"
