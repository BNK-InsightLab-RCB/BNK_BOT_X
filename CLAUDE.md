# BNK_BOT_X — Source-Aware Ops Support Engine

은행 업무 담당자가 **사내 프로그램을 쓰다 막힐 때**(오류·업무흐름·화면 표기 의미·다음 단계·화면 간 데이터 차이) 지금은 개발자에게 전화로 묻는 질문을, **챗봇이 1차로 받아 답하고 못 푸는 것만 개발자에게 넘기는** 엔진.
근거는 새로 저작하지 않고 **이미 있는 자산(소스코드·SQL·스키마·표준용어)을 변환**해서 만든다.

> **Status: P4 완료** — P0~P3 ✅ · P4 검색+정밀도 게이트 ✅(측정③). KURE 설치됨. 다음 = **P5 측정 게이트(슬라이스 종료 판정)**.
> 코드: `src/`(엔진 전체) · `examples/bank_sample/`(seed: 경비 save/approve · 예산 save · 동적 SQL) · `scripts/`(eval_extract·build_manuals·load_manuals·eval_query) · `tests/`(8) · `data/manuals/` · `.venv/`.
> 실행: `docker compose up -d`(Qdrant 6335) → `uvicorn src.main:app --port 9000`.
> 빌드·적재·질의: `build_manuals.py` → `load_manuals.py` → `eval_query.py`. 측정: `eval_extract.py` · `pytest`.
> 형제 프로젝트: `../BNK_Bot`(원본, 약관/설명서 PDF RAG — 참고 대상) · `../BNK_Bot_S`(소스-aware 프로토타입 — 참고 대상).

---

## 📌 프로젝트 목표

- **대상 사용자:** 영업점/업무 담당자 (고객이 아님 — 이게 `BNK_Bot`과 다른 점).
- **하는 일:** 자연어 문의 → 관련 화면/업무 규칙/오류 조건/조치법을 **업무 언어로** 안내.
- **목표는 커버리지가 아니라 정밀도.** 확실히 답할 수 있는 것만 답하고, 모호하면 개발자에게 넘긴다.
- **성공 지표:** 개발자 전화 응대 감소. 1차 자동 응답이 정밀도를 지키면서 늘어나는 것.

---

## 💡 핵심 발상 — 저작이 아니라 변환

새 지식을 만드는 게 아니라 **기존 자산을 변환**한다. 그래서 자동화가 가능하다는 게 전제다.

입력 자산(전부 이미 존재):
- 소스코드 — Spring Boot 백엔드, Vue/React 프론트
- MyBatis로 직접 작성한 SQL
- MariaDB 테이블 구조 — **모든 테이블에 한글 설명 존재**(예: `경비집행내역`)
- 표준용어(한국어)

변환기는 이걸 파싱해 **화면→API→Service→Mapper 쿼리→WHERE 조건→테이블**로 이어지는
연결관계(lineage)와 표기 의미·오류 정보를 추출하고, 그 **사실을 근거로** 사람이 읽을 매뉴얼을 생성한다.
LLM은 무에서 짓는 게 아니라 추출된 사실을 요약하는 역할이라 환각이 억제된다.

---

## 🧭 설계 철학 — 두 시간 축

하나의 시스템을 두 시간 축으로 나눈다.

### ① 빌드 타임 — 변환기 (지식을 *한 번* 만들어 적재)

```
기존 자산  →  추출(Extractor): lineage · 표기의미 · 오류 — 사실만
          →  매뉴얼 생성(LLM): 추출된 사실 요약 · branch/it 두 버전
          →  사람 검토 · 동결: 개발자 승인  ← 감사 가능성의 핵심
          →  승인 매뉴얼 적재: 매뉴얼 저장소(Qdrant) + 임베딩 색인 / lineage(그래프 저장소)
```

### ② 질의 타임 — 소비 (`BNK_Bot` 질의 *방식* 참고, 코드는 새로)

