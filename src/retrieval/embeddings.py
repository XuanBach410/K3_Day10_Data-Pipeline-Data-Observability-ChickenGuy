from __future__ import annotations

from functools import lru_cache

from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer


import math
import numpy as np
from langchain_core.embeddings import Embeddings


import os
import math
import numpy as np
from langchain_core.embeddings import Embeddings


class FallbackEmbedder:
    """Offline deterministic 384-dim embedder using token hashing vectorization."""
    def __init__(self, dim: int = 384):
        self.dim = dim

    def _hash_embed(self, text: str) -> list[float]:
        vec = np.zeros(self.dim, dtype=np.float32)
        words = text.lower().split()
        if not words:
            return vec.tolist()
        for word in words:
            h = abs(hash(word)) % self.dim
            vec[h] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec.tolist()

    def encode(self, texts: list[str], normalize_embeddings: bool = True) -> np.ndarray:
        return np.array([self._hash_embed(t) for t in texts], dtype=np.float32)


def _load_model_safe(model_name: str):
    if os.getenv("USE_FALLBACK_EMBEDDINGS", "").lower() in {"1", "true", "yes"}:
        return FallbackEmbedder(dim=384)
    try:
        from sentence_transformers import SentenceTransformer
        # Set short timeout for local hub lookup
        os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
        return SentenceTransformer(model_name)
    except Exception as exc:
        print(f"Notice: Could not load SentenceTransformer '{model_name}' ({exc}). Using FallbackEmbedder.")
        return FallbackEmbedder(dim=384)



class MiniLMEmbeddings(Embeddings):
    def __init__(self, model_name: str):
        self.model = _load_model_safe(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        if hasattr(embeddings, "tolist"):
            return embeddings.tolist()
        return list(embeddings)

    def embed_query(self, text: str) -> list[float]:
        embeddings = self.model.encode([text], normalize_embeddings=True)
        if hasattr(embeddings, "tolist"):
            return embeddings.tolist()[0]
        return list(embeddings[0])

