FROM python:3.12

WORKDIR /app

COPY app/req.txt .

RUN pip install --no-cache-dir -r req.txt

COPY app .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]