package com.bnk.expense;

import org.springframework.stereotype.Service;

@Service
public class ExpenseService {

    private final ExpenseMapper expenseMapper;

    public ExpenseService(ExpenseMapper expenseMapper) {
        this.expenseMapper = expenseMapper;
    }

    public ApiResponse saveExpense(ExpenseDto dto) {
        // 저장 권한이 없으면 처리할 수 없다
        if (!SecurityUtil.hasAuthority("EXPENSE_SAVE")) {
            throw new BizException("E_AUTH", "경비 저장 권한이 없습니다.");
        }
        // 마감(STATUS=C)된 경비는 수정할 수 없다
        ExpenseExec cur = expenseMapper.selectExpense(dto.getExecNo());
        if (cur != null && "C".equals(cur.getStatus())) {
            throw new BizException("E_CLOSED", "이미 마감된 경비는 수정할 수 없습니다.");
        }
        // 집행금액은 0보다 커야 한다
        if (dto.getAmount() == null || dto.getAmount().signum() <= 0) {
            throw new BizException("E_AMOUNT", "집행금액을 정확히 입력해 주세요.");
        }
        expenseMapper.insertExpense(dto);
        return ApiResponse.ok();
    }
}
