from typing import Dict, List, Tuple

from .config import LLM_MODEL, LLM_PROVIDER
from .context import build_context
from .llm import generate_text
from .retrieval import RetrievalEngine


def build_prompt(query: str, context: str) -> str:
    return (
        "Ты ассистент по нормативно-правовым актам в сфере образования. "
        "Ответь кратко и по сути, опираясь ТОЛЬКО на приведенные источники. "
        "Если информации недостаточно — скажи об этом.\n\n"
        f"Вопрос: {query}\n\n"
        f"Источники:\n{context}\n\n"
        "Ответ:"
    )


class RAGService:
    def __init__(
        self,
        retrieval: RetrievalEngine,
        llm_model: str = LLM_MODEL,
        llm_provider: str = LLM_PROVIDER,
    ):
        self.retrieval = retrieval
        self.llm_model = llm_model
        self.llm_provider = llm_provider

    def search(self, query: str, top_k: int) -> List[Dict]:
        return self.retrieval.search(query=query, top_k=top_k)

    def search_with_scores(self, query: str, top_k: int) -> Tuple[List[Dict], List[float]]:
        return self.retrieval.search_with_scores(query=query, top_k=top_k)

    def answer(self, query: str, top_k: int, max_context_chars: int) -> Tuple[str, List[Dict], List[float]]:
        hits, scores = self.search_with_scores(query=query, top_k=top_k)
        context = build_context(hits, max_chars=max_context_chars)
        prompt = build_prompt(query=query, context=context)
        answer_text = generate_text(
            model=self.llm_model,
            provider=self.llm_provider,
            prompt=prompt,
        )
        return answer_text, hits, scores
