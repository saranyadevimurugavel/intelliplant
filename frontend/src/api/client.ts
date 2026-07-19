import axios from 'axios'

// When served from FastAPI (port 8000), use relative /api
// When running dev server (port 5173), proxy handles it
export const api = axios.create({
  baseURL: '/api',
  timeout: 60_000,
  headers: { 'Content-Type': 'application/json' },
})

// Documents
export const uploadDocument = (file: File, category: string) => {
  const form = new FormData()
  form.append('file', file)
  form.append('category', category)
  return api.post('/documents/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
export const listDocuments = (params?: Record<string, string>) =>
  api.get('/documents/', { params })
export const getDocument = (id: string) => api.get(`/documents/${id}`)
export const searchKG = (q: string, node_type?: string) =>
  api.get('/documents/graph/search', { params: { q, node_type } })
export const getEntity = (id: string) => api.get(`/documents/graph/entity/${id}`)
export const getKGStats = () => api.get('/documents/stats/knowledge-graph')

// Copilot
export const querycopilot = (body: {
  query: string
  session_id?: string
  category_filter?: string
}) => api.post('/copilot/query', body)
export const listSessions = () => api.get('/copilot/sessions')
export const getMessages = (sessionId: string) =>
  api.get(`/copilot/sessions/${sessionId}/messages`)
export const deleteSession = (sessionId: string) =>
  api.delete(`/copilot/sessions/${sessionId}`)

// Maintenance
export const getRecommendations = (params?: Record<string, string>) =>
  api.get('/maintenance/recommendations', { params })
export const getMaintenanceHistory = (params?: Record<string, string>) =>
  api.get('/maintenance/history', { params })
export const runRCA = (asset_tag: string, failure_description: string) =>
  api.post('/maintenance/rca', { asset_tag, failure_description })
export const getSchedule = () => api.get('/maintenance/schedule')

// Compliance
export const getComplianceGaps = (params?: Record<string, string>) =>
  api.get('/compliance/gaps', { params })
export const getComplianceHealth = () => api.get('/compliance/health')
export const generateAuditPackage = (regulation: string) =>
  api.post('/compliance/audit-package', { regulation })

// Lessons
export const getLessons = (params?: Record<string, string>) =>
  api.get('/lessons/', { params })
export const getWarnings = () => api.get('/lessons/warnings')
export const analyzePatterns = (asset_tag?: string) =>
  api.get('/lessons/patterns', { params: asset_tag ? { asset_tag } : undefined })

// Health
export const getHealth = () => api.get('/health')
