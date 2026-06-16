<template>
  <div class="budget-register">
    <h1>예산집행내역 등록</h1>
    <input v-model="form.budgetNo" placeholder="예산번호" />
    <input v-model.number="form.amount" placeholder="편성금액" />
    <button @click="onSave">저장</button>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "BudgetRegister",
  data() {
    return { screenId: "BUDGET_REGISTER", form: { budgetNo: "", amount: 0, limitAmt: 0 } };
  },
  methods: {
    async onSave() {
      const res = await axios.post("/api/budget/save", this.form);
      if (res.data.code === "E_LIMIT") {
        // 예산한도 초과 안내
        alert("편성금액이 예산한도를 초과했습니다.");
      }
    },
  },
};
</script>
