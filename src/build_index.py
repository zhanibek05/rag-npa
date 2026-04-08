"""
build_index.py — чанкует raw_text из Postgres, эмбеддит и загружает в Qdrant.
Обрабатывает документы со статусом 'scraped', по завершении ставит 'indexed'.

Запуск:
    python -m src.build_index
    python -m src.build_index --batch-size 64 --max-chars 1200
"""

import argparse
import re
from typing import Iterator

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

try:
    from src.core.config import (
        DATABASE_URL, EMBEDDING_DEVICE, EMBEDDING_MODEL,
        QDRANT_COLLECTION, QDRANT_URL,
    )
    from src.core.models import Document
except ModuleNotFoundError:
    from core.config import (
        DATABASE_URL, EMBEDDING_DEVICE, EMBEDDING_MODEL,
        QDRANT_COLLECTION, QDRANT_URL,
    )
    from core.models import Document


# ── chunking ──────────────────────────────────────────────────────────────────

def _split_chunks(text: str, max_chars: int, overlap: int) -> list[dict]:
    paragraphs = [p for p in re.split(r"\n+", text) if p.strip()]
    chunks = []
    i = 0
    while i < len(paragraphs):
        buf, length = [], 0
        start = i
        while i < len(paragraphs):
            p = paragraphs[i]
            if buf and length + len(p) + 1 > max_chars:
                break
            buf.append(p)
            length += len(p) + 1
            i += 1
        chunks.append({
            "text": "\n".join(buf),
            "chunk_index": len(chunks),
            "paragraph_start": start,
            "paragraph_end": i - 1,
        })
        if overlap > 0:
            i = max(i - overlap, start + 1)
    return chunks


# ── point id generator ────────────────────────────────────────────────────────

def _make_point_id(doc_id: str, chunk_index: int) -> int:
    """Детерминированный числовой ID для Qdrant из строки doc_id + chunk_index."""
    raw = f"{doc_id}_{chunk_index}"
    return abs(hash(raw)) % (2 ** 53)


# ── streaming batch iterator ──────────────────────────────────────────────────

def iter_points(
    docs: list,
    max_chars: int,
    overlap: int,
    model: SentenceTransformer,
    embed_batch: int,
) -> Iterator[list[PointStruct]]:
    """
    Для каждого документа строит чанки, эмбеддит батчами и отдаёт PointStruct-ы.
    Никогда не держит все эмбеддинги в памяти одновременно.
    """
    buf_texts: list[str] = []
    buf_meta: list[dict] = []

    def flush() -> list[PointStruct]:
        if not buf_texts:
            return []
        vecs = model.encode(
            buf_texts,
            batch_size=embed_batch,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        points = [
            PointStruct(
                id=_make_point_id(m["doc_id"], m["chunk_index"]),
                vector=vecs[j].tolist(),
                payload=m,
            )
            for j, m in enumerate(buf_meta)
        ]
        buf_texts.clear()
        buf_meta.clear()
        return points

    for doc in docs:
        chunks = _split_chunks(doc.raw_text or "", max_chars, overlap)
        for ch in chunks:
            buf_texts.append(ch["text"])
            buf_meta.append({
                "doc_id": doc.id,
                "text": ch["text"],
                "title": doc.title,
                "doc_type": doc.doc_type,
                "status": doc.status,
                "adopted_date": doc.adopted_date.isoformat() if doc.adopted_date else None,
                "source_url": doc.url,
                "chunk_index": ch["chunk_index"],
                "paragraph_start": ch["paragraph_start"],
                "paragraph_end": ch["paragraph_end"],
            })
            if len(buf_texts) >= embed_batch:
                yield flush()

    remaining = flush()
    if remaining:
        yield remaining


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-chars", type=int, default=1200)
    parser.add_argument("--overlap-paragraphs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--qdrant-url", default=QDRANT_URL)
    parser.add_argument("--collection", default=QDRANT_COLLECTION)
    parser.add_argument("--model", default=EMBEDDING_MODEL)
    parser.add_argument("--device", default=EMBEDDING_DEVICE)
    parser.add_argument("--recreate", action="store_true",
                        help="Пересоздать коллекцию Qdrant с нуля")
    args = parser.parse_args()

    sync_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)

    with Session() as db:
        docs = db.scalars(
            select(Document).where(Document.index_status == "scraped")
        ).all()

    if not docs:
        print("Нет документов со статусом 'scraped'. Запусти scrape_docs.py сначала.")
        return

    print(f"Документов для индексации: {len(docs)}")
    print(f"Загружаю модель '{args.model}' на {args.device}...")
    model = SentenceTransformer(args.model, device=args.device)

    qdrant = QdrantClient(url=args.qdrant_url)

    if args.recreate and qdrant.collection_exists(args.collection):
        qdrant.delete_collection(args.collection)

    if not qdrant.collection_exists(args.collection):
        # определяем размерность через тестовый эмбеддинг
        dim = model.encode(["test"], normalize_embeddings=True).shape[1]
        qdrant.create_collection(
            collection_name=args.collection,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        print(f"Создана коллекция '{args.collection}' (dim={dim})")

    total_points = 0
    for batch_points in iter_points(
        docs, args.max_chars, args.overlap_paragraphs, model, args.batch_size
    ):
        qdrant.upsert(collection_name=args.collection, points=batch_points)
        total_points += len(batch_points)
        print(f"  Загружено чанков: {total_points}", end="\r")

    # помечаем как indexed
    indexed_ids = [d.id for d in docs]
    with Session() as db:
        for doc_id in indexed_ids:
            d = db.get(Document, doc_id)
            if d:
                d.index_status = "indexed"
        db.commit()

    print(f"\nГотово. Чанков в Qdrant: {total_points}, документов помечено 'indexed': {len(docs)}")


if __name__ == "__main__":
    main()
