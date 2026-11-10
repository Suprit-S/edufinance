import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import ErrorBanner from '../components/ErrorBanner'
import Modal from '../components/Modal'
import PageHeader from '../components/PageHeader'
import RunwayBadge from '../components/RunwayBadge'
import WalletForm from '../components/WalletForm'
import { humanize } from '../lib/dates'
import { formatMoney } from '../lib/format'
import { useFinanceData } from '../lib/useFinanceData'

/** Wallet overview (US-04). */
export default function WalletsPage() {
  const { user } = useAuth()
  const location = useLocation()
  const { wallets, loading, error, reload } = useFinanceData()
  const [creating, setCreating] = useState(false)
  const active = wallets.filter((w) => !w.is_archived)
  const archived = wallets.filter((w) => w.is_archived)

  return (
    <>
      <PageHeader
        eyebrow="Wallets"
        title="Your wallets"
        lead="One wallet per account or pot of money — home account, daily spending, savings, blocked account."
        actions={
          <button className="btn btn-primary" onClick={() => setCreating(true)}>
            Add wallet
          </button>
        }
      />
      {location.state?.welcome && wallets.length === 0 && (
        <div className="alert alert-info" role="status">
          Welcome, {user.full_name.split(' ')[0]}! Start by adding the accounts you already have — for
          example your home bank account in {user.home_currency} and a spending account in{' '}
          {user.base_currency}.
        </div>
      )}
      <ErrorBanner error={error} />
      {loading ? (
        <p className="status-line">Loading wallets…</p>
      ) : active.length === 0 ? (
        <section className="card empty">
          <h2>No wallets yet</h2>
          <p>Every income and expense is booked into a wallet.</p>
          <p style={{ marginTop: 16 }}>
            <button className="btn btn-primary" onClick={() => setCreating(true)}>
              Add your first wallet
            </button>
          </p>
        </section>
      ) : (
        <div className="grid grid-3">
          {active.map((w) => (
            <WalletCard key={w.id} wallet={w} />
          ))}
        </div>
      )}
      {archived.length > 0 && (
        <details className="archived">
          <summary>Archived wallets ({archived.length})</summary>
          <div className="grid grid-3">
            {archived.map((w) => (
              <WalletCard key={w.id} wallet={w} />
            ))}
          </div>
        </details>
      )}
      {creating && (
        <Modal title="Add wallet" onClose={() => setCreating(false)}>
          <WalletForm
            defaultCurrency={user.base_currency}
            onCancel={() => setCreating(false)}
            onSaved={() => {
              setCreating(false)
              reload()
            }}
          />
        </Modal>
      )}
    </>
  )
}

function WalletCard({ wallet }) {
  const negative = Number(wallet.balance) < 0
  return (
    <Link to={`/wallets/${wallet.id}`} className="card wallet-card">
      <div className="wallet-card-top">
        <span className="badge badge-neutral">{humanize(wallet.wallet_type)}</span>
        <span className="mono wallet-ccy">{wallet.currency_code}</span>
      </div>
      <h3>{wallet.name}</h3>
      <p className={`stat-value ${negative ? 'neg' : ''}`}>{formatMoney(wallet.balance, wallet.currency_code)}</p>
      <p className="stat-sub">Current balance</p>
      {wallet.runway && (
        <p>
          <RunwayBadge runway={wallet.runway} />
        </p>
      )}
    </Link>
  )
}
