import { createContext, useContext } from 'react'

export const AuthContext = createContext(null)

/** Access the current user and auth actions. */
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
