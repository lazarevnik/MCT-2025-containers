# main.py
import os
from fastapi import FastAPI, Request
from sqlalchemy import create_engine, Column, Integer, String, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi.responses import PlainTextResponse

# Получаем данные для подключения к БД из переменных окружения
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "mydb")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# Настройка SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Определяем модель для таблицы
class Visit(Base):
    __tablename__ = "visits"
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String, index=True)

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "ok"}

@app.get("/ping")
def ping(request: Request):
    db = SessionLocal()
    ip_address = request.client.host
    new_visit = Visit(ip_address=ip_address)
    db.add(new_visit)
    db.commit()
    db.close()
    return PlainTextResponse(content="pong")

@app.get("/visits")
def get_visits():
    db = SessionLocal()
    count = db.query(Visit).count()
    db.close()
    return count