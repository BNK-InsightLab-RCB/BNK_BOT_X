<template>
  <BasicLayout>
    <div class="rounded-lg border border-slate-200 bg-white p-5">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-semibold text-slate-900">핸드오프 목록</h2>
          <p class="mt-1 text-sm text-slate-500">챗봇이 확실히 답하지 못한 질문입니다.</p>
        </div>
        <button class="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700" @click="loadHandoffs">
          새로고침
        </button>
      </div>

      <CommonTableComponent class="mt-5">
        <template #head>
          <th class="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500">ID</th>
          <th class="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500">질문</th>
          <th class="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500">역할</th>
          <th class="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500">상태</th>
          <th class="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500">처리</th>
        </template>
        <tr v-for="item in items" :key="item.id" class="hover:bg-slate-50">
          <td class="px-4 py-3 text-sm text-slate-700">{{ item.id }}</td>
          <td class="px-4 py-3 text-sm text-slate-700">{{ item.question }}</td>
          <td class="px-4 py-3 text-sm text-slate-700">{{ item.role }}</td>
          <td class="px-4 py-3 text-sm text-slate-700">{{ item.status }}</td>
          <td class="px-4 py-3 text-sm">
            <button
              class="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
              @click="resolve(item.id)"
            >
              해소
            </button>
          </td>
        </tr>
      </CommonTableComponent>
    </div>
  </BasicLayout>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { getHandoffs, resolveHandoff } from '../../api/adminapi/adminAPI.js'
import CommonTableComponent from '../../common/CommonTableComponent.vue'
import BasicLayout from '../../layout/BasicLayout.vue'

const items = ref([])

const loadHandoffs = async () => {
  const res = await getHandoffs('open')
  items.value = res.items || []
}

const resolve = async (id) => {
  await resolveHandoff(id)
  await loadHandoffs()
}

onMounted(loadHandoffs)
</script>
