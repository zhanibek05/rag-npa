from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from src.core.config import (
        EMBEDDING_DEVICE,
        EMBEDDING_MODEL,
        LLM_MODEL,
        LLM_PROVIDER,
        QDRANT_COLLECTION,
        QDRANT_URL,
    )
    from src.core.database import engine
    from src.core.models import Base
    from src.core.retrieval import RetrievalEngine
    from src.core.service import RAGService
    from src.routers.auth import router as auth_router
    from src.routers.chat import router as chat_router
    from src.routers.admin import router as admin_router
    from src.routers.documents import router as documents_router
except ModuleNotFoundError as exc:
    if not exc.name.startswith("src"):
        raise
    from core.config import (
        EMBEDDING_DEVICE,
        EMBEDDING_MODEL,
        LLM_MODEL,
        LLM_PROVIDER,
        QDRANT_COLLECTION,
        QDRANT_URL,
    )
    from core.database import engine
    from core.models import Base
    from core.retrieval import RetrievalEngine
    from core.service import RAGService
    from routers.auth import router as auth_router
    from routers.chat import router as chat_router
    from routers.admin import router as admin_router
    from routers.documents import router as documents_router

app = FastAPI(title="RAG NPA API")

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(documents_router)

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
    suggestions: List[str] = []


@app.on_event("startup")
async def load_models():
    global retrieval_engine, rag_service

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Database tables ready")

    retrieval_engine = RetrievalEngine(
        embedding_model=EMBEDDING_MODEL,
        device=EMBEDDING_DEVICE,
        qdrant_url=QDRANT_URL,
        collection_name=QDRANT_COLLECTION,
    )
    retrieval_engine.load()
    rag_service = RAGService(
        retrieval=retrieval_engine,
        llm_model=LLM_MODEL,
        llm_provider=LLM_PROVIDER,
    )

    collection_info = retrieval_engine.client.get_collection(QDRANT_COLLECTION)
    print(f"✓ Loaded Qdrant collection '{QDRANT_COLLECTION}' with {collection_info.points_count} chunks")


@app.get("/health")
async def health():
    ready = retrieval_engine.is_ready() if retrieval_engine else False
    chunks_count = 0
    if ready:
        info = retrieval_engine.client.get_collection(retrieval_engine.collection_name)
        chunks_count = info.points_count
    return {
        "status": "ok",
        "index_loaded": ready,
        "chunks_count": chunks_count,
    }


def _ensure_ready() -> RAGService:
    if not rag_service or not retrieval_engine or not retrieval_engine.is_ready():
        raise HTTPException(status_code=503, detail="Models not loaded")
    return rag_service


def _to_search_result(item: dict, score: float) -> SearchResult:
    return SearchResult(
        id=item.get("doc_id") or item.get("id", ""),
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

    try:
        suggestions = service.suggest(query=req.query, answer=answer_text)
    except Exception:
        suggestions = []

    return AnswerResponse(answer=answer_text, sources=sources, suggestions=suggestions)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
