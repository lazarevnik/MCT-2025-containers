from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://user:password@db:5432/mydatabase"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Visit(Base):
    __tablename__ = "visits"
    id = Column(Integer, primary_key=True, index=True)
    client_ip = Column(String)


Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/ping")
def pong(db: Session = Depends(get_db)):
    new_visit = Visit(client_ip="127.0.0.1")
    db.add(new_visit)
    db.commit()
    return "pong"


@app.get("/visits")
def get_visits(db: Session = Depends(get_db)):
    count = db.query(Visit).count()
    return {"visits": count}
