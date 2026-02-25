import argparse
import json
import os
from typing import List

import faiss
import requests
from sentence_transformers import SentenceTransformer


def load_meta(path: str):
    meta = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            meta.append(json.loads(line))
    return meta


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
        "options": {
            "temperature": temperature,
        },
    }
    resp = requests.post(url, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data.get("response", "").strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--index", default="./data/faiss.index")
    parser.add_argument("--meta", default="./data/chunks_meta.jsonl")
    parser.add_argument("--model", default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="Device for embedding model")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--ollama-model", default="llama3.1:8b")
    parser.add_argument("--max-context-chars", type=int, default=3000)
    args = parser.parse_args()

    if not os.path.exists(args.index):
        raise SystemExit("Index not found. Run build_index.py first.")

    meta = load_meta(args.meta)
    index = faiss.read_index(args.index)
    emb_model = SentenceTransformer(args.model, device=args.device)

    q_emb = emb_model.encode([args.query], normalize_embeddings=True, convert_to_numpy=True)
    scores, ids = index.search(q_emb, args.top_k)

    hits = []
    for idx in ids[0]:
        if idx < 0 or idx >= len(meta):
            continue
        hits.append(meta[idx])

    context = build_context(hits, max_chars=args.max_context_chars)

    prompt = (
        "Ты ассистент по нормативно-правовым актам в сфере образования. "
        "Ответь кратко и по сути, опираясь ТОЛЬКО на приведенные источники. "
        "Если информации недостаточно — скажи об этом.\n\n"
        f"Вопрос: {args.query}\n\n"
        f"Источники:\n{context}\n\n"
        "Ответ:"
    )

    answer = ollama_generate(args.ollama_model, prompt)
    print("\n=== Ответ ===\n")
    print(answer)


if __name__ == "__main__":
    main()
