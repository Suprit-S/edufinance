import ThemeToggle from '../components/ThemeToggle'

/** Split screen for login and registration: story on the left, form on the right. */
export default function AuthLayout({ title, lead, children }) {
  return (
    <div className="auth-page">
      <aside className="auth-aside" aria-label="About EduFinance">
        <p className="brand">
          Edu <span>Finance</span>
        </p>
        <div className="auth-story">
          <p className="auth-quote">
            From the first application fee to the last loan EMI — every euro and rupee in one
            place.
          </p>
          <ol className="auth-journey">
            <li>Pre-departure</li>
            <li>Settling in</li>
            <li>Study</li>
            <li>Work</li>
          </ol>
        </div>
        <ThemeToggle />
      </aside>
      <main className="auth-main">
        <div className="auth-card">
          <h1>{title}</h1>
          {lead && <p className="lead">{lead}</p>}
          {children}
        </div>
      </main>
    </div>
  )
}