```
담당자 질문  →  매뉴얼 검색(KURE+Qdrant, 매칭 점수)
            →  정밀도 게이트: 점수 충분?
                ├─ 충분 →  승인 매뉴얼을 질문에 맞게 다듬어 답 (branch/it)
                └─ 부족 →  개발자 핸드오프  →  넘긴 Q&A 축적  →  다음 빌드로 피드백
```

축적 루프가 "코드로 못 만드는 지식"의 빈틈을 시간이 지나며 메운다.

---

## ⚖️ 두 설계(A/B)와 불변식

이 프로젝트는 **A 설계**(변환·출판·정밀도)를 목적지로 한다. `BNK_Bot`의 질의 파이프라인(B)은
"매뉴얼을 만드는 저자"가 아니라 **"맞는 매뉴얼을 찾아주는 사서"** 역할로 참고한다(방식만, 코드는 새로).

| 축 | A (이 프로젝트) | B (`BNK_Bot` 현재) |
|---|---|---|
| 지식 생성 시점 | 빌드 타임 1회, 매뉴얼로 적재 | 질의 시점마다 합성 |
| 저장소 정체 | 검수된 매뉴얼 저장소 | 사실 인덱스 |
| LLM 위치 | 변환단(사실 요약) + 질의단(다듬기) | 응답단(맥락 요약) |
| 정확성 근원 | lineage + 검수된 매뉴얼 | 검색 랭킹 |
| 안전 원칙 | 정밀도·회피·핸드오프 | 역할 마스킹 |

### 시스템을 떠받치는 3개 불변식 (반드시 지킨다)

1. **생성은 빌드 타임, 검색은 질의 타임.** 질의 시점에 매뉴얼을 새로 합성하지 않는다 — 하면 검수·동결이 무너지고 B로 회귀한다.
2. **질의 타임 LLM은 "다듬기"만, "짓기"는 금지.** 검색된(이미 승인된) 매뉴얼 안에서 좁히고 바꿔 말할 수 있을 뿐, 새 사실을 만들 수 없다.
3. **확신 없으면 답하지 않는다.** 정밀도 게이트가 지키고, 못 답한 건 핸드오프 → 축적으로 흘려보낸다.

---

## 🔒 인식론적 경계 (의도적 빈 영역)

추출은 **코드에서 파생 가능한 사실만** 뽑는다(lineage·표기의미·오류).
절차·업무의도·시스템/팀 경계 핸드오프처럼 **코드에 없는 지식은 일부러 만들지 않는다.**
그 빈자리는 질의 타임의 핸드오프 축적 루프가 채운다. "내가 못 아는 것을 안다"가 구조에 박혀 있어야 한다.

---

## 🏗️ 아키텍처 — 재사용 vs 신규

도메인 분리(Spring/Nest 스타일)는 `BNK_Bot` 구조를 따른다: `ingestion` / `chat` / `main`.
**`ingestion`의 입력만 PDF→소스코드로 바꾸고, 척추(chunk→embed→qdrant)와 `chat` 도메인의 *형태*를 참고한다. 코드는 전부 새로 쓴다.**

| 구분 | 내용 | `BNK_Bot`에서 가져오는 것 |
|---|---|---|
| **결정·패턴만 참고 (코드는 새로)** | Qdrant 어댑터 · KURE 임베더 · Qwen generator · lifespan · `/health` · eval 하니스 | 설정·함정·구조만 (코드 복사 ❌) |
| **패턴 참고 + 크게 확장** | retriever(+하이브리드·필터) · service(+정밀도 게이트·핸드오프) | `chat` 도메인 형태 |
| **완전 신규 (이 프로젝트 정체)** | Extractor(소스→lineage) · 매뉴얼 생성·검수·동결 · 핸드오프 축적 루프 · lineage 그래프 저장소 | 없음 |

### `BNK_Bot`에서 *방식*을 가져오는 것 (이미 A의 질의 절반)

`BNK_Bot`의 `chat` 도메인은 A의 질의 타임 불변식을 이미 검증해 둠 — 코드를 베끼는 게 아니라 그 *방식*을 새로 구현한다:
- `service.py`의 **"모름" 경로**(검색 0건→LLM 없이 즉시 회피) = 정밀도 게이트/회피의 씨앗
- 가드레일: **근거강제 + 숫자보존** = "다듬기만, 짓기 금지" 불변식
- `eval_answer.py` / `eval_retrieval.py` = 측정 기반 회귀 루프

