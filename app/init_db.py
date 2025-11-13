from db import Base, engine


def init() -> None:
    """
    Initialize the database by creating all tables.
    """
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init()
    print("DB initialized")
