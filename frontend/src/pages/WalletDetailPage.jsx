import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import api from '../api/client'
import { useAuth } from '../auth/useAuth'
import ConfirmDialog from '../components/ConfirmDialog'
import ErrorBanner from '../components/ErrorBanner'
import Modal from '../components/Modal'
import PageHeader from '../components/PageHeader'
import RunwayBadge from '../components/RunwayBadge'
import TransactionForm from '../components/TransactionForm'
import TransactionList from '../components/TransactionList'
import WalletForm from '../components/WalletForm'
import { humanize } from '../lib/dates'
import { formatDate, formatMoney } from '../lib/format'
import { useFinanceData } from '../lib/useFinanceData'

const PAGE = 25

/** One wallet: balance, actions and its transactions. */
export default function WalletDetailPage() {
  const { walletId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { wallets, categories, reload: reloadData, error: dataError } = useFinanceData()
  const [txns, setTxns] = useState({ items: [], total: 0 })
  const [limit, setLimit] = useState(PAGE)
  const [error, setError] = useState(null)
  const [dialog, setDialog] = useState(null)

  const wallet = wallets.find((w) => w.id === walletId)

  const loadTxns = useCallback(() => {
    api
      .get('/transactions', { params: { wallet_id: walletId, per_page: limit } })
      .then(({ data }) => setTxns(data))
      .catch(setError)
  }, [walletId, limit])

  useEffect(() => {
    loadTxns()
  }, [loadTxns])

  const refresh = () => {
    loadTxns()
    reloadData()
  }
  const close = () => setDialog(null)

  if (!wallet) {
    return dataError || wallets.length ? (
      <section className="card empty">
        <h2>Wallet not found</h2>
        <Link to="/wallets">Back to wallets</Link>
      </section>
    ) : (
      <p className="status-line">Loading…</p>
    )
  }

  return (
    <>
      <p className="breadcrumb">
        <Link to="/wallets">Wallets</Link> / {wallet.name}
      </p>
      <PageHeader
        eyebrow={`${humanize(wallet.wallet_type)} · ${wallet.currency_code}${wallet.is_archived ? ' · archived' : ''}`}
        title={wallet.name}
        actions={
          <div className="actions">
            {!wallet.is_archived && (
              <button className="btn btn-primary" onClick={() => setDialog({ type: 'add' })}>
                Add transaction
              </button>
            )}
            <button className="btn btn-secondary" onClick={() => setDialog({ type: 'edit-wallet' })}>
              Edit
            </button>
            <button
              className="btn btn-secondary"
              onClick={() =>
                api.patch(`/wallets/${wallet.id}`, { is_archived: !wallet.is_archived }).then(refresh, setError)
              }
            >
              {wallet.is_archived ? 'Restore' : 'Archive'}
            </button>
            {txns.total === 0 && (
              <button className="btn btn-danger" onClick={() => setDialog({ type: 'delete-wallet' })}>
                Delete
              </button>
            )}
          </div>
        }
      />
      <ErrorBanner error={error || dataError} />

      <div className="grid grid-3">
        <div className="card">
          <p className="stat-label">Balance</p>
          <p className="stat-value">{formatMoney(wallet.balance, wallet.currency_code)}</p>
          <p className="stat-sub">
            Opening {formatMoney(wallet.opening_balance, wallet.currency_code)} on {formatDate(wallet.opening_date)}
          </p>
        </div>
        <div className="card">
          <p className="stat-label">Runway</p>
          {wallet.runway ? (
            <>
              <p className="stat-value">{wallet.runway.days === null ? '∞' : `${wallet.runway.days} days`}</p>
              <p className="stat-sub">
                <RunwayBadge runway={wallet.runway} />
              </p>
              <p className="stat-sub">
                Spending {formatMoney(wallet.runway.burn_rate_per_day, wallet.currency_code)} per day (last 30 days)
              </p>
            </>
          ) : (
            <p className="stat-sub">Not calculated for archived wallets.</p>
          )}
        </div>
        <div className="card">
          <p className="stat-label">Transactions</p>
          <p className="stat-value">{txns.total}</p>
        </div>
      </div>

      <section className="card">
        <h2>Transactions</h2>
        <TransactionList
          items={txns.items}
          baseCurrency={user.base_currency}
          showWallet={false}
          onEdit={(t) => setDialog({ type: 'edit', txn: t })}
          onDelete={(t) => setDialog({ type: 'delete', txn: t })}
        />
        {txns.items.length < txns.total && (
          <button className="btn btn-secondary load-more" onClick={() => setLimit((l) => l + PAGE)}>
            Show more ({txns.total - txns.items.length} left)
          </button>
        )}
      </section>

      {(dialog?.type === 'add' || dialog?.type === 'edit') && (
        <Modal title={dialog.type === 'add' ? 'Add transaction' : 'Edit transaction'} onClose={close}>
          <TransactionForm
            wallets={wallets}
            categories={categories}
            phases={user.phases}
            baseCurrency={user.base_currency}
            defaultWalletId={wallet.id}
            initial={dialog.txn}
            onCancel={close}
            onSaved={() => {
              close()
              refresh()
            }}
          />
        </Modal>
      )}
      {dialog?.type === 'edit-wallet' && (
        <Modal title="Edit wallet" onClose={close}>
          <WalletForm
            initial={wallet}
            onCancel={close}
            onSaved={() => {
              close()
              refresh()
            }}
          />
        </Modal>
      )}
      {dialog?.type === 'delete' && (
        <ConfirmDialog
          title="Delete transaction?"
          message={`${dialog.txn.category_name}, ${formatMoney(dialog.txn.amount, dialog.txn.currency_code)} on ${formatDate(dialog.txn.txn_date)} will be removed.`}
          onConfirm={() => api.delete(`/transactions/${dialog.txn.id}`).then(refresh)}
          onClose={close}
        />
      )}
      {dialog?.type === 'delete-wallet' && (
        <ConfirmDialog
          title="Delete wallet?"
          message={`"${wallet.name}" has no transactions and will be removed.`}
          onConfirm={() => api.delete(`/wallets/${wallet.id}`).then(() => navigate('/wallets'))}
          onClose={close}
        />
      )}
    </>
  )
}
