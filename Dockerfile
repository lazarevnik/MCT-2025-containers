FROM python:3.11-slim

WORKDIR /app

COPY requ.txt .
RUN pip install --no-cache-dir -r requ.txt

COPY main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
