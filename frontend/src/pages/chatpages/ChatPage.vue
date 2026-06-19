<template>
  <BasicLayout>
    <div class="grid gap-6 xl:h-[calc(100dvh-7rem)] xl:min-h-[520px] xl:grid-rows-[minmax(0,1fr)] xl:overflow-hidden xl:grid-cols-[minmax(0,1fr)_340px]">
      <section class="flex h-[calc(100dvh-7rem)] min-h-[520px] flex-col overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm xl:h-full">
        <header class="flex items-center justify-between gap-4 border-b border-slate-200 bg-white/95 px-5 py-4 backdrop-blur">
          <div class="flex items-center gap-3">
            <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-bnk-blue text-white shadow-sm">
              <Bot class="h-5 w-5" />
            </div>
            <div>
              <h2 class="text-base font-semibold text-slate-950">BNK Bot</h2>
              <p class="text-sm text-slate-500">영업점 업무 지원</p>
            </div>
          </div>
          <div v-if="authStore.isAdmin" class="flex rounded-md border border-slate-300 p-1 text-sm">
            <button
              class="rounded px-3 py-1.5"
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
        </header>

        <div ref="scrollArea" class="min-h-0 flex-1 overflow-y-auto bg-gradient-to-b from-slate-50 to-white px-5 py-6">
          <div class="mx-auto flex max-w-4xl flex-col gap-5">
            <div v-if="messages.length === 0" class="flex items-start gap-3">
              <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white text-bnk-blue shadow-sm ring-1 ring-slate-200">
                <Sparkles class="h-4 w-4" />
              </div>
              <div class="max-w-[760px] rounded-2xl rounded-tl-md border border-slate-200 bg-white px-4 py-3 text-sm leading-7 text-slate-700 shadow-sm">
                무엇을 도와드릴까요?
              </div>
            </div>

            <div
              v-for="message in messages"
              :key="message.id"
              class="flex items-end gap-3"
              :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
            >
              <div
                v-if="message.role === 'assistant'"
                class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white text-bnk-blue shadow-sm ring-1 ring-slate-200"
              >
                <Bot class="h-4 w-4" />
              </div>

              <div class="max-w-[78%]">
                <div
                  class="markdown-body px-4 py-3 text-sm leading-7 shadow-sm"
                  :class="message.role === 'user'
                    ? 'rounded-2xl rounded-br-md bg-bnk-blue text-white'
                    : 'rounded-2xl rounded-bl-md border border-slate-200 bg-white text-slate-800'"
                  v-html="renderMarkdown(message.text)"
                ></div>
                <div v-if="message.role === 'assistant' && message.handoff" class="mt-2">
                  <span class="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800">
                    개발자 문의 필요
                  </span>
                </div>
              </div>

              <div
                v-if="message.role === 'user'"
                class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-600"
              >
                <UserRound class="h-4 w-4" />
              </div>
            </div>

            <div v-if="loading" class="flex items-start gap-3">
              <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white text-bnk-blue shadow-sm ring-1 ring-slate-200">
                <Bot class="h-4 w-4" />
              </div>
              <div class="rounded-2xl rounded-tl-md border border-slate-200 bg-white px-4 py-3 shadow-sm">
                <LoadingComponent />
              </div>
            </div>
          </div>
        </div>

        <form class="border-t border-slate-200 bg-white px-5 py-4" @submit.prevent="submitQuestion">
          <div class="mx-auto flex max-w-4xl items-end gap-3 rounded-2xl border border-slate-300 bg-slate-50 px-4 py-3 focus-within:border-bnk-blue focus-within:ring-1 focus-within:ring-bnk-blue">
            <textarea
              v-model="question"
              class="max-h-36 min-h-12 flex-1 resize-none bg-transparent py-2 text-sm text-slate-800 outline-none placeholder:text-slate-400"
              placeholder="업무 중 막힌 내용을 입력하세요"
              @keydown.enter.exact.prevent="submitQuestion"
            />
            <button
              class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-bnk-blue text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
              type="submit"
              :disabled="loading || !question.trim()"
              aria-label="질문 보내기"
            >
              <SendHorizontal class="h-4 w-4" />
            </button>
          </div>
        </form>
      </section>

      <aside class="flex min-h-0 flex-col gap-6 xl:h-full xl:overflow-hidden">
        <section class="shrink-0 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h3 class="text-sm font-semibold text-slate-900">근거 매뉴얼</h3>
          <div class="mt-3 max-h-56 space-y-3 overflow-y-auto pr-1">
            <div v-for="source in sources" :key="source.manualId" class="rounded-md border border-slate-200 p-3">
              <p class="text-sm font-medium text-slate-900">{{ source.screenKo || source.manualId }}</p>
              <p class="mt-1 text-xs text-slate-500">{{ source.action }} · score {{ source.score ?? '-' }}</p>
            </div>
            <p v-if="!sources.length" class="text-sm text-slate-500">아직 근거가 없습니다.</p>
          </div>
        </section>

        <section class="flex min-h-0 flex-1 flex-col rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h3 class="text-sm font-semibold text-slate-900">최근 질문</h3>
          <div class="mt-3 min-h-0 flex-1 space-y-3 overflow-y-auto pr-1">
            <button
              v-for="item in history"
              :key="item.chatLogId"
              class="block w-full rounded-md border border-slate-200 p-3 text-left text-sm hover:bg-slate-50"
              @click="selectHistory(item.question)"
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
import { Bot, SendHorizontal, Sparkles, UserRound } from '@lucide/vue'
import { marked } from 'marked'
import { nextTick, onMounted, ref } from 'vue'
import { askQuestion, getChatHistory } from '../../api/chatapi/chatAPI.js'
import LoadingComponent from '../../common/LoadingComponent.vue'
import BasicLayout from '../../layout/BasicLayout.vue'
import { useAuthStore } from '../../stores/authStore.js'

const authStore = useAuthStore()
const question = ref('')
const mode = ref('branch')
const loading = ref(false)
const scrollArea = ref(null)
const sources = ref([])
const history = ref([])
const messages = ref([])
let messageSeq = 1

const renderMarkdown = (text) => DOMPurify.sanitize(marked.parse(text || ''))

const loadHistory = async () => {
  history.value = await getChatHistory()
}

const scrollToBottom = async () => {
  await nextTick()
  if (scrollArea.value) {
    scrollArea.value.scrollTop = scrollArea.value.scrollHeight
  }
}

const selectHistory = (text) => {
  question.value = text
}

const submitQuestion = async () => {
  const text = question.value.trim()
  if (!text || loading.value) return

  messages.value.push({
    id: messageSeq++,
    role: 'user',
    text
  })
  question.value = ''
  await scrollToBottom()

  loading.value = true
  try {
    const res = await askQuestion(text, authStore.isAdmin ? mode.value : 'branch')
    messages.value.push({
      id: messageSeq++,
      role: 'assistant',
      text: res.answer,
      handoff: res.handoff
    })
    sources.value = res.sources || []
    await loadHistory()
  } catch {
    messages.value.push({
      id: messageSeq++,
      role: 'assistant',
      text: '현재 답변을 가져오지 못했습니다. 잠시 후 다시 시도해 주세요.',
      handoff: true
    })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

onMounted(async () => {
  await loadHistory()
  await scrollToBottom()
})
</script>
