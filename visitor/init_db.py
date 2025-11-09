import os
from sqlalchemy import create_engine, Integer, String, Column
from sqlalchemy.orm import declarative_base

DB_USER = os.getenv("POSTGRES_USER", "user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "apppw")
DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "app")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

Base = declarative_base()


class Visit(Base):
    __tablename__ = "visits"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String(64))


def main():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    main()
