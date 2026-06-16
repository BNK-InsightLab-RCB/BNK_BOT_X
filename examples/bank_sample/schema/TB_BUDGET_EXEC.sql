-- 예산집행내역 테이블. 경비집행내역과 근거리 중복(검색 변별 시험용).
CREATE TABLE TB_BUDGET_EXEC (
    BUDGET_NO  VARCHAR(20) NOT NULL COMMENT '예산번호',
    DEPT_CD    VARCHAR(10) NOT NULL COMMENT '부서코드',
    AMOUNT     DECIMAL(15) NOT NULL COMMENT '편성금액',
    LIMIT_AMT  DECIMAL(15) COMMENT '예산한도',
    STATUS     CHAR(1)     NOT NULL COMMENT '상태(R:등록, A:승인, C:마감)',
    PRIMARY KEY (BUDGET_NO)
) COMMENT='예산집행내역';
