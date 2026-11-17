import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../api/client'
import { useAuth } from '../auth/useAuth'
import ErrorBanner from '../components/ErrorBanner'
import LoanForm from '../components/LoanForm'
import Modal from '../components/Modal'
import PageHeader from '../components/PageHeader'
import { formatMoney } from '../lib/format'
import { monthLabel } from '../lib/months'
import { useFinanceData } from '../lib/useFinanceData'

const VERDICT = { AFFORDABLE: ['badge-healthy', 'Part-payment affordable'], SAVE: ['badge-warning', 'Save up for part-payment'], NOT_AFFORDABLE: ['badge-neutral', 'Part-payment not affordable'] }

/** Loan Planner overview (US-10). */
export default function LoansPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const { wallets } = useFinanceData()
  const [loans, setLoans] = useState(null)
  const [error, setError] = useState(null)
  const [adding, setAdding] = useState(false)

  useEffect(() => {
    api.get('/loans').then(({ data }) => setLoans(data), setError)
  }, [])

  return (
    <>
      <PageHeader
        eyebrow="Loan Planner"
        title="Your loans"
        lead="Record every EMI and part-payment: see interest paid, interest saved and when you will be debt-free."
        actions={<button className="btn btn-primary" onClick={() => setAdding(true)}>Add loan</button>}
      />
      <ErrorBanner error={error} />
      {!loans ? (
        <p className="status-line">Loading…</p>
      ) : loans.length === 0 ? (
        <section className="card empty">
          <h2>No loans</h2>
          <p>Add your education loan or an instalment plan. Its EMI is added to your Monthly Plan automatically.</p>
          <p style={{ marginTop: 16 }}>
            <button className="btn btn-primary" onClick={() => setAdding(true)}>Add a loan</button>
          </p>
        </section>
      ) : (
        <div className="grid grid-2">
          {loans.map((l) => (
            <Link key={l.id} to={`/loans/${l.id}`} className="card loan-card">
              <div className="wallet-card-top">
                <span className={`badge ${l.status === 'ACTIVE' ? 'badge-ok' : 'badge-healthy'}`}>
                  {l.status === 'ACTIVE' ? 'Repaying' : 'Paid off'}
                </span>
                <span className="mono wallet-ccy">{l.annual_rate_pct}% p.a.</span>
              </div>
              <h2>{l.name}</h2>
              <p className="stat-value">{formatMoney(l.outstanding_amount, l.currency_code)}</p>
              <p className="stat-sub">
                outstanding of {formatMoney(l.sanctioned_amount, l.currency_code)} · EMI{' '}
                {formatMoney(l.emi_amount, l.currency_code)}
              </p>
              <div className="progress" role="progressbar" aria-label={`${l.name} repaid`} aria-valuenow={l.summary.repaid_pct} aria-valuemin={0} aria-valuemax={100}>
                <span style={{ width: `${l.summary.repaid_pct}%` }} />
              </div>
              <p className="stat-sub">
                {l.summary.repaid_pct}% repaid
                {l.summary.payoff_month && ` · debt-free in ${monthLabel(l.summary.payoff_month)}`}
                {l.status === 'ACTIVE' && !l.summary.emi_covers_interest && ' · EMI does not cover the interest'}
              </p>
              {l.affordability && (
                <span className={`badge ${VERDICT[l.affordability.status][0]}`}>{VERDICT[l.affordability.status][1]}</span>
              )}
            </Link>
          ))}
        </div>
      )}
      {adding && (
        <Modal title="Add loan" onClose={() => setAdding(false)}>
          <LoanForm
            wallets={wallets}
            defaultCurrency={user.home_currency}
            onCancel={() => setAdding(false)}
            onSaved={(loan) => navigate(`/loans/${loan.id}`)}
          />
        </Modal>
      )}
    </>
  )
}
