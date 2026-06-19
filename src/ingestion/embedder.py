"""KURE-v1 임베딩 어댑터 (새 코드).

sentence-transformers를 lazy-load. 모델을 못 불러오면(예: P0 골격, 2GB 미다운로드)
결정론 해시 임베딩으로 폴백 → 골격/테스트가 모델 없이도 돈다. 인터페이스는 동일.
"""
from __future__ import annotations

import hashlib
import math
import re
from typing import Any


class Embedder:
    @staticmethod
    def bigrams(text: str) -> set[str]:
        """식별자/한글 질의를 같은 방식으로 접기 위한 char-bigram 토큰."""
        normalized = re.sub(r"[^0-9a-z가-힣]", "", (text or "").lower())
        return {normalized[i : i + 2] for i in range(len(normalized) - 1)}

    @staticmethod
    def get_sparse_vector(text: str) -> dict[str, Any] | None:
        """Qdrant sparse vector.

        값은 binary/count lexical matching에 가깝게 둔다. dense가 의미 검색을 맡고,
        sparse는 `TB_...`, `/api/...`, mapper id, error code 같은 식별자 recall을 보강한다.
        """
        tokens = Embedder.bigrams(text)
        if not tokens:
            return None
        weights: dict[int, float] = {}
        for token in tokens:
            idx = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % 1_000_003
            weights[idx] = weights.get(idx, 0.0) + 1.0
        indices = sorted(weights)
        values = [weights[idx] for idx in indices]
        return {"indices": indices, "values": values}

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
