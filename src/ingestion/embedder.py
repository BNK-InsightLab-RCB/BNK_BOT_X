"""KURE-v1 임베딩 어댑터 (새 코드).

sentence-transformers를 lazy-load. 모델을 못 불러오면(예: P0 골격, 2GB 미다운로드)
결정론 해시 임베딩으로 폴백 → 골격/테스트가 모델 없이도 돈다. 인터페이스는 동일.
"""
from __future__ import annotations

import hashlib
import math


class Embedder:
    def __init__(self, model_name: str, dim: int = 1024):
        self.model_name = model_name
        self.dim = dim
        self._model = None
        self._tried = False

    def _load(self):
        if self._tried:
            return self._model
        self._tried = True
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        except Exception:
            self._model = None  # 폴백
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        model = self._load()
        if model is not None:
            try:
                vectors = model.encode(texts, normalize_embeddings=True)
                return [list(map(float, v)) for v in vectors]
            except Exception:
                pass
        return [self._hash(t) for t in texts]

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]

    def _hash(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for token in (text or "").lower().split() or ["∅"]:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for i, byte in enumerate(digest):
                vec[(byte + i * 31) % self.dim] += 1.0 if byte % 2 == 0 else -1.0
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]