---

## 🔁 재사용 스탠스 (`BNK_Bot`을 어떻게 참고하나)

**코드는 전부 새로 쓴다. `BNK_Bot`에서 가져오는 건 *결정과 패턴*뿐 — 코드 복사 안 함.**
가장 큰 이득은 코드 줄이 아니라 *`BNK_Bot`이 이미 푼 문제를 다시 안 푸는 것*이다.

| 종류 | 방침 |
|---|---|
| **결정·교훈** (reasoning_effort=none, num_ctx=16384, NFC 정규화, 회피 보정, 결정론 우선) | ✅ 가져온다 (지식) |
| **패턴·아키텍처** (도메인 분리 ingestion/chat, lifespan 싱글톤, payload 파티셔닝, eval 회귀 루프) | ✅ 참고해 **새로 작성** |
| **인프라/모델 실행체** (Ollama Qwen 엔드포인트 · KURE 모델 · Qdrant 엔진) | ✅ *돌아가는 실행체*만 공유 (코드 아님) |
| **코드 복사 / 공유 라이브러리** | ❌ **안 한다** |

**두 규율:**
- **"인프라 공유"와 "코드 복사"는 다르다.** Qwen 엔드포인트·KURE 모델·Qdrant 엔진은 *돌아가는 실행체*를 쓰는 것(코드 무관). **모든 소스 파일은 이 repo에서 새로 쓴다.**
- **결론이 아니라 이유를 재사용한다.** 예: `BNK_Bot`의 "단일 컬렉션"은 *"같은 임베딩·격리 불필요"* 전제에서 나왔고, 우리는 그 전제를 안 만족 → 별도 컨테이너로 벗어남. 재사용 = 추론(언제 나누나) 계승.

**이 프로젝트의 코드는 전부 신규다** — 파서·Extractor·매뉴얼 생성·게이트·핸드오프·lineage 저장소뿐 아니라 retriever·generator·qdrant 어댑터까지. `BNK_Bot`의 "왜 이렇게 했나" 결정(특히 Qwen 함정·NFC·결정론 우선)만 참고한다.

---

## 🗄️ 저장소 설계 — 두 개로 나눈다

**소스코드 자체는 Qdrant에 넣지 않는다.** 들어가는 건 *생성된 한글 매뉴얼(산문)* 뿐.

- **Qdrant** ← 검수된 매뉴얼(산문). 의미 검색용. **새 별도 컨테이너·컬렉션**(아래 인프라 참조). KURE-v1(1024-dim) 임베딩.
- **그래프/관계형(SQLite 등)** ← lineage(화면→API→…→테이블)·스키마 연결. 구조 탐색용. **실제 검색 확장에 사용**(프로토타입 `BNK_Bot_S`는 그래프를 만들고 미사용이었음 — 그 함정을 피한다).

### 임베딩·검색 결정 (확정)

- **벡터DB는 Qdrant 그대로.** 다른 벡터DB로 바꿀 이유 없음. 소스베이스가 새로 요구하는 건 *다른 벡터DB*가 아니라 *별도 구조(그래프/관계형) 저장소*다.
- **임베딩은 KURE-v1 유지.** 매뉴얼 본문은 한글 산문이라 KURE가 최적. **코드 특화 임베딩은 한글 산문에 역효과**라 쓰지 않는다.
- **검색은 하이브리드.** 매뉴얼엔 식별자·코드값(`TB_…`, `/api/…`, 에러코드, 메서드명)이 박혀 있는데, **어떤 dense 임베딩도 정확 식별자 매칭은 못 한다.** 해법은 모델 교체가 아니라:
  - **dense(KURE) + sparse/BM25 + payload exact-match → RRF 융합.** Qdrant가 sparse 벡터·하이브리드를 네이티브 지원하므로 한 저장소에서 처리.
  - IT용 식별자(api_path/sql_id/table)는 payload 인덱스로 **정확 필터**.
