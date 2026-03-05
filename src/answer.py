import argparse

try:
    from src.core.config import EMBEDDING_MODEL, INDEX_PATH, LLM_MODEL, LLM_PROVIDER, META_PATH
    from src.core.retrieval import RetrievalEngine
    from src.core.service import RAGService
except ModuleNotFoundError as exc:
    if not exc.name.startswith("src"):
        raise
    from core.config import EMBEDDING_MODEL, INDEX_PATH, LLM_MODEL, LLM_PROVIDER, META_PATH
    from core.retrieval import RetrievalEngine
    from core.service import RAGService


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--index", default=INDEX_PATH)
    parser.add_argument("--meta", default=META_PATH)
    parser.add_argument("--model", default=EMBEDDING_MODEL)
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="Device for embedding model")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--llm-model", default=LLM_MODEL)
    parser.add_argument("--llm-provider", default=LLM_PROVIDER, choices=["ollama", "openai"])
    parser.add_argument("--max-context-chars", type=int, default=3000)
    args = parser.parse_args()

    retrieval = RetrievalEngine(
        index_path=args.index,
        meta_path=args.meta,
        embedding_model=args.model,
        device=args.device,
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
