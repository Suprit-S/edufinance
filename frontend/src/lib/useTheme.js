import { useCallback, useEffect, useState } from 'react'

const STORAGE_KEY = 'edufinance.theme'
export const THEMES = ['system', 'light', 'dark']

function readStored() {
  try {
    const value = localStorage.getItem(STORAGE_KEY)
    return THEMES.includes(value) ? value : 'system'
  } catch {
    return 'system'
  }
}

/** Theme preference: 'system' follows the OS; otherwise sets data-theme on <html>. */
export function useTheme() {
  const [theme, setThemeState] = useState(readStored)

  useEffect(() => {
    const root = document.documentElement
    if (theme === 'system') root.removeAttribute('data-theme')
    else root.setAttribute('data-theme', theme)
  }, [theme])

  const setTheme = useCallback((value) => {
    setThemeState(value)
    try {
      localStorage.setItem(STORAGE_KEY, value)
    } catch {
      /* storage unavailable (private mode): preference lasts for this visit */
    }
  }, [])

  return { theme, setTheme }
}
