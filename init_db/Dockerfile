FROM python:3.10

RUN mkdir -p /init
WORKDIR /init

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD [ "python3", "init_db.py" ]