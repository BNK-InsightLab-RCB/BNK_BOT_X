<template>
  <div class="expense-approve">
    <h1>경비집행내역 승인</h1>
    <input v-model="form.execNo" placeholder="집행번호" />
    <button @click="onApprove">승인</button>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "ExpenseApprove",
  data() {
    return { screenId: "EXPENSE_APPROVE", form: { execNo: "" } };
  },
  methods: {
    async onApprove() {
      const res = await axios.post("/api/expense/approve", this.form);
      if (res.data.code === "E_STATUS") {
        // 등록 상태가 아니면 승인 불가 안내
        alert("등록 상태인 경비만 승인할 수 있습니다.");
      }
    },
  },
};
</script>
