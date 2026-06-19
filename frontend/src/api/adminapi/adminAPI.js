import jwtAxios from '../../util/jwtUtil.js'

const normalizeManual = (manual = {}) => ({
  ...manual,
  screenId: manual.screenId ?? manual.screen_id ?? '',
  screenKo: manual.screenKo ?? manual.screen_ko ?? '',
  apiPath: manual.apiPath ?? manual.api_path ?? '',
  tableEn: manual.tableEn ?? manual.table_en ?? [],
  tableKo: manual.tableKo ?? manual.table_ko ?? [],
  branchMd: manual.branchMd ?? manual.branch_md ?? '',
  itMd: manual.itMd ?? manual.it_md ?? '',
  lineageRef: manual.lineageRef ?? manual.lineage_ref ?? [],
  reviewedAt: manual.reviewedAt ?? manual.reviewed_at ?? '',
  reviewedBy: manual.reviewedBy ?? manual.reviewed_by ?? ''
})

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
  return {
    ...res.data,
    items: (res.data.items || []).map(normalizeManual)
  }
}

export const getManual = async (manualId) => {
  const res = await jwtAxios.get(`/admin/manuals/${manualId}`)
  return normalizeManual(res.data)
}

export const editManual = async (manualId, payload) => {
  const res = await jwtAxios.put(`/admin/manuals/${manualId}`, payload)
  return res.data
}

export const approveManual = async (manualId) => {
  const res = await jwtAxios.post(`/admin/manuals/${manualId}/approve`)
  return res.data
}
