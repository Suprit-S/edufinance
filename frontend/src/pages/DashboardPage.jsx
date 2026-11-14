import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import { useAuth } from '../auth/useAuth'
import BarList from '../components/BarList'
import ErrorBanner from '../components/ErrorBanner'
import PageHeader from '../components/PageHeader'
import RunwayBadge from '../components/RunwayBadge'
import { formatDate, formatMoney } from '../lib/format'
import { monthLabel } from '../lib/months'

/** Dashboard: balance, this month's target, alerts, loans, phase, spending (US-14). */
export default function DashboardPage() {
  const { user } = useAuth()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.get('/dashboard').then(({ data }) => setData(data), setError)
  }, [])

  const firstName = user.full_name.split(' ')[0]
  const phase = user.phases.find((p) => p.id === data?.current_phase_id) ?? user.phases.find((p) => p.is_current)
  const ccy = user.base_currency

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
      <ErrorBanner error={error} />
      {!data ? (
        <p className="status-line">Loading your overview…</p>
      ) : (
        <>
          {data.alerts.length > 0 && (
            <section className="alert alert-warning" role="alert" aria-label="Low funds">
              <strong>Low funds:</strong>
              <ul className="alert-list">
                {data.alerts.map((w) => (
                  <li key={w.id}>
                    <Link to={`/wallets/${w.id}`}>{w.name}</Link>
                    <RunwayBadge runway={w.runway} />
                  </li>
                ))}
              </ul>
            </section>
          )}

          <div className="grid grid-3">
            <section className="card">
              <p className="stat-label">Total balance</p>
              <p className="stat-value">{formatMoney(data.total_balance, ccy)}</p>
              <p className="stat-sub">
                {data.wallets.length} wallets in {ccy} at today’s rates
                {data.estimated_rates ? ' (estimated)' : ''}
              </p>
            </section>
            <section className="card">
              <p className="stat-label">{monthLabel(data.this_month.month)}: earned vs. target</p>
              <p className="stat-value">
                {formatMoney(data.this_month.earned, ccy)}
                <span className="stat-of"> / {formatMoney(data.this_month.target, ccy)}</span>
              </p>
              {data.this_month.progress_pct !== null && (
                <div
                  className="progress"
                  role="progressbar"
                  aria-label="Share of this month's target earned"
                  aria-valuenow={Math.min(100, data.this_month.progress_pct)}
                  aria-valuemin={0}
                  aria-valuemax={100}
                >
                  <span style={{ width: `${Math.min(100, data.this_month.progress_pct)}%` }} />
                </div>
              )}
              <p className="stat-sub">
                {Number(data.this_month.still_to_earn) > 0
                  ? `${formatMoney(data.this_month.still_to_earn, ccy)} still to earn · `
                  : 'Target reached · '}
                <Link to="/target">Details</Link>
              </p>
            </section>
            <section className="card">
              <p className="stat-label">Loans</p>
              {data.loans.active === 0 ? (
                <p className="stat-sub">
                  No active loans. <Link to="/loans">Add one</Link>
                </p>
              ) : (
                <>
                  <p className="stat-value">{formatMoney(data.loans.outstanding, ccy)}</p>
                  <p className="stat-sub">
                    {data.loans.active} active · EMIs this month {formatMoney(data.loans.emi_this_month, ccy)}
                  </p>
                  <p className="stat-sub">
                    {data.loans.debt_free_month
                      ? `Debt-free in ${monthLabel(data.loans.debt_free_month)}`
                      : 'Check your EMIs'}{' '}
                    · <Link to="/loans">Loan Planner</Link>
                  </p>
                </>
              )}
            </section>
          </div>

          <div className="grid grid-2">
            <section className="card">
              <h2>Spending, last 30 days</h2>
              <p className="stat-sub">{formatMoney(data.spending_30d.total, ccy)} in total</p>
              <BarList items={data.spending_30d.categories} currency={ccy} label="Spending by category, last 30 days" />
            </section>
            <div className="stack">
              <section className="card">
                <p className="stat-label">Current life phase</p>
                <p className="stat-value phase-title">{phase ? phase.name : '–'}</p>
                {phase && (
                  <>
                    <p className="stat-sub">
                      {formatDate(phase.start_date)} – {phase.end_date ? formatDate(phase.end_date) : 'open-ended'}
                    </p>
                    {phase.progress_pct !== null && (
                      <>
                        <div
                          className="progress"
                          role="progressbar"
                          aria-label="Phase progress"
                          aria-valuenow={phase.progress_pct}
                          aria-valuemin={0}
                          aria-valuemax={100}
                        >
                          <span style={{ width: `${phase.progress_pct}%` }} />
                        </div>
                        <p className="stat-sub">{phase.progress_pct}% of this phase completed</p>
                      </>
                    )}
                  </>
                )}
              </section>
              <section className="card">
                <h2>Wallets</h2>
                {data.wallets.length === 0 ? (
                  <p className="stat-sub">
                    No wallets yet. <Link to="/wallets">Add your first wallet</Link>.
                  </p>
                ) : (
                  <ul className="mini-list">
                    {data.wallets.map((w) => (
                      <li key={w.id}>
                        <Link to={`/wallets/${w.id}`}>{w.name}</Link>
                        <span className="money">{formatMoney(w.balance, w.currency_code)}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            </div>
          </div>
        </>
      )}
    </>
  )
}
