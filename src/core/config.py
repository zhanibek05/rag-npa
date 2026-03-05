import os

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

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", os.getenv("OPENAI_KEY", ""))
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
LLM_MODEL = os.getenv(
    "LLM_MODEL",
    OPENAI_MODEL if LLM_PROVIDER == "openai" else OLLAMA_MODEL,
)
