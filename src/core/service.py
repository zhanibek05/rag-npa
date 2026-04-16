from typing import Dict, Generator, List, Tuple

from .config import LLM_MODEL, LLM_PROVIDER
from .context import build_context
from .llm import generate_text, stream_text
from .retrieval import RetrievalEngine


def build_prompt(query: str, context: str) -> str:
    return (
        "Ты ассистент по нормативно-правовым актам Казахстана в сфере образования.\n"
        "Правила ответа:\n"
        "1. Отвечай ТОЛЬКО на основе приведённых источников — не выдумывай факты.\n"
        "2. Если в источниках есть конкретные числа, суммы, даты или нормы — обязательно укажи их явно.\n"
        "3. Если в источниках встречается таблица или список с несколькими значениями — перечисли все релевантные строки.\n"
        "4. Не говори «информации недостаточно», если нужные данные есть в источниках — просто извлеки их.\n"
        "5. Если информации действительно нет ни в одном источнике — скажи об этом.\n"
        "6. Ответ должен быть структурированным и конкретным.\n\n"
        f"Вопрос: {query}\n\n"
        f"Источники:\n{context}\n\n"
        "Ответ:"
    )


def build_suggestions_prompt(query: str, answer: str) -> str:
    return (
        "На основе вопроса и ответа предложи ровно 3 коротких уточняющих вопроса, "
        "которые пользователь мог бы задать дальше по теме НПА в сфере образования.\n"
        "Выведи ТОЛЬКО 3 вопроса — каждый с новой строки, без нумерации и лишних символов.\n\n"
        f"Вопрос: {query}\n"
        f"Ответ: {answer[:800]}\n\n"
        "Три следующих вопроса:"
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

    def suggest(self, query: str, answer: str) -> List[str]:
        prompt = build_suggestions_prompt(query=query, answer=answer)
        raw = generate_text(model=self.llm_model, provider=self.llm_provider, prompt=prompt, temperature=0.7)
        lines = [
            line.strip().lstrip("-•*1234567890.). ")
            for line in raw.strip().splitlines()
            if line.strip()
        ]
        return lines[:3]

    def answer_stream(self, query: str, top_k: int, max_context_chars: int) -> Generator[dict, None, None]:
        hits, scores = self.search_with_scores(query=query, top_k=top_k)
        context = build_context(hits, max_chars=max_context_chars)
        prompt = build_prompt(query=query, context=context)

        yield {"type": "sources", "hits": hits, "scores": scores}

        full_answer = []
        for token in stream_text(model=self.llm_model, provider=self.llm_provider, prompt=prompt):
            full_answer.append(token)
            yield {"type": "token", "text": token}

        answer_text = "".join(full_answer)

        try:
            suggestions = self.suggest(query=query, answer=answer_text)
        except Exception:
            suggestions = []
        yield {"type": "suggestions", "suggestions": suggestions}
        yield {"type": "done"}
