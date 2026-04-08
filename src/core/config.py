import os
import platform

from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*args, **kwargs):
        return False

load_dotenv()

INDEX_PATH = os.getenv("INDEX_PATH", "./data/faiss.index")
META_PATH = os.getenv("META_PATH", "./data/chunks_meta.jsonl")
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "gpu")
RETRIEVAL_MODE = os.getenv(
    "RETRIEVAL_MODE",
    "lexical" if platform.system() == "Darwin" else "semantic",
).strip().lower()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", os.getenv("OPENAI_KEY", ""))
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
LLM_MODEL = os.getenv(
    "LLM_MODEL",
    OPENAI_MODEL if LLM_PROVIDER == "openai" else OLLAMA_MODEL,
)

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# SMTP
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# JWT Auth
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production-use-a-long-random-string")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

