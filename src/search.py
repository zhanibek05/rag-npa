import argparse
import json
import os
from typing import List

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


def load_meta(path: str):
    meta = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            meta.append(json.loads(line))
    return meta


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--index", default="./data/faiss.index")
    parser.add_argument("--meta", default="./data/chunks_meta.jsonl")
    parser.add_argument("--model", default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    if not os.path.exists(args.index):
        raise SystemExit("Index not found. Run build_index.py first.")

    meta = load_meta(args.meta)
    index = faiss.read_index(args.index)
    model = SentenceTransformer(args.model)

    q_emb = model.encode([args.query], normalize_embeddings=True, convert_to_numpy=True)
    scores, ids = index.search(q_emb, args.top_k)

    print("\n=== Top results ===\n")
    for rank, (idx, score) in enumerate(zip(ids[0], scores[0]), start=1):
        if idx < 0 or idx >= len(meta):
            continue
        item = meta[idx]
        text = item["text"].replace("\n", " ")
        if len(text) > 500:
            text = text[:500] + "..."
        print(f"{rank}. score={score:.3f} id={item['id']}")
        print(text)
        print("-")


if __name__ == "__main__":
    main()
