from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    database_url: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REDIS_URL: str
    TELEGRAM_TOKEN: str
    TELEGRAM_CHAT_ID: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()