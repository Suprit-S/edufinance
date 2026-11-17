import { THEMES, useTheme } from '../lib/useTheme'

const LABELS = { system: 'Auto', light: 'Light', dark: 'Dark' }

/** Three-way switch: follow the OS, or force light/dark. */
export default function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  return (
    <div className="theme-toggle" role="group" aria-label="Colour theme">
      {THEMES.map((value) => (
        <button
          key={value}
          type="button"
          aria-pressed={theme === value}
          onClick={() => setTheme(value)}
        >
          {LABELS[value]}
        </button>
      ))}
    </div>
  )
}
