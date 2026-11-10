import { Link } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import ComingSoon from '../components/ComingSoon'
import PageHeader from '../components/PageHeader'
import RunwayBadge from '../components/RunwayBadge'
import { formatDate, formatMoney } from '../lib/format'
import { useFinanceData } from '../lib/useFinanceData'

/**
 * Sprint 1 dashboard: greeting, current life phase and wallet balances.
 * The full dashboard (target, runway, loans, charts) arrives in Sprint 3.
 */
export default function DashboardPage() {
  const { user } = useAuth()
  const { wallets, loading } = useFinanceData()
  const current = user.phases.find((p) => p.is_current)
  const active = wallets.filter((w) => !w.is_archived)
  const firstName = user.full_name.split(' ')[0]
  const alerts = active.filter((w) => w.runway && ['WARNING', 'CRITICAL'].includes(w.runway.status))

  return (
    <>
      <PageHeader
        eyebrow="Overview"
        title={`Hello, ${firstName}`}
        lead="From your first university application to your last loan EMI: one place for every cost of your journey."
        actions={
          <Link className="btn btn-primary" to="/transactions">
            Add or find transactions
          </Link>
        }
      />

      {alerts.length > 0 && (
        <section className="alert alert-warning" role="alert" aria-label="Low funds">
          <strong>Low funds:</strong>
          <ul className="alert-list">
            {alerts.map((w) => (
              <li key={w.id}>
                <Link to={`/wallets/${w.id}`}>{w.name}</Link>
                <RunwayBadge runway={w.runway} />
              </li>
            ))}
          </ul>
        </section>
      )}

      <div className="grid grid-2">
        <section className="card">
          <p className="stat-label">Current life phase</p>
          <p className="stat-value phase-title">{current ? current.name : '–'}</p>
          {current && (
            <>
              <p className="stat-sub">
                {formatDate(current.start_date)} –{' '}
                {current.end_date ? formatDate(current.end_date) : 'open-ended'}
              </p>
              {current.progress_pct !== null && (
                <div
                  className="progress"
                  role="progressbar"
                  aria-label="Phase progress"
                  aria-valuenow={current.progress_pct}
                  aria-valuemin={0}
                  aria-valuemax={100}
                >
                  <span style={{ width: `${current.progress_pct}%` }} />
                </div>
              )}
              {current.progress_pct !== null && (
                <p className="stat-sub">{current.progress_pct}% of this phase completed</p>
              )}
            </>
          )}
          <p className="stat-sub">
            <Link to="/profile">See all phases</Link>
          </p>
        </section>

        <section className="card">
          <p className="stat-label">Wallets</p>
          {loading ? (
            <p className="status-line">Loading…</p>
          ) : active.length === 0 ? (
            <p className="stat-sub">
              No wallets yet. <Link to="/wallets">Add your first wallet</Link>.
            </p>
          ) : (
            <ul className="mini-list">
              {active.map((w) => (
                <li key={w.id}>
                  <Link to={`/wallets/${w.id}`}>{w.name}</Link>
                  <span className="money">{formatMoney(w.balance, w.currency_code)}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <ComingSoon
        sprint={3}
        features={[
          `Total balance across all wallets in ${user.base_currency}`,
          'Earned this month vs. minimum target',
          'Loan summary and 30-day spending chart',
        ]}
      />
    </>
  )
}
