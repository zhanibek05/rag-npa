import argparse

try:
    from src.core.config import EMBEDDING_MODEL, INDEX_PATH, META_PATH
    from src.core.retrieval import RetrievalEngine
except ModuleNotFoundError as exc:
    if not exc.name.startswith("src"):
        raise
    from core.config import EMBEDDING_MODEL, INDEX_PATH, META_PATH
    from core.retrieval import RetrievalEngine


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--index", default=INDEX_PATH)
    parser.add_argument("--meta", default=META_PATH)
    parser.add_argument("--model", default=EMBEDDING_MODEL)
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    retrieval = RetrievalEngine(
        index_path=args.index,
        meta_path=args.meta,
        embedding_model=args.model,
        device=args.device,
    )
    retrieval.load()
    hits, scores = retrieval.search_with_scores(query=args.query, top_k=args.top_k)

    print("\n=== Top results ===\n")
    for rank, (item, score) in enumerate(zip(hits, scores), start=1):
        text = item["text"].replace("\n", " ")
        if len(text) > 500:
            text = text[:500] + "..."
        print(f"{rank}. score={score:.3f} id={item['id']}")
        print(text)
        print("-")


if __name__ == "__main__":
    main()
