from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://helsi_user:helsi_password@db:5432/medflow_database"

settings = Settings()