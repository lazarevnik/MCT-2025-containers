from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    APP_PORT: str

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
