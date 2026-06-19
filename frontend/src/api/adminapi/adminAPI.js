import jwtAxios from '../../util/jwtUtil.js'

export const getEngineHealth = async () => {
  const res = await jwtAxios.get('/admin/engine/health')
  return res.data
}

export const runIngest = async () => {
  const res = await jwtAxios.post('/admin/engine/ingest')
  return res.data
}

export const getHandoffs = async (status = 'open') => {
  const res = await jwtAxios.get(`/admin/handoffs?status=${status}`)
  return res.data
}

export const resolveHandoff = async (handoffId) => {
  const res = await jwtAxios.post(`/admin/handoffs/${handoffId}/resolve`)
  return res.data
}

export const getManuals = async () => {
  const res = await jwtAxios.get('/admin/manuals')
  return res.data
}

export const getManual = async (manualId) => {
  const res = await jwtAxios.get(`/admin/manuals/${manualId}`)
  return res.data
}

export const editManual = async (manualId, payload) => {
  const res = await jwtAxios.put(`/admin/manuals/${manualId}`, payload)
  return res.data
}

export const approveManual = async (manualId) => {
  const res = await jwtAxios.post(`/admin/manuals/${manualId}/approve`)
  return res.data
}
