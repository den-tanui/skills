from __future__ import annotations
import logging
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)

_model = None


class Embedder:
    """Wrapper around sentence-transformers for generating embeddings."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", device: str = "cpu"):
        self.model_name = model_name
        self.device = device

    def _load_model(self):
        """Lazy-load the model (singleton)."""
        global _model
        if _model is None:
            try:
                from sentence_transformers import SentenceTransformer
                _model = SentenceTransformer(self.model_name, device=self.device)
                logger.info(f"Loaded model: {self.model_name} on {self.device}")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise
        return _model

    def embed(self, text: str) -> np.ndarray:
        """Embed a single text string."""
        model = self._load_model()
        vec = model.encode(text, normalize_embeddings=True)
        return vec.astype(np.float32)

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """Embed a batch of texts."""
        if not texts:
            return []
        model = self._load_model()
        vecs = model.encode(texts, batch_size=batch_size, normalize_embeddings=True)
        return [v.astype(np.float32) for v in vecs]

    @property
    def is_loaded(self) -> bool:
        return _model is not None


class MockEmbedder:
    """Mock embedder for testing — returns random unit vectors."""

    def embed(self, text: str) -> np.ndarray:
        vec = np.random.randn(384).astype(np.float32)
        return vec / np.linalg.norm(vec)

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        return [self.embed(t) for t in texts]

    @property
    def is_loaded(self) -> bool:
        return True
