import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import { TargetHistoryChart } from '../components/charts'
import ErrorBanner from '../components/ErrorBanner'
import MonthPicker from '../components/MonthPicker'
import PageHeader from '../components/PageHeader'
import { formatMoney } from '../lib/format'
import { currentMonth, monthLabel } from '../lib/months'

/** Target to Earn: target vs. earned vs. spent for a month (US-09). */
export default function TargetPage() {
  const [month, setMonth] = useState(currentMonth())
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.get('/target', { params: { month } }).then(({ data }) => setData(data), setError)
  }, [month])

  const ccy = data?.currency
  const reached = data && Number(data.still_to_earn) === 0 && Number(data.target) > 0

  return (
    <>
      <PageHeader
        eyebrow="Target to Earn"
        title={`${monthLabel(month)} target`}
        lead="How much you must earn to cover your Monthly Plan — and how far you are. Loan money and transfers between your wallets do not count as earned."
        actions={<MonthPicker value={month} onChange={setMonth} />}
      />
      <ErrorBanner error={error} />
      {!data ? (
        <p className="status-line">Loading…</p>
      ) : (
        <>
          <section className="card hero">
            <div>
              <p className="stat-label">{reached ? 'Target reached — surplus' : 'Still to earn'}</p>
              <p className={`hero-value ${reached ? 'good' : ''}`}>
                {formatMoney(reached ? data.surplus_over_target : data.still_to_earn, ccy)}
              </p>
              {data.progress_pct !== null && (
                <>
                  <div
                    className="progress"
                    role="progressbar"
                    aria-label="Share of target earned"
                    aria-valuenow={Math.min(100, data.progress_pct)}
                    aria-valuemin={0}
                    aria-valuemax={100}
                  >
                    <span style={{ width: `${Math.min(100, data.progress_pct)}%` }} />
                  </div>
                  <p className="stat-sub">{data.progress_pct}% of the target earned</p>
                </>
              )}
              {Number(data.target) === 0 && (
                <p className="stat-sub">
                  No plan items this month. <Link to="/plan">Set up your Monthly Plan</Link>.
                </p>
              )}
            </div>
            <dl className="kv">
              <dt>Minimum target</dt>
              <dd>{formatMoney(data.target, ccy)}</dd>
              <dt>Earned</dt>
              <dd>{formatMoney(data.earned, ccy)}</dd>
              <dt>Spent</dt>
              <dd>{formatMoney(data.spent, ccy)}</dd>
              <dt>Net (earned − spent)</dt>
              <dd>{formatMoney(data.net, ccy, { signed: true })}</dd>
            </dl>
          </section>
          {data.estimated_rates && (
            <div className="alert alert-warning" role="status">
              Some plan items are in another currency and were converted with an estimated rate.
            </div>
          )}

          <div className="grid grid-2">
            <section className="card">
              <h2>Earned by source</h2>
              {data.by_source.length === 0 ? (
                <p className="empty-inline">No earnings recorded this month.</p>
              ) : (
                <dl className="kv">
                  {data.by_source.map((s) => (
                    <div key={s.source} style={{ display: 'contents' }}>
                      <dt>{s.source}</dt>
                      <dd>{formatMoney(s.amount, ccy)}</dd>
                    </div>
                  ))}
                </dl>
              )}
            </section>
            <section className="card">
              <h2>Last six months</h2>
              <TargetHistoryChart history={data.history} currency={ccy} />
            </section>
          </div>

          <section className="card">
            <h2>Plan vs. actual</h2>
            {data.lines.length === 0 ? (
              <p className="empty-inline">No plan items in this month.</p>
            ) : (
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th scope="col">Item</th>
                      <th scope="col" className="num">Planned</th>
                      <th scope="col" className="num">Actual</th>
                      <th scope="col" className="num">Difference</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.lines.map((l) => (
                      <tr key={l.id}>
                        <td>
                          <span className="txn-category">{l.name}</span>
                          {l.currency_code !== ccy && (
                            <span className="txn-note">{formatMoney(l.planned_original, l.currency_code)}</span>
                          )}
                        </td>
                        <td className="num money">{formatMoney(l.planned, ccy)}</td>
                        <td className="num money">{formatMoney(l.actual, ccy)}</td>
                        <td className="num money">{formatMoney(l.difference, ccy, { signed: true })}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <p className="hint">Actual = expenses in the item’s category this month; for loan EMIs, the payments recorded.</p>
          </section>
        </>
      )}
    </>
  )
}
