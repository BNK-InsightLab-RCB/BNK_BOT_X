"""MyBatis SELECT 컬럼 추출."""

from src.ingestion.parsers.mybatis import parse_mybatis


def test_select_columns_attach_to_single_table_without_keyword_alias(tmp_path):
    mapper = tmp_path / "LoanMapper.xml"
    mapper.write_text(
        """
        <mapper namespace="com.example.LoanMapper">
          <select id="findProducts">
            SELECT PRODUCT_CD, PRODUCT_NM, STATUS
            FROM TB_LOAN_PRODUCT WHERE STATUS = 'ACTIVE'
          </select>
        </mapper>
        """,
        encoding="utf-8",
    )

    parsed = parse_mybatis(mapper)

    assert parsed["LoanMapper.findProducts"]["columns_by_table"] == {
        "TB_LOAN_PRODUCT": ["PRODUCT_CD", "PRODUCT_NM", "STATUS"]
    }


def test_select_columns_follow_explicit_join_aliases(tmp_path):
    mapper = tmp_path / "LoanMapper.xml"
    mapper.write_text(
        """
        <mapper namespace="com.example.LoanMapper">
          <select id="findHistory">
            SELECT L.LOAN_NO, L.STATUS, P.PRODUCT_NM
            FROM TB_LOAN_EXEC L
            LEFT JOIN TB_LOAN_PRODUCT P ON L.PRODUCT_CD = P.PRODUCT_CD
          </select>
        </mapper>
        """,
        encoding="utf-8",
    )

    parsed = parse_mybatis(mapper)

    assert parsed["LoanMapper.findHistory"]["columns_by_table"] == {
        "TB_LOAN_EXEC": ["LOAN_NO", "STATUS"],
        "TB_LOAN_PRODUCT": ["PRODUCT_NM"],
    }