- **전환은 측정으로 판단.** `BNK_Bot`의 `eval_retrieval` 패턴으로 **식별자 질의 recall**을 재고, dense+sparse로도 무너질 때만 Elasticsearch/pgvector 전환 검토(느낌이 아니라 측정).

---

## 📄 매뉴얼 형식 (데이터 계약)

매뉴얼 = **JSON 레코드 1개 + 본문(branch/it)만 Markdown.** P0의 `models.py`가 이 계약을 고정한다.
임베딩되는 건 MD 본문, 필터·lineage 링크는 JSON 필드. (`BNK_Bot`의 JSONL 청크 패턴과 동형.)

```json
{
  "id": "manual_expense_save",
  "screen_id": "EXPENSE_REGISTER",
  "screen_ko": "경비집행내역 등록",
  "action": "save",
  "api_path": "/api/expense/save",
  "table_en": ["TB_EXPENSE_EXEC"],
  "table_ko": ["경비집행내역"],
  "branch_md": "## 가능한 원인\n- 마감(상태 C)된 경비는 수정할 수 없습니다...\n## 먼저 확인할 사항\n1. ...",
  "it_md": "## 처리 흐름\n`/api/expense/save` → `ExpenseService.saveExpense` → `ExpenseMapper.insertExpense` → `TB_EXPENSE_EXEC`...",
  "facts": { "conditions": ["..."], "errors": ["..."], "auth": ["..."] },
  "lineage_ref": ["EXPENSE_REGISTER", "/api/expense/save", "ExpenseService.saveExpense", "ExpenseMapper.insertExpense", "TB_EXPENSE_EXEC"],
  "provenance": [{ "path": "backend/ExpenseService.java", "lines": "40-72", "commit": "..." }],
  "status": "draft|approved|frozen",
  "version": 1
}
```

- **`branch_md` / `it_md`** — 역할별 Markdown 산문. 임베딩·답변의 원천. 숫자·조건은 verbatim 보존.
- **구조 필드** — Qdrant payload(`screen_id`/`table_en`/`table_ko`/`action`/`role`) + lineage 그래프 링크(`lineage_ref`) + 근거(`provenance`).
- **Qdrant 적재:** role별 포인트 분리(role=branch는 `branch_md` 임베딩, role=it는 `it_md`) → 질의 시 역할 안에서 검색.
- **검수 산물(선택):** 동결 매뉴얼을 git용 `.md`(+YAML frontmatter)로도 직렬화 → 감사 추적. 빌드가 위 JSON으로 변환.

---

## 🧱 매뉴얼 생성 단위 (오퍼레이션 단위)

**매뉴얼 1개 = 오퍼레이션 1개 = 화면 × 액션 = 하나의 lineage 체인.** (화면 통째도, 오류 하나하나도 아님.)

- 한 화면엔 보통 여러 액션(저장/조회/승인)이 있고 **각 액션이 서로 다른 API→Service→Mapper→테이블 체인**을 탄다. Extractor가 뽑는 자연 단위(컨트롤러/서비스 메서드 1개) = 1 오퍼레이션 = 1 매뉴얼.
- **왜 화면 통째가 아닌가:** 저장/조회/승인이 한 매뉴얼에 뭉치면 체인·실패조건이 섞여 검색이 덜 정밀(정밀도 우선에 반함).
- **왜 오류 단위가 아닌가:** 너무 잘게 쪼개면 "이 화면 저장이 안돼요" 덩어리 질문에 조각을 다시 모아야 하고 검수도 파편화.

**오퍼레이션 안에 실패 모드를 목록으로.** 1 매뉴얼(예: 저장) 안 `facts`/`branch_md`에 가능한 원인 여러 개(권한 없음 / 마감 상태 `STATUS=C` / 필수값 누락 …)를 각각 `{조건·의미·조치·근거(source:line)}`로 담는다. → 질의시점 LLM은 이 목록에서 **질문에 맞는 원인만 골라 다듬는다**("다듬기만, 짓기 금지").

