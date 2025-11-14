from sqlalchemy import create_engine
from db import Base

engine = create_engine("postgresql+psycopg://user:pass@db:5432/posdb", echo=True)
Base.metadata.create_all(engine)