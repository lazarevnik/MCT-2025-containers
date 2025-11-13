FROM python:3.11-slim
WORKDIR /init
COPY db_init/init_db.py .
RUN pip install psycopg2-binary
CMD ["python", "init_db.py"]
