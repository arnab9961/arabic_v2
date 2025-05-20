from functools import lru_cache
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    MODEL_PATH: str = os.getenv("MODEL_PATH", "/app/models/llama-model.bin")
    QURAN_TEXT_PATH: str = os.getenv("QURAN_TEXT_PATH", "/app/data/quran_text.json")
    
    # Model settings
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "whisper-large-v3")
    LLAMA_MODEL: str = os.getenv("LLAMA_MODEL", "llama3-70b-8192")
    
    # API configuration
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "5000"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.1"))
    
    # Audio processing
    AUDIO_SAMPLE_RATE: int = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get settings instance (cached)"""
    return Settings()