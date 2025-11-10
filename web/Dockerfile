FROM python:3.11-alpine

WORKDIR /tmp

COPY . .

RUN pip install -r web/requirements.txt

CMD ["python3", "-m", "web"]
