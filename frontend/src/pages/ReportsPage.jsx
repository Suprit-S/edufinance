import { useEffect, useState } from 'react'
import api from '../api/client'
import { useAuth } from '../auth/useAuth'
import BarList from '../components/BarList'
import { EarnedSpentChart, MonthLineChart } from '../components/charts'
import ErrorBanner from '../components/ErrorBanner'
import MonthPicker from '../components/MonthPicker'
import PageHeader from '../components/PageHeader'
import { formatDate, formatMoney } from '../lib/format'
import { currentMonth, monthLabel } from '../lib/months'

const KINDS = [
  ['MONTH', 'Month'],
  ['YEAR', 'Year'],
  ['PHASE', 'Life phase'],
  ['LIFETIME', 'Lifetime'],
]

/** Reports with a period switch: month, year, life phase, lifetime (US-13). */
export default function ReportsPage() {
  const { user } = useAuth()
  const currentPhase = user.phases.find((p) => p.is_current) ?? user.phases[0]
  const [kind, setKind] = useState('MONTH')
  const [month, setMonth] = useState(currentMonth())
  const [year, setYear] = useState(String(new Date().getFullYear()))
  const [phaseId, setPhaseId] = useState(currentPhase?.id ?? '')
  const [report, setReport] = useState(null)
  const [extra, setExtra] = useState(null)
  const [error, setError] = useState(null)

  const value = { MONTH: month, YEAR: year, PHASE: phaseId, LIFETIME: undefined }[kind]

  useEffect(() => {
    let cancelled = false
    api
      .get('/reports', { params: { period: kind, value } })
      .then(({ data }) => !cancelled && setReport(data))
      .catch((err) => !cancelled && setError(err))
    return () => {
      cancelled = true
    }
  }, [kind, value])

  useEffect(() => {
    Promise.all([api.get('/reports/costs'), api.get('/reports/net-worth'), api.get('/reports/loans')])
      .then(([c, n, l]) => setExtra({ costs: c.data, netWorth: n.data, loans: l.data }))
      .catch(setError)
  }, [])

  const ccy = user.base_currency
  const years = []
  for (let y = Number(user.planning_start_date.slice(0, 4)); y <= new Date().getFullYear(); y++) years.push(String(y))

  return (
    <>
      <PageHeader
        eyebrow="Reports"
        title="Your money over time"
        lead="Choose a month, a year, one life phase or your whole journey since you started planning."
      />
      <ErrorBanner error={error} />

      <section className="card period-bar" aria-label="Report period">
        <div className="segmented segmented-wrap" role="group" aria-label="Period type">
          {KINDS.map(([k, label]) => (
            <button key={k} type="button" aria-pressed={kind === k} onClick={() => setKind(k)}>
              {label}
            </button>
          ))}
        </div>
        {kind === 'MONTH' && <MonthPicker value={month} onChange={setMonth} />}
        {kind === 'YEAR' && (
          <select className="input period-select" aria-label="Year" value={year} onChange={(e) => setYear(e.target.value)}>
            {years.map((y) => (
              <option key={y}>{y}</option>
            ))}
          </select>
        )}
        {kind === 'PHASE' && (
          <select className="input period-select" aria-label="Life phase" value={phaseId} onChange={(e) => setPhaseId(e.target.value)}>
            {user.phases.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        )}
      </section>

      {report && (
        <>
          <p className="period-label">
            <strong>{report.period.label}</strong> · {formatDate(report.period.start)} – {formatDate(report.period.end)}
          </p>
          <div className="grid grid-3">
            <div className="card">
              <p className="stat-label">Earned</p>
              <p className="stat-value">{formatMoney(report.earned, ccy)}</p>
              <p className="stat-sub">Salary, family support, scholarships, refunds</p>
            </div>
            <div className="card">
              <p className="stat-label">Spent</p>
              <p className="stat-value">{formatMoney(report.spent, ccy)}</p>
              {Number(report.other_income) > 0 && (
                <p className="stat-sub">Not counted as earned: {formatMoney(report.other_income, ccy)} (e.g. loan money)</p>
              )}
            </div>
            <div className="card">
              <p className="stat-label">Net (earned − spent)</p>
              <p className={`stat-value ${Number(report.net) < 0 ? 'neg' : ''}`}>
                {formatMoney(report.net, ccy, { signed: true })}
              </p>
            </div>
          </div>

          <div className="grid grid-2">
            <section className="card">
              <h2>Where the money went</h2>
              <BarList items={report.top_categories} currency={ccy} label="Spending by category" />
            </section>
            <section className="card">
              <h2>Spending per life phase</h2>
              <BarList items={report.by_phase} currency={ccy} label="Spending by life phase" />
              {report.by_source.length > 0 && (
                <>
                  <h3 className="subhead">Earned by source</h3>
                  <BarList items={report.by_source} currency={ccy} label="Earnings by source" />
                </>
              )}
            </section>
          </div>

          {report.monthly.length > 1 && (
            <section className="card">
              <h2>Month by month</h2>
              <EarnedSpentChart monthly={report.monthly} currency={ccy} />
              <details className="chart-table">
                <summary>Show as table</summary>
                <div className="table-wrap">
                  <table className="table">
                    <thead>
                      <tr>
                        <th scope="col">Month</th>
                        <th scope="col" className="num">Earned</th>
                        <th scope="col" className="num">Spent</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.monthly.map((m) => (
                        <tr key={m.month}>
                          <td>{monthLabel(m.month)}</td>
                          <td className="num money">{formatMoney(m.earned, ccy)}</td>
                          <td className="num money">{formatMoney(m.spent, ccy)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
            </section>
          )}
        </>
      )}

      {extra && (
        <>
          <h2 className="section-title">Your whole journey</h2>
          <div className="grid grid-2">
            <section className="card">
              <p className="stat-label">Total cost of going abroad</p>
              <p className="hero-value">{formatMoney(extra.costs.going_abroad.total, ccy)}</p>
              <p className="stat-sub">Everything spent before departure and while settling in</p>
              <BarList items={extra.costs.going_abroad.by_group} currency={ccy} label="Cost of going abroad by topic" />
            </section>
            <section className="card">
              <p className="stat-label">Cost of my degree {extra.costs.degree.complete ? '' : 'so far'}</p>
              <p className="hero-value">{formatMoney(extra.costs.degree.total_so_far, ccy)}</p>
              <p className="stat-sub">
                All spending from your first application until study end ({formatDate(extra.costs.degree.until)})
              </p>
              <div
                className="progress"
                role="progressbar"
                aria-label="Study progress"
                aria-valuenow={extra.costs.degree.study_progress_pct}
                aria-valuemin={0}
                aria-valuemax={100}
              >
                <span style={{ width: `${extra.costs.degree.study_progress_pct}%` }} />
              </div>
              <p className="stat-sub">{extra.costs.degree.study_progress_pct}% of your study time is over</p>
            </section>
          </div>

          <div className="grid grid-2">
            <section className="card">
              <h2>Net worth</h2>
              <p className="hint">
                All wallets minus all loans, valued at today’s exchange rates — so the line shows your
                saving and spending, not currency swings.
              </p>
              <MonthLineChart points={extra.netWorth.points} valueKey="net_worth" name="Net worth" currency={ccy} zeroLine />
              {extra.netWorth.points.length > 0 && (
                <dl className="kv">
                  <dt>Assets now</dt>
                  <dd>{formatMoney(extra.netWorth.points.at(-1).assets, ccy)}</dd>
                  <dt>Loans now</dt>
                  <dd>{formatMoney(extra.netWorth.points.at(-1).debt, ccy)}</dd>
                  <dt>Net worth now</dt>
                  <dd>{formatMoney(extra.netWorth.points.at(-1).net_worth, ccy, { signed: true })}</dd>
                </dl>
              )}
            </section>
            <section className="card">
              <h2>Loan payoff</h2>
              {extra.loans.points.length === 0 ? (
                <p className="empty-inline">No active loans.</p>
              ) : (
                <>
                  <p className="hint">
                    {extra.loans.debt_free_month
                      ? `Debt-free in ${monthLabel(extra.loans.debt_free_month)} at your current EMIs.`
                      : 'At least one EMI does not cover its interest.'}
                  </p>
                  <MonthLineChart points={extra.loans.points} valueKey="outstanding" name="Outstanding loans" currency={ccy} />
                  <dl className="kv">
                    {extra.loans.loans.map((l) => (
                      <div key={l.loan_id} style={{ display: 'contents' }}>
                        <dt>{l.name}</dt>
                        <dd>{l.payoff_month ? monthLabel(l.payoff_month) : '–'}</dd>
                      </div>
                    ))}
                  </dl>
                </>
              )}
            </section>
          </div>
        </>
      )}
    </>
  )
}
