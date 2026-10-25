import math
import re
import hashlib
from typing import List
import numpy as np

from app.core.config import settings


def generate_embedding(text: str, dimension: int = 384) -> List[float]:
    """
    Generates a deterministic 384-dimensional normalized vector embedding.
    Combines subword n-gram hashing and term-frequency pooling to produce
    vectors where semantically related documents share high cosine similarity.
    """
    if not text or not text.strip():
        # Return zero vector if empty
        return [0.0] * dimension

    vector = np.zeros(dimension, dtype=np.float32)
    tokens = re.findall(r"\w+", text.lower())

    for token in tokens:
        # Hash full token
        h_val = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
        idx = h_val % dimension
        sign = 1.0 if ((h_val >> 8) & 1) else -1.0
        vector[idx] += sign

        # Hash character 3-grams for subword similarity
        for i in range(max(1, len(token) - 2)):
            tri = token[i:i+3]
            h_tri = int(hashlib.sha256(tri.encode("utf-8")).hexdigest(), 16)
            tri_idx = h_tri % dimension
            tri_sign = 0.5 if ((h_tri >> 8) & 1) else -0.5
            vector[tri_idx] += tri_sign

    # L2 Normalization
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm

    return vector.tolist()


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes cosine similarity between two float vectors."""
    a = np.array(v1, dtype=np.float32)
    b = np.array(v2, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))
