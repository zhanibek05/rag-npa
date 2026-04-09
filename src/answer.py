import argparse

try:
    from src.core.config import EMBEDDING_DEVICE, EMBEDDING_MODEL, LLM_MODEL, LLM_PROVIDER, QDRANT_COLLECTION, QDRANT_URL
    from src.core.retrieval import RetrievalEngine
    from src.core.service import RAGService
except ModuleNotFoundError as exc:
    if not exc.name.startswith("src"):
        raise
    from core.config import EMBEDDING_DEVICE, EMBEDDING_MODEL, LLM_MODEL, LLM_PROVIDER, QDRANT_COLLECTION, QDRANT_URL
    from core.retrieval import RetrievalEngine
    from core.service import RAGService


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--model", default=EMBEDDING_MODEL)
    parser.add_argument("--device", default=EMBEDDING_DEVICE, choices=["cpu", "cuda"])
    parser.add_argument("--qdrant-url", default=QDRANT_URL)
    parser.add_argument("--collection", default=QDRANT_COLLECTION)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--llm-model", default=LLM_MODEL)
    parser.add_argument("--llm-provider", default=LLM_PROVIDER, choices=["ollama", "openai"])
    parser.add_argument("--max-context-chars", type=int, default=3000)
    args = parser.parse_args()

    retrieval = RetrievalEngine(
        embedding_model=args.model,
        device=args.device,
        qdrant_url=args.qdrant_url,
        collection_name=args.collection,
    )
    retrieval.load()
    service = RAGService(
        retrieval=retrieval,
        llm_model=args.llm_model,
        llm_provider=args.llm_provider,
    )
    answer, _, _ = service.answer(
        query=args.query,
        top_k=args.top_k,
        max_context_chars=args.max_context_chars,
    )
    print("\n=== Ответ ===\n")
    print(answer)


if __name__ == "__main__":
    main()
