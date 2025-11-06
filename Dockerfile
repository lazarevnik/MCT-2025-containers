FROM python:3-slim

CMD ["pip", "install", "-r", "requiremets.txt"]

WORKDIR /app
COPY . .

ENTRYPOINT ["fastapi", "run", "main.py"]