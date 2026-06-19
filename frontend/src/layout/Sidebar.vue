<template>
  <aside class="flex w-64 flex-col border-r border-slate-200 bg-white">
    <div class="border-b border-slate-200 px-6 py-5">
      <p class="text-xs font-semibold uppercase tracking-wide text-bnk-blue">BNK Bot X</p>
      <p class="mt-1 text-xl font-bold text-bnk-navy">Ops Support</p>
    </div>

    <nav class="flex-1 space-y-1 px-3 py-4">
      <RouterLink
        to="/chat"
        class="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
        active-class="bg-bnk-blue text-white hover:bg-bnk-blue"
      >
        <MessageSquare class="h-4 w-4" />
        질문하기
      </RouterLink>

      <template v-if="authStore.isAdmin">
        <RouterLink
          to="/admin"
          class="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
          active-class="bg-bnk-blue text-white hover:bg-bnk-blue"
        >
          <LayoutDashboard class="h-4 w-4" />
          대시보드
        </RouterLink>
        <RouterLink
          to="/admin/manuals"
          class="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
          active-class="bg-bnk-blue text-white hover:bg-bnk-blue"
        >
          <FileText class="h-4 w-4" />
          매뉴얼
        </RouterLink>
        <RouterLink
          to="/admin/handoffs"
          class="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
          active-class="bg-bnk-blue text-white hover:bg-bnk-blue"
        >
          <Inbox class="h-4 w-4" />
          핸드오프
        </RouterLink>
      </template>
    </nav>
  </aside>
</template>

<script setup>
import { FileText, Inbox, LayoutDashboard, MessageSquare } from '@lucide/vue'
import { useAuthStore } from '../stores/authStore.js'

const authStore = useAuthStore()
</script>
