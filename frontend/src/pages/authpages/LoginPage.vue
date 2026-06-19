<template>
  <div class="flex min-h-screen items-center justify-center bg-bnk-gray px-4">
    <div class="grid w-full max-w-5xl overflow-hidden rounded-lg bg-white shadow-xl md:grid-cols-2">
      <section class="flex flex-col justify-between bg-bnk-navy p-10 text-white">
        <div>
          <p class="text-sm font-semibold text-bnk-gold">BNK Bot X</p>
          <h1 class="mt-4 text-3xl font-bold">업무 지원 챗봇</h1>
          <p class="mt-4 text-sm leading-6 text-slate-200">
            은행 직원은 질문 화면으로, 관리자는 매뉴얼과 핸드오프 관리 화면으로 이동합니다.
          </p>
        </div>
        <div class="mt-12 rounded-md bg-white/10 p-4 text-sm text-slate-100">
          <p>테스트 계정</p>
          <p class="mt-2">관리자: admin / admin123</p>
          <p>직원: employee / employee123</p>
        </div>
      </section>

      <section class="p-10">
        <h2 class="text-2xl font-semibold text-slate-900">로그인</h2>
        <form class="mt-8 space-y-5" @submit.prevent="handleLogin">
          <label class="block">
            <span class="text-sm font-medium text-slate-700">아이디</span>
            <input
              v-model="form.loginId"
              class="mt-2 block w-full rounded-md border border-slate-300 px-3 py-3 text-sm focus:border-bnk-blue focus:outline-none focus:ring-1 focus:ring-bnk-blue"
              type="text"
              autocomplete="username"
            />
          </label>
          <label class="block">
            <span class="text-sm font-medium text-slate-700">비밀번호</span>
            <input
              v-model="form.password"
              class="mt-2 block w-full rounded-md border border-slate-300 px-3 py-3 text-sm focus:border-bnk-blue focus:outline-none focus:ring-1 focus:ring-bnk-blue"
              type="password"
              autocomplete="current-password"
            />
          </label>
          <p v-if="errorMessage" class="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {{ errorMessage }}
          </p>
          <button
            class="w-full rounded-md bg-bnk-blue px-4 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
            type="submit"
            :disabled="loading"
          >
            {{ loading ? '로그인 중' : '로그인' }}
          </button>
        </form>
      </section>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '../../api/authapi/authAPI.js'
import { useAuthStore } from '../../stores/authStore.js'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const errorMessage = ref('')
const form = reactive({
  loginId: '',
  password: ''
})

const handleLogin = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const data = await login(form)
    authStore.setAuth(data)
    await router.push(data.role === 'ADMIN' ? '/admin' : '/chat')
  } catch {
    errorMessage.value = '아이디 또는 비밀번호를 확인해 주세요.'
  } finally {
    loading.value = false
  }
}
</script>
