import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

/** App shell: sidebar on desktop, top bar + drawer on phones (360 px+). */
export default function Layout() {
  const [menuOpen, setMenuOpen] = useState(false)
  const close = () => setMenuOpen(false)

  return (
    <div className="shell">
      <header className="topbar">
        <span className="brand">
          Edu <span>Finance</span>
        </span>
        <button
          type="button"
          className="menu-button"
          aria-expanded={menuOpen}
          aria-controls="main-sidebar"
          onClick={() => setMenuOpen((v) => !v)}
        >
          {menuOpen ? 'Close' : 'Menu'}
        </button>
      </header>
      <div id="main-sidebar">
        <Sidebar open={menuOpen} onNavigate={close} />
      </div>
      <main className="content" onClick={menuOpen ? close : undefined}>
        <div className="content-inner">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