**화면 roll-up.** 모든 매뉴얼에 `screen_id` → "이 화면에서 뭔가 안돼요" 같은 모호한 질문엔 그 화면의 오퍼레이션 매뉴얼들을 모아 제시(lineage 그래프 + payload 필터).

**정밀도 필터 (인식론적 경계와 일치).** 실제 업무규칙(조건·오류·권한)이 추출되는 오퍼레이션만 매뉴얼이 된다. 단순 getter처럼 실패 로직이 없으면 매뉴얼을 안 만든다 → 근거 없는 건 핸드오프 영역.

**참조 매뉴얼 (보조·선택).** 화면/용어 설명(표기의미)은 대부분 오퍼레이션 매뉴얼 메타(`table_ko`)로 커버. 필요 시 가벼운 "참조 매뉴얼"(화면·용어 설명) 타입을 따로 둘 수 있다.

---

## 🐳 인프라 결정

- **[확정] Qdrant는 새 Docker 컨테이너로 띄워 진행한다 — 기존 `BNK_Bot` Qdrant와 공유하지 않는다.**
  - 이 프로젝트(`BNK_BOT_X`) 안에 **자기 `docker-compose.yml`** 작성. **포트 6335**(BNK_Bot=6333), 컨테이너명 예: `bnk-ops-qdrant`, 볼륨 `./data/qdrant_storage`.
  - 컬렉션명 예: **`bnk_ops_knowledge`**.
  - 이유는 "다른 프로젝트라서"가 아니라 **위험도 비대칭** — `BNK_Bot`은 고객대면 운영, 이 엔진은 개발 중(잦은 recreate/reset). stateful 저장소를 공유하면 개발 중 사고가 운영 데이터에 번진다.
  - `BNK_Bot/CLAUDE.md`의 "컬렉션 분리는 강한 격리가 필요할 때만" 규칙의 정상 적용 — 여기선 **컨테이너까지 분리**.
- **stateful만 가른다.** Qwen(Ollama)·KURE는 무상태 → 개발 단계엔 **공유**.
  데이터 blast radius가 없고, **단일 머신에서 9B 모델 중복 로딩**(메모리 트랩)을 피하기 위함.
  Ollama 엔드포인트(`localhost:11434`)·KURE 모델은 `BNK_Bot`과 공유, 컬렉션만 다름.
- **Docling/PDF 파싱 계층 전부 미사용.** 입력이 이미 구조화된 텍스트(코드/XML/SQL/스키마)라
  "PDF→텍스트" 작업 자체가 없다. docling·pdfplumber·PyMuPDF·rapidocr·onnxruntime 제거.
  그 자리는 코드 파서(Java/Spring · MyBatis XML · SQL)가 대신한다.
- **[확정] 자산 형식 = 코드/DDL 텍스트(프로토타입).** 스키마=DDL(`COMMENT` 포함, en+ko), SQL=MyBatis XML,
  소스=Java/Vue 파일 — 전부 구조화 텍스트라 **문서 파싱 0.** 코드/SQL 파서만으로 충분.
  (표준용어가 별도 파일로 들어오면 그때 CSV/리더 추가 — 현재 미확보.)

---

## 📚 데이터 자산 & 어휘 다리

**[프로토타입 데이터 형식 — 확정]** 실 사내 코드는 **영구 미접근.** 따라서 데이터는 **예시 웹 앱**
(백엔드·프론트·쿼리·스키마·메타)을 아래 형식으로 직접 작성해 *증명 기반(substrate)* 으로 삼는다.
형식은 실 환경(MariaDB `information_schema` + `COMMENT`)과 동형이라 현실적이다.

