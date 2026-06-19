import jwtAxios from '../../util/jwtUtil.js'

export const askQuestion = async (question, mode = 'branch') => {
  const res = await jwtAxios.post('/chat/query', {
    question,
    mode,
    topK: 5
  })
  return res.data
}

export const getChatHistory = async () => {
  const res = await jwtAxios.get('/chat/history')
  return res.data
}
