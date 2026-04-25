from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/voicenotes"
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4.5-preview"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    WHISPER_MODEL_SIZE: str = "base"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"
    CORS_ORIGINS: list[str] = Field(default=["http://localhost:3000"])
    MAX_AUDIO_BYTES: int = 25 * 1024 * 1024  # 25 MB

    class Config:
        env_file = ".env"


settings = Settings()
