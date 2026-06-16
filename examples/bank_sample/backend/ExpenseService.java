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

    public ApiResponse approveExpense(ExpenseDto dto) {
        // 승인 권한이 없으면 처리할 수 없다
        if (!SecurityUtil.hasAuthority("EXPENSE_APPROVE")) {
            throw new BizException("E_AUTH", "경비 승인 권한이 없습니다.");
        }
        // 등록(STATUS=R) 상태인 경비만 승인할 수 있다
        ExpenseExec cur = expenseMapper.selectExpense(dto.getExecNo());
        if (cur == null || !"R".equals(cur.getStatus())) {
            throw new BizException("E_STATUS", "등록 상태인 경비만 승인할 수 있습니다.");
        }
        expenseMapper.updateStatus(dto.getExecNo());
        return ApiResponse.ok();
    }
}
