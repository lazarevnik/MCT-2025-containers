FROM python:3.13-bookworm

ENV PATH=/root/.local/bin:$PATH

RUN pip install --user pydantic uvicorn[standard] fastapi sqlalchemy alembic pydantic-settings psycopg2-binary pytest pytest-cov
COPY . /opt/app

ENV PYTHONPATH=/opt
WORKDIR /opt/app
