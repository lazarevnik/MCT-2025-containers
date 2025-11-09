FROM python:3.13

WORKDIR /appdir

COPY requirements.txt /appdir/requirements.txt
RUN pip install --no-cache-dir -r /appdir/requirements.txt

COPY ./app /appdir/app

EXPOSE 80

CMD [ "fastapi", "run", "app/app.py", "--port=80" ]
