from typing import Dict, List, Tuple

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

from .config import (
    EMBEDDING_DEVICE,
    EMBEDDING_MODEL,
    QDRANT_COLLECTION,
    QDRANT_URL,
)


class RetrievalEngine:
    def __init__(
        self,
        embedding_model: str = EMBEDDING_MODEL,
        device: str = EMBEDDING_DEVICE,
        qdrant_url: str = QDRANT_URL,
        collection_name: str = QDRANT_COLLECTION,
    ):
        self.embedding_model = embedding_model
        self.device = device
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name

        self.client: QdrantClient | None = None
        self.model = None

    def load(self) -> None:
        self.client = QdrantClient(url=self.qdrant_url)

        if not self.client.collection_exists(collection_name=self.collection_name):
            raise RuntimeError(
                f"Collection '{self.collection_name}' not found. Run build_index.py first."
            )

        print(f"Loading embedding model '{self.embedding_model}' on {self.device}...")
        self.model = SentenceTransformer(self.embedding_model, device=self.device)
        print(f"✓ Embedding model loaded")

    def is_ready(self) -> bool:
        return self.client is not None and self.model is not None

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

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=q_emb[0].tolist(),
            limit=top_k,
            with_payload=True,
        )

        hits = [point.payload for point in results.points]
        scores = [float(point.score) for point in results.points]
        return hits, scores
