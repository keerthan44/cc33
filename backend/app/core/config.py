from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./notes.db"
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4.5-preview"
    WHISPER_MODEL_SIZE: str = "base"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"
    CORS_ORIGINS: list[str] = Field(default=["http://localhost:3000"])

    class Config:
        env_file = ".env"


settings = Settings()
