import { NavLink } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import { NAV_ITEMS } from './navItems'
import ThemeToggle from './ThemeToggle'

/** Left navigation. On small screens it slides in as a drawer (`open`). */
export default function Sidebar({ open = false, onNavigate }) {
  const { user, logout } = useAuth()
  return (
    <aside className={`sidebar${open ? ' open' : ''}`} aria-label="Main navigation">
      <NavLink to="/" className="brand" onClick={onNavigate}>
        Edu <span>Finance</span>
      </NavLink>
      <nav className="nav">
        {NAV_ITEMS.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.to === '/'} onClick={onNavigate}>
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-footer">
        {user && (
          <div className="sidebar-user">
            <span className="sidebar-name">{user.full_name}</span>
            <span className="sidebar-ccy">
              {user.home_currency} → {user.base_currency}
            </span>
          </div>
        )}
        <ThemeToggle />
        <button type="button" className="btn btn-ghost btn-small" onClick={logout}>
          Log out
        </button>
      </div>
    </aside>
  )
}
