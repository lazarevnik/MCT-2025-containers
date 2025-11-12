FROM python:3.12-slim

WORKDIR /init

COPY ./requirements.txt /init/requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /init/requirements.txt

COPY ./app /app
COPY ./init/init_db.py /init/init_db.py

ENV PYTHONPATH="${PYTHONPATH}:/"

CMD ["python", "/init/init_db.py"]