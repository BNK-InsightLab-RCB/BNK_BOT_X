<template>
  <header class="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6">
    <div>
      <p class="text-sm text-slate-500">BNK 업무 지원 챗봇</p>
      <h1 class="text-lg font-semibold text-slate-900">{{ title }}</h1>
    </div>
    <div class="flex items-center gap-3">
      <span class="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700">
        {{ authStore.userName }}
      </span>
      <button
        class="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
        @click="handleLogout"
      >
        로그아웃
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore.js'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const title = computed(() => {
  if (route.path.startsWith('/admin/manuals')) return '매뉴얼 관리'
  if (route.path.startsWith('/admin/handoffs')) return '핸드오프 관리'
  if (route.path.startsWith('/admin')) return '관리자 대시보드'
  return '질문하기'
})

const handleLogout = () => {
  authStore.clearAuth()
  router.push('/login')
}
</script>
