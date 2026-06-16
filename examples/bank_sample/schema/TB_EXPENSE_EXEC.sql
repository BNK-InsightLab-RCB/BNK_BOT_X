-- 경비집행내역 테이블. 영문명 + 한글 설명을 COMMENT에 함께(단일 출처).
CREATE TABLE TB_EXPENSE_EXEC (
    EXEC_NO   VARCHAR(20)  NOT NULL COMMENT '집행번호',
    DEPT_CD   VARCHAR(10)  NOT NULL COMMENT '부서코드',
    AMOUNT    DECIMAL(15)  NOT NULL COMMENT '집행금액',
    STATUS    CHAR(1)      NOT NULL COMMENT '상태(R:등록, A:승인, C:마감)',
    USE_YN    CHAR(1)      DEFAULT 'Y' COMMENT '사용여부(Y:사용, N:미사용)',
    REG_USER  VARCHAR(20)  COMMENT '등록자',
    PRIMARY KEY (EXEC_NO)
) COMMENT='경비집행내역';
