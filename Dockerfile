FROM python:3.13-bookworm

ENV PATH=/root/.local/bin:$PATH

RUN pip install --user pydantic uvicorn[standard] fastapi sqlalchemy alembic pydantic-settings psycopg2-binary pytest pytest-cov
COPY alembic /opt/alembic
COPY alembic.ini /opt/alembic.ini
COPY app /opt/app
COPY tests /opt/tests

ENV PYTHONPATH=/opt
WORKDIR /opt
