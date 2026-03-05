from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from src.core.config import (
        EMBEDDING_DEVICE,
        EMBEDDING_MODEL,
        INDEX_PATH,
        LLM_MODEL,
        LLM_PROVIDER,
        META_PATH,
    )
    from src.core.retrieval import RetrievalEngine
    from src.core.service import RAGService
except ModuleNotFoundError as exc:
    if not exc.name.startswith("src"):
        raise
    from core.config import (
        EMBEDDING_DEVICE,
        EMBEDDING_MODEL,
        INDEX_PATH,
        LLM_MODEL,
        LLM_PROVIDER,
        META_PATH,
    )
    from core.retrieval import RetrievalEngine
    from core.service import RAGService

app = FastAPI(title="RAG NPA API")

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

retrieval_engine: Optional[RetrievalEngine] = None
rag_service: Optional[RAGService] = None


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
    global retrieval_engine, rag_service

    retrieval_engine = RetrievalEngine(
        index_path=INDEX_PATH,
        meta_path=META_PATH,
        embedding_model=EMBEDDING_MODEL,
        device=EMBEDDING_DEVICE,
    )
    retrieval_engine.load()
    rag_service = RAGService(
        retrieval=retrieval_engine,
        llm_model=LLM_MODEL,
        llm_provider=LLM_PROVIDER,
    )

    print(f"✓ Loaded index with {len(retrieval_engine.meta)} chunks")


@app.get("/health")
async def health():
    chunks_count = len(retrieval_engine.meta) if retrieval_engine else 0
    return {
        "status": "ok",
        "index_loaded": retrieval_engine.is_ready() if retrieval_engine else False,
        "chunks_count": chunks_count,
    }


def _ensure_ready() -> RAGService:
    if not rag_service or not retrieval_engine or not retrieval_engine.is_ready():
        raise HTTPException(status_code=503, detail="Models not loaded")
    return rag_service


def _to_search_result(item: dict, score: float) -> SearchResult:
    return SearchResult(
        id=item["id"],
        text=item["text"],
        score=float(score),
        source_url=item.get("source_url"),
        title=item.get("title"),
    )


@app.post("/search", response_model=List[SearchResult])
async def search(req: SearchRequest):
    """Семантический поиск по индексу"""
    service = _ensure_ready()
    hits, scores = service.search_with_scores(query=req.query, top_k=req.top_k)
    return [_to_search_result(item, score) for item, score in zip(hits, scores)]


@app.post("/answer", response_model=AnswerResponse)
async def answer(req: AnswerRequest):
    """Генерация ответа через RAG + LLM provider"""
    service = _ensure_ready()
    try:
        answer_text, hits, scores = service.answer(
            query=req.query,
            top_k=req.top_k,
            max_context_chars=req.max_context_chars,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"LLM error: {str(e)}")

    sources = [_to_search_result(item, score) for item, score in zip(hits, scores)]
    return AnswerResponse(answer=answer_text, sources=sources)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
