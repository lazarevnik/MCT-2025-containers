FROM python:3.9

WORKDIR /server

RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

COPY server.py .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY init/ ./init/

RUN chmod +x ./init/initdb.sh

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "80"]
