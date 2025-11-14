FROM python:3

WORKDIR /app
# installing requirements

# installing prerequisites for MySQLdb
RUN apt update
RUN apt-get install -y python3-dev default-libmysqlclient-dev build-essential pkg-config
COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# copying project to image
COPY . .

# forwarding ports
EXPOSE 80

ENTRYPOINT ["fastapi", "run", "main.py", "--port", "80"]