- **테이블 = 영어명 + 한글 설명을 DDL `COMMENT`에 함께 박는다.** 별도 매핑 파일 대신 스키마에 내장 → 단일 출처(single source of truth).

  ```sql
  CREATE TABLE TB_EXPENSE_EXEC (
    EXEC_NO  VARCHAR(20) COMMENT '집행번호',
    STATUS   CHAR(1)     COMMENT '상태(C:마감)',
    ...
  ) COMMENT='경비집행내역';
  ```

  - SQL 파서가 `table_en` / `table_ko` / `column_ko` / 코드값 한글을 **한 번에 결정론적 추출**(문서 파싱 불필요).
  - 컬럼·코드값 한글(`STATUS C:해지`)까지 COMMENT에 넣으면 "왜 막혔는가" 정밀도↑(테이블만이면 "어느 데이터"까지). **프로토타입에선 권장.**
- **코드 내 한글 주석 = 1급 증거.** 메서드/클래스 주석 → 처리 목적, 조건문·throw 옆 주석 → 그 분기/오류의 업무 의미.
  Extractor가 **코드 위치(메서드·조건·throw)에 묶어** 캡처한다. 제어흐름만으론 못 얻는 *업무 의도*의 일부를 코드 안에서 확보 → 인식론적 경계의 천장을 올린다.
- **어휘 다리.** 담당자는 "경비집행내역이 안 보여요"(한글), 코드는 `TB_EXPENSE…`(영어).
  payload에 `table_en`(정확 필터·lexical) + `table_ko`(임베딩·표시), branch 매뉴얼은 **한글명만** 노출. KURE가 한·영을 잇는다.

### 주석 신뢰 규율 (결정론 우선)

주석은 코드와 어긋날 수 있다(drift) → **증거지 진실이 아니다.**
- **숫자·조건 = 코드에서(verbatim) · 의도·설명 = 주석에서 · 업무 라벨 = table_ko에서.**
- 충돌 시 **코드가 이기고**, **사람 검토·동결**이 drift를 잡는다.

### glossary 자동화 (하드코딩 제거)

`table_ko` + 한글 주석 + (확보 시)표준용어에서 **데이터 기반 용어집**을 구성해 질의→엔티티 매핑에 쓴다.
`BNK_Bot_S`의 손으로 박은 한글 분기(`if "자동이체" in text`) 안티패턴을 제거하고 새 화면에 일반화한다.

---

## 🎯 결정론 우선 원칙 (`BNK_Bot`에서 계승)

금융 데이터는 변환·정제에서 **수치/조건이 바뀌면 안 된다.** 매뉴얼 생성에서:
- 추출된 사실(이율·금액·상태값·조건)은 verbatim 보존.
- LLM은 "정확한 추출" 위에 선별 요약/재진술만. 숫자 보존 가드레일을 건다.
- 결정론적 추출이 1차, LLM은 보강.

---

## ⚠️ 검증 전략 & 리스크 (실 코드는 영구 미접근)

실 사내 코드는 **앞으로도 접근 불가.** 따라서 이 PoC는 **현실적인 예시 웹 앱**을 직접 만들어
*그 위에서* 엔진이 동작함을 증명한다. **예시 앱이 곧 증명 기반.**

**증명의 신뢰도는 예시 앱의 "현실성"에 달렸다 (가장 중요):**
- **어렵게 만들 것** — 근거리 중복 화면 · 동적 SQL(`<if>`) · 프레임워크 indirection · 들쭉날쭉한 명명 · 주석 품질 편차 · 실패로직 없는 화면(도메인 밖). 너무 깨끗하면 "쉬운 것만 된다"만 증명한다.
- **순환 금지** — 앱을 *파서 편의에 맞춰* 짜면 증명이 공허해진다. 실제 개발자처럼 짜고, 엔진이 그걸 *따라가게* 한다.

핵심 리스크는 여전히 **Extractor의 추출 정확도**(동적 SQL·프레임워크 패턴). 나머지(매뉴얼 생성·게이트·핸드오프·검색)는 표준 엔지니어링.

### 좁게 시작해 키운다

- **슬라이스(P0~P5):** 예시 앱의 *대표 한 줌*(비슷한 화면 + 도메인 밖 포함)으로 추출→생성→적재→검색·게이트 로직을 증명(측정①②③).
- **확대(P6):** 예시 앱을 **현실적 규모·난이도**(많은 테이블·화면)로 키워 *규모에서도* 동작함을 시연. ← "1000 테이블"급 시연은 여기.
- 1000개를 *먼저* 짜고 로직을 만들면 설계 변경 시 낭비 → **한 줌으로 로직 확정 후 키운다.**

