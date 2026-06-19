<template>
  <BasicLayout>
    <div class="rounded-lg border border-slate-200 bg-white p-5">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-semibold text-slate-900">매뉴얼 목록</h2>
          <p class="mt-1 text-sm text-slate-500">검수된 매뉴얼을 확인하고 수정합니다.</p>
        </div>
        <button class="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700" @click="loadManuals">
          새로고침
        </button>
      </div>

      <CommonTableComponent class="mt-5">
        <template #head>
          <th class="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500">ID</th>
          <th class="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500">화면</th>
          <th class="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500">액션</th>
          <th class="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500">상태</th>
          <th class="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500">버전</th>
        </template>
        <tr v-for="manual in manuals" :key="manual.id" class="hover:bg-slate-50">
          <td class="px-4 py-3 text-sm font-medium text-bnk-blue">
            <RouterLink :to="`/admin/manuals/${manual.id}`">{{ manual.id }}</RouterLink>
          </td>
          <td class="px-4 py-3 text-sm text-slate-700">{{ manual.screenKo }}</td>
          <td class="px-4 py-3 text-sm text-slate-700">{{ manual.action }}</td>
          <td class="px-4 py-3 text-sm text-slate-700">{{ manual.status }}</td>
          <td class="px-4 py-3 text-sm text-slate-700">{{ manual.version }}</td>
        </tr>
      </CommonTableComponent>
    </div>
  </BasicLayout>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { getManuals } from '../../api/adminapi/adminAPI.js'
import CommonTableComponent from '../../common/CommonTableComponent.vue'
import BasicLayout from '../../layout/BasicLayout.vue'

const manuals = ref([])

const loadManuals = async () => {
  const res = await getManuals()
  manuals.value = res.items || []
}

onMounted(loadManuals)
</script>
