<template>
  <div class="expense-register">
    <h1>경비집행내역 등록</h1>
    <input v-model="form.execNo" placeholder="집행번호" />
    <input v-model.number="form.amount" placeholder="집행금액" />
    <button @click="onSave">저장</button>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "ExpenseRegister",
  data() {
    return {
      screenId: "EXPENSE_REGISTER",
      form: { execNo: "", deptCd: "", amount: 0 },
    };
  },
  methods: {
    async onSave() {
      // 집행금액 필수 입력 확인
      if (!this.form.amount) {
        alert("집행금액을 입력해 주세요.");
        return;
      }
      const res = await axios.post("/api/expense/save", this.form);
      if (res.data.code === "E_AUTH") {
        // 저장 권한 없음 안내
        alert("저장 권한이 없습니다. 권한 담당자에게 문의하세요.");
      }
    },
  },
};
</script>
