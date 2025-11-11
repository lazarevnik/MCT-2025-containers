from enum import Enum

from pydantic_settings import BaseSettings


class Modes(str, Enum):
    DEV = "dev"
    PROD = "prod"


class Settings(BaseSettings, use_enum_values=True):
    APP_PORT: str
    APP_MODE: Modes

    DATABASE_DRIVER: str
    DATABASE_HOST: str
    DATABASE_PORT: int
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_NAME: str

    @property
    def database_url(self) -> str:
        return f"{self.DATABASE_DRIVER}://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

settings = Settings()
