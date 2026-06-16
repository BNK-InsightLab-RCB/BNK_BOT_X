"""Qwen(Ollama OpenAI 호환) 답변 어댑터 (새 코드).

BNK_Bot의 *결정*만 계승: reasoning_effort="none"(안 끄면 답변당 ~5천 추론 토큰,
90~230초), 타임아웃. P4에서 *승인된 매뉴얼을 근거 안에서 다듬는* 데만 쓴다 — 저작 금지.
"""
from __future__ import annotations


class GeneratorError(RuntimeError):
    pass


class Generator:
    def __init__(self, base_url: str, api_key: str, model: str, timeout_s: float = 120.0):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.timeout_s = timeout_s
        self._client = None

    def _ensure(self):
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(
                base_url=self.base_url, api_key=self.api_key, timeout=self.timeout_s
            )
        return self._client

    def rephrase(self, system: str, user: str) -> str:
        try:
            client = self._ensure()
            resp = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.1,
                extra_body={"reasoning_effort": "none"},
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:  # noqa: BLE001
            raise GeneratorError(str(exc)) from exc
