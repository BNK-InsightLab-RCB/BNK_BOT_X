import jwtAxios from '../../util/jwtUtil.js'

const normalizeSource = (source = {}) => ({
  ...source,
  manualId: source.manualId ?? source.manual_id ?? '',
  screenKo: source.screenKo ?? source.screen_ko ?? '',
  score: source.score
})

const normalizeChatResponse = (data = {}) => ({
  ...data,
  sources: (data.sources || []).map(normalizeSource),
  related: (data.related || []).map(normalizeSource)
})

export const askQuestion = async (question, mode = 'branch') => {
  const res = await jwtAxios.post('/chat/query', {
    question,
    mode,
    topK: 5
  })
  return normalizeChatResponse(res.data)
}

export const getChatHistory = async () => {
  const res = await jwtAxios.get('/chat/history')
  return res.data
}
