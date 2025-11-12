FROM python:3.14-alpine
WORKDIR /code
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY app.py app.py
COPY config.py config.py
EXPOSE 5000
CMD ["flask", "run", "--debug"]
