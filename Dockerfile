# Use official UV image with Python 3.12 Alpine
FROM ghcr.io/astral-sh/uv:python3.12-alpine

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
COPY uv.lock .
RUN uv sync

COPY init_db.py ./
COPY pingpong/ ./pingpong/
COPY .env ./

EXPOSE 5000

CMD ["uv", "run", "uvicorn", "pingpong.app:app", "--host", "0.0.0.0", "--port", "5000"]

