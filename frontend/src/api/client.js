import axios from 'axios'

/**
 * Single Axios instance for the whole app.
 * - baseURL '/api': same origin in dev (Vite proxy) and production (nginx).
 * - Attaches the JWT from sessionStorage (cleared when the tab closes).
 * - Normalises every error to { status, code, message, details }.
 * - Reports 401 responses of authenticated calls so the app can log out.
 */
export const TOKEN_KEY = 'edufinance.token'

export function getToken() {
  try {
    return sessionStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token) {
  try {
    if (token) sessionStorage.setItem(TOKEN_KEY, token)
    else sessionStorage.removeItem(TOKEN_KEY)
  } catch {
    /* storage blocked: the session lasts only in memory */
  }
}

let unauthorizedHandler = null

/** Register a callback for expired/invalid sessions (set by AuthProvider). */
export function onUnauthorized(handler) {
  unauthorizedHandler = handler
}

const api = axios.create({ baseURL: '/api', timeout: 15000 })

api.interceptors.request.use((config) => {
  const token = getToken()
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

/** Field errors from a 422 response as { field: 'first message' }. */
export function fieldErrors(err) {
  const out = {}
  const details = err?.details
  if (!details || typeof details !== 'object') return out
  for (const [key, value] of Object.entries(details)) {
    if (Array.isArray(value)) out[key] = String(value[0])
    else if (value && typeof value === 'object') out[key] = Object.values(value).flat().join(' ')
    else out[key] = String(value)
  }
  return out
}

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const err = normaliseError(error)
    const hadToken = Boolean(error?.config?.headers?.Authorization)
    if (err.status === 401 && hadToken && unauthorizedHandler) unauthorizedHandler(err)
    return Promise.reject(err)
  },
)

export default api
