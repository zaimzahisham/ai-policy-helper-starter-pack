"""Embedding providers."""
import hashlib
from typing import List
import numpy as np


def _tokenize(s: str) -> List[str]:
    """Simple tokenizer: split on whitespace and lowercase."""
    return [t.lower() for t in s.split()]


class LocalEmbedder:
    """
    Deterministic local embedder using hash-based pseudo-random vectors.
    
    Uses SHA-1 hash of text to seed a PRNG, generating a fixed-size vector.
    Useful for offline testing and deterministic behavior.
    """
    
    def __init__(self, dim: int = 384):
        self.dim = dim

    def embed(self, text: str) -> np.ndarray:
        """
        Generate deterministic embedding vector from text.
        
        Args:
            text: Input text to embed
        
        Returns:
            L2-normalized float32 vector of shape (dim,)
        """
        # Hash-based repeatable pseudo-embedding
        h = hashlib.sha1(text.encode("utf-8")).digest()
        rng_seed = int.from_bytes(h[:8], "big") % (2**32-1)
        rng = np.random.default_rng(rng_seed)
        v = rng.standard_normal(self.dim).astype("float32")
        # L2 normalize
        v = v / (np.linalg.norm(v) + 1e-9)
        return v

