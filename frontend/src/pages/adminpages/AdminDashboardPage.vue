<template>
  <BasicLayout>
    <div class="grid gap-6 lg:grid-cols-3">
      <section class="rounded-lg border border-slate-200 bg-white p-5">
        <p class="text-sm text-slate-500">엔진 상태</p>
        <h2 class="mt-2 text-2xl font-bold text-slate-900">{{ engineStatus }}</h2>
        <p class="mt-2 text-sm text-slate-500">FastAPI 내부 엔진 health 결과입니다.</p>
      </section>
      <section class="rounded-lg border border-slate-200 bg-white p-5">
        <p class="text-sm text-slate-500">관리 메뉴</p>
        <div class="mt-4 flex gap-2">
          <RouterLink class="rounded-md bg-bnk-blue px-4 py-2 text-sm font-semibold text-white" to="/admin/manuals">
            매뉴얼 관리
          </RouterLink>
          <RouterLink class="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700" to="/admin/handoffs">
            핸드오프
          </RouterLink>
        </div>
      </section>
      <section class="rounded-lg border border-slate-200 bg-white p-5">
        <p class="text-sm text-slate-500">적재</p>
        <button
          class="mt-4 rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          @click="handleIngest"
        >
          엔진 적재 실행
        </button>
        <p v-if="ingestResult" class="mt-3 text-sm text-slate-600">{{ ingestResult }}</p>
      </section>
    </div>
  </BasicLayout>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { getEngineHealth, runIngest } from '../../api/adminapi/adminAPI.js'
import BasicLayout from '../../layout/BasicLayout.vue'

const engineStatus = ref('확인 중')
const ingestResult = ref('')

const loadHealth = async () => {
  try {
    const health = await getEngineHealth()
    engineStatus.value = health.status || 'unknown'
  } catch {
    engineStatus.value = 'down'
  }
}

const handleIngest = async () => {
  const res = await runIngest()
  ingestResult.value = res.status || '요청 완료'
}

onMounted(loadHealth)
</script>
