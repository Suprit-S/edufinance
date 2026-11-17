import { useCallback, useEffect, useState } from 'react'
import api from '../api/client'

/** Wallets (with balances) and categories of the logged-in user. */
export function useFinanceData() {
  const [state, setState] = useState({ wallets: [], categories: [], loading: true, error: null })

  const reload = useCallback(async () => {
    try {
      const [w, c] = await Promise.all([api.get('/wallets'), api.get('/categories')])
      setState({ wallets: w.data, categories: c.data, loading: false, error: null })
    } catch (error) {
      setState((s) => ({ ...s, loading: false, error }))
    }
  }, [])

  useEffect(() => {
    reload()
  }, [reload])

  return { ...state, reload }
}
