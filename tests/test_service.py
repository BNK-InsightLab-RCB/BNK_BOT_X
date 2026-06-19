"""ChatService 답변 생성 — 부실한 LLM 출력은 승인 매뉴얼 기반으로 폴백한다."""

from src.chat.service import ChatService, _is_bad_generated_answer


BODY = """# 경비집행내역 등록 — 처리가 안 될 때

경비집행내역 등록 화면에서 처리가 안 되는 경우 아래를 확인해 주세요.

## 가능한 원인과 확인 사항
1. 경비 저장 권한이 없습니다 — 저장 권한이 없으면 처리할 수 없다.
2. 이미 마감된 경비는 수정할 수 없습니다 — 마감된 경비는 수정할 수 없다.
3. 집행금액을 정확히 입력해 주세요 — 집행금액은 0보다 커야 한다.

## 그래도 안 되면
위 사항을 확인한 뒤에도 같은 오류가 계속되면, 화면명(경비집행내역 등록)·수행 작업·오류 문구를 정리해 IT 담당자에게 전달해 주세요.
"""


class _Retriever:
    def retrieve(self, question: str, role: str = "branch", top_k: int = 5) -> list[dict]:
        return [
            {
                "payload": {
                    "manual_id": "manual_expense_register_save",
                    "screen_ko": "경비집행내역 등록",
                    "action": "save",
                    "body": BODY,
                },
                "score": 1.0,
                "dense": 0.6,
                "lexical": 0.5,
            }
        ]


class _Gate:
    def passes(self, hits: list[dict]) -> bool:
        return True


class _Generator:
    def __init__(self, answer: str):
        self.answer = answer

    def rephrase(self, system: str, user: str) -> str:
        return self.answer


def test_bad_generated_answer_falls_back_to_branch_manual():
    svc = ChatService(
        _Retriever(),
        _Gate(),
        _Generator("제공된 매뉴얼에는 관련된 구체적인 내용이 포함되어 있지 않습니다."),
    )

    resp = svc.answer("경비집행내역 저장이 안돼요")

    assert resp.handoff is False
    assert "제공된 매뉴얼에는" not in resp.answer
    assert "경비 저장 권한" in resp.answer
    assert "이미 마감된 경비" in resp.answer
    assert "집행금액" in resp.answer
    assert "# 경비집행내역" not in resp.answer


def test_good_generated_answer_is_kept():
    answer = "경비 저장 권한, 마감 여부, 집행금액을 순서대로 확인해 주세요."
    svc = ChatService(_Retriever(), _Gate(), _Generator(answer))

    resp = svc.answer("경비집행내역 저장이 안돼요")

    assert resp.answer == answer


def test_placeholder_generated_answer_is_bad():
    assert _is_bad_generated_answer("## (관리자 수정) 가능한 원인\n- ...")
