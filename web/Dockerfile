FROM python:3.11-alpine

WORKDIR /web

COPY ./web/* .

RUN pip install -r requirements.txt

CMD ["python3", "main.py"]
