import argparse

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer
from core.config import QDRANT_URL, QDRANT_COLLECTION, EMBEDDING_MODEL

try:
    from src.core.io import load_jsonl
except ModuleNotFoundError as exc:
    if not exc.name.startswith("src"):
        raise
    from core.io import load_jsonl


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunks", default="./data/act_chunks.jsonl")
    parser.add_argument("--model", default=EMBEDDING_MODEL)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--qdrant-url", default=QDRANT_URL)
    parser.add_argument("--collection", default=QDRANT_COLLECTION)
    args = parser.parse_args()

    chunks = load_jsonl(args.chunks)
    texts = [c["text"] for c in chunks]

    model = SentenceTransformer(args.model)
    embeddings = model.encode(
        texts,
        batch_size=args.batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    dim = embeddings.shape[1]
    client = QdrantClient(url=args.qdrant_url)

    if client.collection_exists(collection_name=args.collection):
        client.delete_collection(collection_name=args.collection)
    client.create_collection(
        collection_name=args.collection,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )

    batch_size = args.batch_size
    for start in range(0, len(chunks), batch_size):
        batch_chunks = chunks[start : start + batch_size]
        batch_embeddings = embeddings[start : start + batch_size]
        points = [
            PointStruct(
                id=start + i,
                vector=batch_embeddings[i].tolist(),
                payload={
                    "id": batch_chunks[i]["id"],
                    "text": batch_chunks[i]["text"],
                    "source_url": batch_chunks[i].get("source_url"),
                    "title": batch_chunks[i].get("title"),
                    "chunk_index": batch_chunks[i].get("chunk_index"),
                    "char_start": batch_chunks[i].get("char_start"),
                    "char_end": batch_chunks[i].get("char_end"),
                    "paragraph_start": batch_chunks[i].get("paragraph_start"),
                    "paragraph_end": batch_chunks[i].get("paragraph_end"),
                },
            )
            for i, _ in enumerate(batch_chunks)
        ]
        client.upsert(collection_name=args.collection, points=points)

    print(f"Saved {len(chunks)} chunks to Qdrant collection '{args.collection}' (dim={dim}).")


if __name__ == "__main__":
    main()
