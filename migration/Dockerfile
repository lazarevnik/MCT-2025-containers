FROM python:3.12.12-slim

WORKDIR server

RUN  apt update \
     && apt install curl -y \
     && curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH=/root/.local/bin:$PATH
ENV UV_PROJECT_ENVIRONMENT=/usr/local/

COPY pyproject.toml .
COPY uv.lock .
RUN uv sync --frozen

COPY ./migration .

CMD ["alembic", "upgrade", "head"]
