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
    max_text_chars: int = 30000  # trim before sending to AI
    ai_backend: str = "gemini"  # "gemini" | "ollama" | "groq"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:0.5b"
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    groq_max_chars: int = 8000  # ~2000 tokens, within Groq free-tier payload limits
    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"


settings = Settings()
