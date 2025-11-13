import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker


# Configure the database connection and ORM base
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/mydatabase")
# Create the SQLAlchemy engine and session factory
engine = create_engine(DATABASE_URL)
# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Define the base class for ORM models
Base = declarative_base()


class Visit(Base):
    """
    SQLAlchemy model for storing visit information.

    Attributes:
        id (int): Primary key for the visit record.
        client_ip (str): IP address of the client making the visit.
    """

    __tablename__ = "visits"
    id = Column(Integer, primary_key=True, index=True)
    client_ip = Column(String)
