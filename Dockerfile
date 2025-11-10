FROM python:3.13-slim

ENV PATH=/root/.local/bin:$PATH

WORKDIR /opt
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
COPY app /opt/app

ENV PYTHONPATH=/opt
WORKDIR /opt/app
