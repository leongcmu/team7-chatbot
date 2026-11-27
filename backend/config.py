"""Runtime settings. Secrets are read from the environment, never committed."""
import os
from pathlib import Path
from functools import lru_cache
from dataclasses import dataclass

ROOT = Path(__file__).resolve().parent.parent

@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str
    allowed_origins: tuple[str, ...]
    max_agent_steps: int
    model_max_retries: int
    embedding_model: str
    embedding_min_score: float
    diagnostic_logging: bool

@lru_cache
def get_settings() -> Settings:
    # Local development: load .env when python-dotenv is installed. In hosting,
    # set the same values as environment variables / secret configuration.
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / '.env')
    except ImportError:
        pass
    return Settings(
        gemini_api_key=os.getenv('GEMINI_API_KEY', ''),
        gemini_model=os.getenv('GEMINI_MODEL', 'gemini-3.8-flash'),
        allowed_origins=tuple(x.strip() for x in os.getenv('ALLOWED_ORIGINS','http://localhost:5500,http://127.0.0.1:5500').split(',') if x.strip()),
        max_agent_steps=int(os.getenv('MAX_AGENT_STEPS','4')),
        model_max_retries=int(os.getenv('MODEL_MAX_RETRIES','2')),
        embedding_model=os.getenv(
            'EMBEDDING_MODEL','sentence-transformers/all-MiniLM-L6-v2',
        ),
        embedding_min_score=float(os.getenv('EMBEDDING_MIN_SCORE','0.27')),
        diagnostic_logging=os.getenv('DIAGNOSTIC_LOGGING','false').lower() in {'1','true','yes','on'},
    )
