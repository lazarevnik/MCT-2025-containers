FROM python:3.9-slim

WORKDIR /pinpong

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pinpong.py .

EXPOSE 5000

CMD ["python", "pinpong.py"]
