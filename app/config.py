import os
from pathlib import Path
from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    gemini_api_key: str = ""
    secret_key: str = "change-this-to-a-random-secret"
    database_url: str = f"sqlite:///{BASE_DIR}/instance/research.db"
    upload_dir: str = str(BASE_DIR / "data" / "uploads")
    extracted_dir: str = str(BASE_DIR / "data" / "extracted")
    summaries_dir: str = str(BASE_DIR / "data" / "summaries")
    gemini_model: str = "gemini-1.5-flash"
    max_text_chars: int = 30000  # trim before sending to Gemini

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"


settings = Settings()
