import os
from typing import Dict, List, Tuple

import faiss
from sentence_transformers import SentenceTransformer

from .config import EMBEDDING_DEVICE, EMBEDDING_MODEL, INDEX_PATH, META_PATH
from .io import load_meta


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

        q_emb = self.model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        scores, ids = self.index.search(q_emb, top_k)

        hits: List[Dict] = []
        hit_scores: List[float] = []
        for idx, score in zip(ids[0], scores[0]):
            if idx < 0 or idx >= len(self.meta):
                continue
            item = self.meta[idx]
            hits.append(item)
            hit_scores.append(float(score))

        return hits, hit_scores
