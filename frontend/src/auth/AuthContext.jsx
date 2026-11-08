import { useCallback, useEffect, useMemo, useState } from 'react'
import api, { getToken, onUnauthorized, setToken } from '../api/client'
import { AuthContext } from './useAuth'

/**
 * Holds the logged-in user. The token lives in sessionStorage; the user
 * object is (re)loaded from /api/me on start-up and after profile changes.
 */
export default function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState(getToken() ? 'loading' : 'anonymous')
  const [notice, setNotice] = useState(null)

  const clear = useCallback((message = null) => {
    setToken(null)
    setUser(null)
    setStatus('anonymous')
    setNotice(message)
  }, [])

  const refresh = useCallback(async () => {
    const { data } = await api.get('/me')
    setUser(data)
    setStatus('authenticated')
    return data
  }, [])

  useEffect(() => {
    onUnauthorized((err) => clear(err.message))
    return () => onUnauthorized(null)
  }, [clear])

  // Restore the session after a page reload (token still in sessionStorage).
  useEffect(() => {
    if (!getToken()) return
    api
      .get('/me')
      .then(({ data }) => {
        setUser(data)
        setStatus('authenticated')
      })
      .catch(() => {
        setToken(null)
        setUser(null)
        setStatus('anonymous')
      })
  }, [])

  const startSession = useCallback((data) => {
    setToken(data.access_token)
    setUser(data.user)
    setStatus('authenticated')
    setNotice(null)
    return data.user
  }, [])

  const login = useCallback(
    async (email, password) => startSession((await api.post('/auth/login', { email, password })).data),
    [startSession],
  )

  const register = useCallback(
    async (payload) => startSession((await api.post('/auth/register', payload)).data),
    [startSession],
  )

  const logout = useCallback(async () => {
    try {
      await api.post('/auth/logout')
    } catch {
      /* token may already be invalid - log out locally anyway */
    }
    clear('You have been logged out.')
  }, [clear])

  const value = useMemo(
    () => ({ user, status, notice, login, register, logout, refresh, setUser }),
    [user, status, notice, login, register, logout, refresh],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
