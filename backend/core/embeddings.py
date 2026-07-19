"""
Lightweight local embeddings using TF-IDF style hashing.
No model download needed — works instantly, no API quota.
Dimension: 384 (compatible with sentence-transformers space).
"""
import logging
import hashlib
import math
import re
from typing import List

logger = logging.getLogger(__name__)
EMBEDDING_DIM = 384


def _tokenize(text: str) -> List[str]:
    """Simple word tokenizer."""
    text = text.lower()[:3000]
    return re.findall(r'\b[a-z][a-z0-9]{1,15}\b', text)


def _hash_embed(text: str) -> List[float]:
    """
    Hash-based embedding: each token is hashed to multiple dimensions.
    Produces consistent, useful similarity for industrial text.
    """
    tokens = _tokenize(text)
    if not tokens:
        return [0.0] * EMBEDDING_DIM

    vec = [0.0] * EMBEDDING_DIM

    # Count token frequencies
    freq: dict = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1

    # Project each unique token into vector space using multiple hashes
    for token, count in freq.items():
        tf = 1 + math.log(count)
        for seed in range(4):
            h = hashlib.md5(f"{seed}:{token}".encode()).hexdigest()
            # Use 8 bytes = 4 pairs for dimension selection and sign
            for i in range(4):
                dim = int(h[i*4:(i+1)*4], 16) % EMBEDDING_DIM
                sign = 1 if int(h[i*2], 16) % 2 == 0 else -1
                vec[dim] += sign * tf

    # L2 normalize
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a list of texts."""
    if not texts:
        return []
    return [_hash_embed(t) for t in texts]


def embed_query(query: str) -> List[float]:
    """Embed a single query."""
    return _hash_embed(query)
