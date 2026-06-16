package com.bnk.expense;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/expense")
public class ExpenseController {

    private final ExpenseService expenseService;

    public ExpenseController(ExpenseService expenseService) {
        this.expenseService = expenseService;
    }

    // 경비집행내역 저장
    @PostMapping("/save")
    public ApiResponse save(@RequestBody ExpenseDto dto) {
        return expenseService.saveExpense(dto);
    }
}