---

## 🛠️ 기술 스택 (예정)

- **언어/프레임워크:** Python / FastAPI (`BNK_Bot`과 동일, SpringBoot가 엔진을 호출하는 구조)
- **벡터 DB:** Qdrant (Docker, **새 별도 컨테이너** 포트 6335 · 컬렉션 `bnk_ops_knowledge`). 검색은 dense+sparse 하이브리드.
- **임베딩:** KURE-v1 (`nlpai-lab/KURE-v1`, 한국어 검색 특화, 1024-dim) — `BNK_Bot`과 공유
- **LLM:** `qwen3.5-bnk` (Qwen3.5:9b 파생, num_ctx 16384) via Ollama(OpenAI 호환) — `BNK_Bot`과 공유
- **lineage 저장소:** SQLite/그래프 (구조 탐색)
- **코드 파서:** Java/Spring · MyBatis XML · SQL (AST 수준 지향; `BNK_Bot_S` 프로토타입은 regex라 한계였음)
- **라이선스:** 전부 MIT/Apache 지향 (`BNK_Bot` 원칙 계승)

---

## 🗺️ 구현 로드맵 (단계별)

**원칙: 세로 슬라이스 1개를 끝까지 → 측정 → 통과해야 폭을 넓힌다.** 전 컴포넌트를 한 번에 펼치지 않는다.
엔진 = **변환(ingestion) + 질의(chat)** 둘 다 포함. SpringBoot·인증·검수 UI는 제외(엔진 밖).

### 슬라이스 단계 (P0~P5) — 척추 1줄을 증명

- **P0 · 스캐폴딩 & 샘플** ✅ **완료** (코드는 전부 새로)
  - FastAPI 골격(도메인 분리 `ingestion`/`chat`/`main`), `config`/`.env` — **새로 작성**(`BNK_Bot` 구조만 참고).
  - 새 Qdrant `docker-compose`(포트 6335, 컬렉션 `bnk_ops_knowledge`).
  - 어댑터(Qdrant/KURE/Qwen)도 **새로 작성**하되 `BNK_Bot`의 결정·함정만 계승(reasoning_effort=none, NFC, KURE 설정). **코드 복사 ❌.**
  - **샘플 1세트(새 형식):** DDL+`COMMENT` 스키마 · 한글 주석 있는 Spring 컨트롤러/서비스 · MyBatis 매퍼 · Vue 화면 1개. 작고 결정적으로(`BNK_Bot_S` bank_sample 각색).
  - ✅ 검증: 부팅 + `/health`(Qdrant 미가동 503 down → 가동 200 degraded) + `/query` 핸드오프 + 빈질문 422 + 컬렉션(dense+sparse) 자동 생성.

- **P1 · Extractor (가장 큰 리스크)** ✅ **완료**
  - 파서 4종(`parsers/ddl·mybatis·java·frontend`) + `extractor.py`(스캔→파싱→오퍼레이션 링크).
  - 화면→API→Service→Mapper→테이블 **lineage** + 표기의미(DDL COMMENT의 `table_ko`/컬럼/코드값) + 실패모드(throw 코드·메시지·조건 verbatim) + **한글 주석(throw 위치에 묶어)** 추출.
  - 출력 = `ExtractedOperation`(lineage·표기의미·실패모드·주석). **SQLite 그래프 적재는 P3에서**(지금은 in-memory).
  - **게이트(측정①) ✅ PASS:** `EXPENSE_REGISTER → /api/expense/save → ExpenseService.saveExpense → ExpenseMapper.insertExpense → TB_EXPENSE_EXEC` + 표기의미(STATUS C:마감 등) + 실패모드 3(E_AUTH/E_CLOSED/E_AMOUNT). `tests/test_extractor.py` 4/4.
  - 한계(정직): regex 기반 + 깨끗한 샘플로만 검증. 자체 프레임워크·동적 SQL 정확도는 P6에서 실 코드로 깬다.

