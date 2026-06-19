<template>
  <BasicLayout>
    <div class="space-y-6">
      <section class="rounded-lg border border-slate-200 bg-white p-5">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-sm text-slate-500">{{ manual?.screenKo }} / {{ manual?.action }}</p>
            <h2 class="mt-1 text-lg font-semibold text-slate-900">{{ manualId }}</h2>
            <p class="mt-1 text-sm text-slate-500">상태 {{ manual?.status }} · v{{ manual?.version }}</p>
          </div>
          <div class="flex gap-2">
            <button class="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700" @click="loadManual">
              새로고침
            </button>
            <button class="rounded-md bg-bnk-blue px-4 py-2 text-sm font-semibold text-white" @click="saveManual">
              저장
            </button>
            <button class="rounded-md bg-bnk-gold px-4 py-2 text-sm font-semibold text-slate-900" @click="approve">
              승인
            </button>
          </div>
        </div>
      </section>

      <section class="grid gap-6 xl:grid-cols-2">
        <div class="rounded-lg border border-slate-200 bg-white p-5">
          <h3 class="text-sm font-semibold text-slate-900">직원용 매뉴얼</h3>
          <textarea
            v-model="form.branchMd"
            class="mt-3 h-[520px] w-full resize-none rounded-md border border-slate-300 p-4 font-mono text-sm focus:border-bnk-blue focus:outline-none focus:ring-1 focus:ring-bnk-blue"
          />
        </div>
        <div class="rounded-lg border border-slate-200 bg-white p-5">
          <h3 class="text-sm font-semibold text-slate-900">IT 상세 매뉴얼</h3>
          <textarea
            v-model="form.itMd"
            class="mt-3 h-[520px] w-full resize-none rounded-md border border-slate-300 p-4 font-mono text-sm focus:border-bnk-blue focus:outline-none focus:ring-1 focus:ring-bnk-blue"
          />
        </div>
      </section>
    </div>
  </BasicLayout>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { approveManual, editManual, getManual } from '../../api/adminapi/adminAPI.js'
import BasicLayout from '../../layout/BasicLayout.vue'

const route = useRoute()
const manualId = route.params.manualId
const manual = ref(null)
const form = reactive({
  branchMd: '',
  itMd: ''
})

const loadManual = async () => {
  manual.value = await getManual(manualId)
  form.branchMd = manual.value.branchMd || ''
  form.itMd = manual.value.itMd || ''
}

const saveManual = async () => {
  await editManual(manualId, { branchMd: form.branchMd, itMd: form.itMd })
  await loadManual()
}

const approve = async () => {
  await approveManual(manualId)
  await loadManual()
}

onMounted(loadManual)
</script>
