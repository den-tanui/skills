import numpy as np
import pytest
from skill_manager.embedder import Embedder, MockEmbedder


def test_mock_embedder():
    embedder = MockEmbedder()
    vec = embedder.embed("test")
    assert vec.shape == (384,)
    assert np.abs(np.linalg.norm(vec) - 1.0) < 1e-5  # unit vector


def test_mock_embed_batch():
    embedder = MockEmbedder()
    vecs = embedder.embed_batch(["hello", "world"])
    assert len(vecs) == 2
    assert all(v.shape == (384,) for v in vecs)


@pytest.mark.acceptance
def test_real_embedder():
    """Test with real model — only runs when explicitly requested."""
    embedder = Embedder()
    vec = embedder.embed("form validation with zod")
    assert vec.shape == (384,)
    assert vec.dtype == np.float32
    assert abs(np.linalg.norm(vec) - 1.0) < 0.01
