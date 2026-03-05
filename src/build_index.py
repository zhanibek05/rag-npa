import argparse
import json
import os

import faiss
from sentence_transformers import SentenceTransformer

try:
    from src.core.io import load_jsonl
except ModuleNotFoundError as exc:
    if not exc.name.startswith("src"):
        raise
    from core.io import load_jsonl


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunks", default="./data/act_chunks.jsonl")
    parser.add_argument("--out-dir", default="./data")
    parser.add_argument("--model", default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    parser.add_argument("--batch-size", type=int, default=32)
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
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    os.makedirs(args.out_dir, exist_ok=True)
    faiss.write_index(index, os.path.join(args.out_dir, "faiss.index"))

    # Save metadata aligned with embeddings
    meta_path = os.path.join(args.out_dir, "chunks_meta.jsonl")
    with open(meta_path, "w", encoding="utf-8") as f:
        for c in chunks:
            item = {
                "id": c["id"],
                "text": c["text"],
                "source_url": c.get("source_url"),
                "title": c.get("title"),
                "chunk_index": c.get("chunk_index"),
                "char_start": c.get("char_start"),
                "char_end": c.get("char_end"),
                "paragraph_start": c.get("paragraph_start"),
                "paragraph_end": c.get("paragraph_end"),
            }
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Saved index with {len(chunks)} chunks (dim={dim}).")


if __name__ == "__main__":
    main()
