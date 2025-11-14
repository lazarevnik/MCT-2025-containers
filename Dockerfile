FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY main.py .
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "main:app"]
