import { useEffect, useState } from 'react'
import api from '../api/client'
import ComingSoon from '../components/ComingSoon'
import PageHeader from '../components/PageHeader'

/**
 * Skeleton dashboard: shows that frontend, API and database are connected.
 * The real dashboard (balances, target, runway, loans) arrives in Sprint 3.
 */
export default function DashboardPage() {
  const [status, setStatus] = useState({ state: 'loading' })

  useEffect(() => {
    let cancelled = false
    Promise.all([api.get('/health'), api.get('/currencies')])
      .then(([health, currencies]) => {
        if (!cancelled)
          setStatus({ state: 'ok', db: health.data.database, currencies: currencies.data.length })
      })
      .catch((err) => !cancelled && setStatus({ state: 'error', message: err.message }))
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <>
      <PageHeader
        eyebrow="Overview"
        title="Welcome to EduFinance"
        lead="From your first university application to your last loan EMI: one place for every euro and rupee of your study-abroad journey."
      />

      <section className="card" aria-live="polite">
        <h2>System status</h2>
        {status.state === 'loading' && <p className="status-line">Checking connection…</p>}
        {status.state === 'ok' && (
          <p className="status-line">
            <span className="badge badge-healthy">Connected</span>
            API and database are running · {status.currencies} currencies available
          </p>
        )}
        {status.state === 'error' && (
          <p className="status-line">
            <span className="badge badge-critical">Offline</span>
            {status.message}
          </p>
        )}
      </section>

      <ComingSoon
        sprint={3}
        features={[
          'Total balance across all wallets in your base currency',
          'Earned this month vs. minimum target',
          'Low-funds alerts and wallet runway',
          'Loan summary and current life phase',
        ]}
      />
    </>
  )
}
