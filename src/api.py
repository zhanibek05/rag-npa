import json
import os
from typing import List, Optional

import faiss
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

app = FastAPI(title="RAG NPA API")

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальные переменные для моделей
INDEX_PATH = "./data/faiss.index"
META_PATH = "./data/chunks_meta.jsonl"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OLLAMA_MODEL = "llama3.1:8b"

index = None
meta = None
emb_model = None


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class AnswerRequest(BaseModel):
    query: str
    top_k: int = 10
    max_context_chars: int = 7000


class SearchResult(BaseModel):
    id: str
    text: str
    score: float
    source_url: Optional[str]
    title: Optional[str]


class AnswerResponse(BaseModel):
    answer: str
    sources: List[SearchResult]


@app.on_event("startup")
async def load_models():
    global index, meta, emb_model
    
    if not os.path.exists(INDEX_PATH):
        raise RuntimeError("Index not found. Run build_index.py first.")
    
    # Загрузка индекса
    index = faiss.read_index(INDEX_PATH)
    
    # Загрузка метаданных
    meta = []
    with open(META_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                meta.append(json.loads(line))
    
    # Загрузка модели эмбеддингов
    emb_model = SentenceTransformer(EMBEDDING_MODEL, device="cpu")
    
    print(f"✓ Loaded index with {len(meta)} chunks")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "index_loaded": index is not None,
        "chunks_count": len(meta) if meta else 0
    }


@app.post("/search", response_model=List[SearchResult])
async def search(req: SearchRequest):
    """Семантический поиск по индексу"""
    if not index or not meta or not emb_model:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    # Векторизация запроса
    q_emb = emb_model.encode([req.query], normalize_embeddings=True, convert_to_numpy=True)
    
    # Поиск
    scores, ids = index.search(q_emb, req.top_k)
    
    results = []
    for idx, score in zip(ids[0], scores[0]):
        if idx < 0 or idx >= len(meta):
            continue
        
        item = meta[idx]
        results.append(SearchResult(
            id=item["id"],
            text=item["text"],
            score=float(score),
            source_url=item.get("source_url"),
            title=item.get("title")
        ))
    
    return results


@app.post("/answer", response_model=AnswerResponse)
async def answer(req: AnswerRequest):
    """Генерация ответа через RAG + Ollama"""
    if not index or not meta or not emb_model:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    # Поиск релевантных чанков
    q_emb = emb_model.encode([req.query], normalize_embeddings=True, convert_to_numpy=True)
    scores, ids = index.search(q_emb, req.top_k)
    
    hits = []
    sources = []
    for idx, score in zip(ids[0], scores[0]):
        if idx < 0 or idx >= len(meta):
            continue
        
        item = meta[idx]
        hits.append(item)
        sources.append(SearchResult(
            id=item["id"],
            text=item["text"],
            score=float(score),
            source_url=item.get("source_url"),
            title=item.get("title")
        ))
    
    # Построение контекста
    context = build_context(hits, max_chars=req.max_context_chars)
    
    # Генерация ответа через Ollama
    prompt = (
        "Ты ассистент по нормативно-правовым актам в сфере образования. "
        "Ответь кратко и по сути, опираясь ТОЛЬКО на приведенные источники. "
        "Если информации недостаточно — скажи об этом.\n\n"
        f"Вопрос: {req.query}\n\n"
        f"Источники:\n{context}\n\n"
        "Ответ:"
    )
    
    try:
        answer_text = ollama_generate(OLLAMA_MODEL, prompt)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Ollama error: {str(e)}")
    
    return AnswerResponse(answer=answer_text, sources=sources)


def build_context(chunks: List[dict], max_chars: int = 3000) -> str:
    parts = []
    total = 0
    for i, c in enumerate(chunks, start=1):
        text = c["text"].strip()
        block = f"[Источник {i}]\n{text}"
        if total + len(block) > max_chars:
            break
        parts.append(block)
        total += len(block)
    return "\n\n".join(parts)


def ollama_generate(model: str, prompt: str, temperature: float = 0.2) -> str:
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }
    resp = requests.post(url, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data.get("response", "").strip()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