- **P2 · 매뉴얼 생성 + 검수·동결** ✅ **완료**
  - `manual.py`(ManualBuilder) — 정적 빌더가 사실에서 직접 생성(결정론), Qwen은 *다듬기*만. Ollama 미가동/실패 시 정적 폴백.
  - branch는 내부 식별자(테이블·API·코드값·메서드) 차단(`is_branch_clean`), it는 조건 verbatim + 표기의미. 코드값 `C→마감` 조인.
  - 검수·동결: `scripts/build_manuals.py` → `data/manuals/{id}.json` + `.branch.md`/`.it.md`(검수용). `--freeze`로 status=frozen.
  - **게이트(측정②) ✅ PASS:** branch 무유출 + it 조건/체인 verbatim 보존. 실제 Qwen 다듬기 결과물도 클린 확인. `tests/test_manual.py` 4/4(정적·결정론).

- **P3 · 적재** ✅ **완료**
  - `indexer.py` + `qdrant_store.upsert/search`(dense) — 매뉴얼 1개 → role별 2 포인트(branch/it 본문 임베딩), payload(`screen_id`/`role`/`table` 등).
  - `scripts/load_manuals.py` → `data/manuals/*.json` 적재 + retrieve 확인. `/health` `degraded→ok`(points=2).
  - ⚠️ 지금은 **해시 임베딩 폴백**(sentence-transformers 미설치) — 적재·검색 *메커니즘*만 증명. **실 KURE 임베딩 + 하이브리드(sparse)는 P4**(의미 검색 품질).
  - lineage SQLite 그래프 적재는 질의 확장이 필요한 P4에서.

- **P4 · 질의 + 정밀도 게이트** ✅ **완료**
  - `retriever.py`(하이브리드: KURE dense + char-bigram lexical, payload role 필터) → `gate.py`(절대 임계 dense≥0.50 또는 lexical≥0.40) → `service.py`(충분: Qwen이 *매뉴얼 안에서만* 다듬어 답, branch 누출 검사·폴백 / 부족: 회피·핸드오프).
  - KURE-v1 설치(sentence-transformers) — 의미 임베딩으로 구어체 질문도 매칭.
  - **게이트(측정③) ✅ PASS (`scripts/eval_query.py`, 4/4):** 경비 저장→expense · **예산 등록→budget(근거리 중복 변별)** · 경비 승인→expense_approve(액션 변별) · 비밀번호→**핸드오프(회피)**. 임계는 측정으로 튜닝(관련 0.71~0.75 vs 도메인밖 0.42).
  - ⚠️ "하이브리드"의 sparse는 현재 char-bigram lexical로 근사. Qdrant 네이티브 sparse 벡터는 규모(P6)에서 필요 시 교체.

- **P5 · 측정 게이트 (슬라이스 종료 판정)**
  - `eval_retrieval`(식별자 recall 포함) + `eval_answer`(정확도·회피 양방향·숫자 충실도).
  - 측정①②③ 통과해야 다음으로. **여기서 A의 사업성이 판가름.**

### 확대 단계 (P6~) — 슬라이스 통과 후에만

- **P6 · 예시 앱 확대 + 일반화** — 예시 웹 앱을 **현실적 규모·난이도**(많은 테이블·화면, 동적 SQL, 프레임워크 패턴)로 키워 *규모에서도* 동작 시연 + Extractor 일반화. ← "1000 테이블"급 시연은 여기.
- **P7 · 핸드오프 축적 루프** — 넘긴 Q&A 적재 → 다음 빌드 매뉴얼 보강 피드백.

### 엔진 밖 (보류, 기록만)

- SpringBoot 연동(API 계약·인증), 검수 UI, 운영(코드 변경 시 재적재 스케줄), 응답 스트리밍.

> 핵심 원칙(`BNK_Bot` 계승): **결정론적 베이스라인 먼저 → 측정 → 부족한 곳에만 LLM/보정 투입.**
> 느낌이 아니라 측정으로 다음 작업을 정한다.
