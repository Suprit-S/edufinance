import axios from 'axios'

/**
 * Single Axios instance for the whole app.
 * - baseURL '/api': same origin in dev (Vite proxy) and production (nginx).
 * - Attaches the JWT (Sprint 1) from sessionStorage.
 * - Normalises every error to { status, code, message, details }.
 */
export const TOKEN_KEY = 'edufinance.token'

const api = axios.create({ baseURL: '/api', timeout: 15000 })

api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem(TOKEN_KEY)
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export function normaliseError(error) {
  const status = error?.response?.status ?? 0
  const body = error?.response?.data?.error
  return {
    status,
    code: body?.code ?? (status ? 'HTTP_ERROR' : 'NETWORK_ERROR'),
    message:
      body?.message ??
      (status ? 'Something went wrong.' : 'Cannot reach the server. Check your connection.'),
    details: body?.details ?? null,
  }
}

api.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(normaliseError(error)),
)

export default api
