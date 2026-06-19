<template>
  <BasicLayout>
    <div class="grid gap-6 xl:grid-cols-[1fr_340px]">
      <section class="rounded-lg border border-slate-200 bg-white p-5">
        <div class="flex items-center justify-between gap-4">
          <div>
            <h2 class="text-lg font-semibold text-slate-900">업무 질문</h2>
            <p class="mt-1 text-sm text-slate-500">은행 직원 답변은 업무 언어로 표시됩니다.</p>
          </div>
          <div v-if="authStore.isAdmin" class="flex rounded-md border border-slate-300 p-1 text-sm">
            <button
              class="rounded px-3 py-1"
              :class="mode === 'branch' ? 'bg-bnk-blue text-white' : 'text-slate-600'"
              @click="mode = 'branch'"
            >
              직원용
            </button>
            <button
              class="rounded px-3 py-1"
              :class="mode === 'it' ? 'bg-bnk-blue text-white' : 'text-slate-600'"
              @click="mode = 'it'"
            >
              IT상세
            </button>
          </div>
        </div>

        <form class="mt-5" @submit.prevent="submitQuestion">
          <textarea
            v-model="question"
            class="h-32 w-full resize-none rounded-md border border-slate-300 p-4 text-sm focus:border-bnk-blue focus:outline-none focus:ring-1 focus:ring-bnk-blue"
            placeholder="예: 예금 신규가 안돼요"
          />
          <div class="mt-3 flex justify-end">
            <button
              class="rounded-md bg-bnk-blue px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
              type="submit"
              :disabled="loading || !question.trim()"
            >
              질문하기
            </button>
          </div>
        </form>

        <div class="mt-6 rounded-lg border border-slate-200 bg-slate-50 p-5">
          <LoadingComponent v-if="loading" />
          <div v-else-if="answer" class="space-y-4">
            <div class="flex items-center gap-2">
              <span
                class="rounded-full px-3 py-1 text-xs font-semibold"
                :class="handoff ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'"
              >
                {{ handoff ? '개발자 문의 필요' : '답변 가능' }}
              </span>
            </div>
            <div class="markdown-body rounded-md bg-white p-4 text-sm leading-7 text-slate-800" v-html="answerHtml"></div>
          </div>
          <p v-else class="text-sm text-slate-500">질문하면 답변이 여기에 표시됩니다.</p>
        </div>
      </section>

      <aside class="space-y-6">
        <section class="rounded-lg border border-slate-200 bg-white p-5">
          <h3 class="text-sm font-semibold text-slate-900">근거 매뉴얼</h3>
          <div class="mt-3 space-y-3">
            <div v-for="source in sources" :key="source.manualId" class="rounded-md border border-slate-200 p-3">
              <p class="text-sm font-medium text-slate-900">{{ source.screenKo || source.manualId }}</p>
              <p class="mt-1 text-xs text-slate-500">{{ source.action }} · score {{ source.score ?? '-' }}</p>
            </div>
            <p v-if="!sources.length" class="text-sm text-slate-500">아직 근거가 없습니다.</p>
          </div>
        </section>

        <section class="rounded-lg border border-slate-200 bg-white p-5">
          <h3 class="text-sm font-semibold text-slate-900">최근 질문</h3>
          <div class="mt-3 space-y-3">
            <button
              v-for="item in history"
              :key="item.chatLogId"
              class="block w-full rounded-md border border-slate-200 p-3 text-left text-sm hover:bg-slate-50"
              @click="question = item.question"
            >
              <span class="line-clamp-2 text-slate-700">{{ item.question }}</span>
            </button>
            <p v-if="!history.length" class="text-sm text-slate-500">최근 질문이 없습니다.</p>
          </div>
        </section>
      </aside>
    </div>
  </BasicLayout>
</template>

<script setup>
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import { computed, onMounted, ref } from 'vue'
import { askQuestion, getChatHistory } from '../../api/chatapi/chatAPI.js'
import LoadingComponent from '../../common/LoadingComponent.vue'
import BasicLayout from '../../layout/BasicLayout.vue'
import { useAuthStore } from '../../stores/authStore.js'

const authStore = useAuthStore()
const question = ref('')
const mode = ref('branch')
const loading = ref(false)
const answer = ref('')
const handoff = ref(false)
const sources = ref([])
const history = ref([])

const answerHtml = computed(() => DOMPurify.sanitize(marked.parse(answer.value || '')))

const loadHistory = async () => {
  history.value = await getChatHistory()
}

const submitQuestion = async () => {
  loading.value = true
  try {
    const res = await askQuestion(question.value, authStore.isAdmin ? mode.value : 'branch')
    answer.value = res.answer
    handoff.value = res.handoff
    sources.value = res.sources || []
    await loadHistory()
  } finally {
    loading.value = false
  }
}

onMounted(loadHistory)
</script>
