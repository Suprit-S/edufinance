import { useEffect, useState } from 'react'
import api from '../api/client'
import { useAuth } from '../auth/useAuth'
import ConfirmDialog from '../components/ConfirmDialog'
import ErrorBanner from '../components/ErrorBanner'
import Modal from '../components/Modal'
import PageHeader from '../components/PageHeader'
import TransactionForm from '../components/TransactionForm'
import TransactionList from '../components/TransactionList'
import { formatDate, formatMoney } from '../lib/format'
import { useFinanceData } from '../lib/useFinanceData'

const PAGE = 50
const NO_FILTERS = { wallet_id: '', kind: '', phase_id: '', category_id: '', date_from: '', date_to: '', q: '' }

/** All transactions with filters (FR-13). */
export default function TransactionsPage() {
  const { user } = useAuth()
  const { wallets, categories, reload: reloadData } = useFinanceData()
  const [filters, setFilters] = useState(NO_FILTERS)
  const [limit, setLimit] = useState(PAGE)
  const [result, setResult] = useState({ items: [], total: 0, loading: true })
  const [error, setError] = useState(null)
  const [dialog, setDialog] = useState(null)
  const [version, setVersion] = useState(0)
  const [showFilters, setShowFilters] = useState(false)

  useEffect(() => {
    let cancelled = false
    const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v))
    const t = setTimeout(() => {
      api
        .get('/transactions', { params: { ...params, per_page: limit } })
        .then(({ data }) => !cancelled && setResult({ ...data, loading: false }))
        .catch((err) => !cancelled && setError(err))
    }, 200)
    return () => {
      cancelled = true
      clearTimeout(t)
    }
  }, [filters, limit, version])

  const set = (key) => (e) => {
    setLimit(PAGE)
    setFilters((f) => ({ ...f, [key]: e.target.value }))
  }
  const refresh = () => {
    setVersion((v) => v + 1)
    reloadData()
  }
  const close = () => setDialog(null)
  const active = Object.values(filters).some(Boolean)

  return (
    <>
      <PageHeader
        eyebrow="Transactions"
        title="Every euro and rupee"
        lead="Search and filter all income and expenses across wallets and life phases."
        actions={
          <div className="actions">
            <button className="btn btn-primary" onClick={() => setDialog({ type: 'add' })}>
              Add transaction
            </button>
            <button
              className="btn btn-secondary mobile-only"
              aria-expanded={showFilters}
              aria-controls="txn-filters"
              onClick={() => setShowFilters((v) => !v)}
            >
              {showFilters ? 'Hide filters' : `Filters${active ? ' (on)' : ''}`}
            </button>
          </div>
        }
      />
      <ErrorBanner error={error} />

      <section id="txn-filters" className={`card filters ${showFilters ? 'open' : ''}`} aria-label="Filters">
        <label>
          <span className="label">Search note</span>
          <input className="input" value={filters.q} onChange={set('q')} placeholder="e.g. Lidl" />
        </label>
        <label>
          <span className="label">Wallet</span>
          <select className="input" value={filters.wallet_id} onChange={set('wallet_id')}>
            <option value="">All wallets</option>
            {wallets.map((w) => (
              <option key={w.id} value={w.id}>{w.name}</option>
            ))}
          </select>
        </label>
        <label>
          <span className="label">Type</span>
          <select className="input" value={filters.kind} onChange={set('kind')}>
            <option value="">All</option>
            <option value="EXPENSE">Expenses</option>
            <option value="INCOME">Income</option>
          </select>
        </label>
        <label>
          <span className="label">Category</span>
          <select className="input" value={filters.category_id} onChange={set('category_id')}>
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </label>
        <label>
          <span className="label">Life phase</span>
          <select className="input" value={filters.phase_id} onChange={set('phase_id')}>
            <option value="">All phases</option>
            {user.phases.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </label>
        <label>
          <span className="label">From</span>
          <input className="input" type="date" value={filters.date_from} onChange={set('date_from')} />
        </label>
        <label>
          <span className="label">To</span>
          <input className="input" type="date" value={filters.date_to} onChange={set('date_to')} />
        </label>
        {active && (
          <button className="btn btn-secondary" onClick={() => setFilters(NO_FILTERS)}>
            Clear filters
          </button>
        )}
      </section>

      <section className="card">
        <h2>
          {result.loading
            ? 'Transactions'
            : `${result.total} ${result.total === 1 ? 'transaction' : 'transactions'}`}
        </h2>
        {result.loading ? (
          <p className="status-line">Loading…</p>
        ) : (
          <TransactionList
            items={result.items}
            wallets={wallets}
            baseCurrency={user.base_currency}
            onEdit={(t) => setDialog({ type: 'edit', txn: t })}
            onDelete={(t) => setDialog({ type: 'delete', txn: t })}
          />
        )}
        {result.items.length < result.total && (
          <button className="btn btn-secondary load-more" onClick={() => setLimit((l) => l + PAGE)}>
            Show more ({result.total - result.items.length} left)
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
            initial={dialog.txn}
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
    </>
  )
}
