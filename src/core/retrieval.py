import os
from typing import Dict, List, Tuple

import faiss
from sentence_transformers import SentenceTransformer

from .config import EMBEDDING_DEVICE, EMBEDDING_MODEL, INDEX_PATH, META_PATH
from .io import load_meta


import re

_DEF_DASH_RE = re.compile(r"[-–—]")
_WORD_RE = re.compile(r"[0-9a-zа-яё]+", re.I)

_STOPWORDS_RU = {
    "что","такое","это","ли","как","какой","какая","какие","каково",
    "кто","где","когда","почему","зачем","сколько",
    "я","мы","ты","вы","он","она","они",
    "в","на","по","о","об","про","для","от","до","из","к","с","со","у","за","при","без","над","под",
}

def _normalize_tokens(text: str) -> list[str]:
    toks = [t.lower() for t in _WORD_RE.findall(text)]
    # убираем стоп-слова, но оставляем числа (статьи/пункты)
    out = []
    for t in toks:
        if t.isdigit():
            out.append(t)
            continue
        if t in _STOPWORDS_RU:
            continue
        out.append(t)
    return out

def _lexical_boost(query: str, text: str) -> float:
    """
    Буст:
    - за наличие ключевого термина в тексте
    - за формат определения 'термин - ...'
    Работает для запросов вида 'стипендия?', 'что такое стипендия?' и т.п.
    """
    tokens = _normalize_tokens(query)
    if not tokens:
        return 0.0

    t = text.lower()
    boost = 0.0

    # "главный" токен: обычно последний содержательный ("что такое X" -> X)
    main = tokens[-1]

    # 1) точное слово main
    if re.search(rf"\b{re.escape(main)}\b", t):
        boost += 0.12

    # 2) определение через тире: "стипендия - ..."
    if re.search(rf"\b{re.escape(main)}\b\s*{_DEF_DASH_RE.pattern}\s*", t):
        boost += 0.35

    # 3) формат словаря: "53) стипендия - ..."
    if re.search(rf"^\s*\d+[-–]?\d*\)\s*\b{re.escape(main)}\b\s*{_DEF_DASH_RE.pattern}\s*", t):
        boost += 0.40

    # 4) небольшой бонус если встречаются и другие ключевые токены
    # (но аккуратно, чтобы не перетащить шум)
    extra = tokens[:-1]
    extra_hits = 0
    for tok in extra[:3]:  # ограничим
        if re.search(rf"\b{re.escape(tok)}\b", t):
            extra_hits += 1
    boost += 0.03 * extra_hits

    return boost

    

class RetrievalEngine:
    def __init__(
        self,
        index_path: str = INDEX_PATH,
        meta_path: str = META_PATH,
        embedding_model: str = EMBEDDING_MODEL,
        device: str = EMBEDDING_DEVICE,
    ):
        self.index_path = index_path
        self.meta_path = meta_path
        self.embedding_model = embedding_model
        self.device = device

        self.index = None
        self.meta: List[Dict] = []
        self.model = None

    def load(self) -> None:
        if not os.path.exists(self.index_path):
            raise RuntimeError("Index not found. Run build_index.py first.")
        if not os.path.exists(self.meta_path):
            raise RuntimeError("Meta not found. Rebuild index metadata first.")

        self.index = faiss.read_index(self.index_path)
        self.meta = load_meta(self.meta_path)
        self.model = SentenceTransformer(self.embedding_model, device=self.device)

    def is_ready(self) -> bool:
        return self.index is not None and self.model is not None and len(self.meta) > 0

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        hits, _ = self.search_with_scores(query=query, top_k=top_k)
        return hits

    def search_with_scores(self, query: str, top_k: int = 5) -> Tuple[List[Dict], List[float]]:
        if not self.is_ready():
            raise RuntimeError("Retrieval engine is not loaded")

        # Берем больше кандидатов из FAISS и потом переранжируем
        candidate_k = max(top_k * 10, 50)

        q_emb = self.model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        scores, ids = self.index.search(q_emb, candidate_k)

        rescored: List[Tuple[float, int]] = []
        for idx, score in zip(ids[0], scores[0]):
            if idx < 0 or idx >= len(self.meta):
                continue
            item = self.meta[idx]
            text = item.get("text", "")
            new_score = float(score) + _lexical_boost(query, text)
            rescored.append((new_score, int(idx)))

        rescored.sort(key=lambda x: x[0], reverse=True)
        rescored = rescored[:top_k]

        hits: List[Dict] = []
        hit_scores: List[float] = []
        for s, idx in rescored:
            hits.append(self.meta[idx])
            hit_scores.append(float(s))

        return hits, hit_scores