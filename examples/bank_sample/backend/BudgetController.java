package com.bnk.budget;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/budget")
public class BudgetController {

    private final BudgetService budgetService;

    public BudgetController(BudgetService budgetService) {
        this.budgetService = budgetService;
    }

    // 예산집행내역 저장
    @PostMapping("/save")
    public ApiResponse save(@RequestBody BudgetDto dto) {
        return budgetService.saveBudget(dto);
    }
}
