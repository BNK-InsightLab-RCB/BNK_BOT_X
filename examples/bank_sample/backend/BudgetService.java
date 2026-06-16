package com.bnk.budget;

import org.springframework.stereotype.Service;

@Service
public class BudgetService {

    private final BudgetMapper budgetMapper;

    public BudgetService(BudgetMapper budgetMapper) {
        this.budgetMapper = budgetMapper;
    }

    public ApiResponse saveBudget(BudgetDto dto) {
        // 예산 저장 권한이 없으면 처리할 수 없다
        if (!SecurityUtil.hasAuthority("BUDGET_SAVE")) {
            throw new BizException("E_AUTH", "예산 저장 권한이 없습니다.");
        }
        // 편성금액이 예산한도를 초과하면 저장할 수 없다
        if (dto.getAmount() != null && dto.getLimitAmt() != null
                && dto.getAmount().compareTo(dto.getLimitAmt()) > 0) {
            throw new BizException("E_LIMIT", "편성금액이 예산한도를 초과했습니다.");
        }
        budgetMapper.insertBudget(dto);
        return ApiResponse.ok();
    }
}
