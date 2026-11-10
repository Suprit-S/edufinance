import { useEffect, useMemo, useState } from 'react'
import api, { fieldErrors } from '../api/client'
import { useAuth } from '../auth/useAuth'
import ConfirmDialog from '../components/ConfirmDialog'
import CurrencySelect from '../components/CurrencySelect'
import ErrorBanner from '../components/ErrorBanner'
import Field from '../components/Field'
import Modal from '../components/Modal'
import PageHeader from '../components/PageHeader'
import { todayIso } from '../lib/dates'
import { formatDate, formatMoney } from '../lib/format'
import { loadMasterData } from '../lib/masterData'
import { useFinanceData } from '../lib/useFinanceData'

const DIRECTIONS = [
  ['OWN', 'Between my wallets'],
  ['IN', 'Received from outside'],
  ['OUT', 'Sent to someone'],
]

/** Remittances: the real rate of every transfer and what it cost (US-07). */
export default function RemittancesPage() {
  const { user } = useAuth()
  const { wallets, categories, reload: reloadWallets } = useFinanceData()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [dialog, setDialog] = useState(null)
  const [version, setVersion] = useState(0)

  useEffect(() => {
    api.get('/remittances').then(({ data }) => setData(data), setError)
  }, [version])

  const refresh = () => {
    setVersion((v) => v + 1)
    reloadWallets()
  }
  const walletName = Object.fromEntries(wallets.map((w) => [w.id, w.name]))
  const close = () => setDialog(null)

  return (
    <>
      <PageHeader
        eyebrow="Remittances"
        title="Money sent and received"
        lead="Enter what left one account and what arrived in the other. EduFinance works out the rate you really got — and what the transfer cost you compared with the market rate."
        actions={
          <button className="btn btn-primary" onClick={() => setDialog({ type: 'add' })}>
            Record transfer
          </button>
        }
      />
      <ErrorBanner error={error} />

      {data && (
        <div className="grid grid-3">
          <div className="card">
            <p className="stat-label">Transfers recorded</p>
            <p className="stat-value">{data.summary.count}</p>
          </div>
          <div className="card">
            <p className="stat-label">Hidden cost in {data.summary.year}</p>
            <p className="stat-value">
              <CostText value={data.summary.hidden_cost_year} currency={user.base_currency} />
            </p>
            <p className="stat-sub">Your rates compared with the market rate, fees included</p>
          </div>
          <div className="card">
            <p className="stat-label">Hidden cost, all time</p>
            <p className="stat-value">
              <CostText value={data.summary.hidden_cost_total} currency={user.base_currency} />
            </p>
          </div>
        </div>
      )}

      <section className="card">
        <h2>Transfers</h2>
        {!data ? (
          <p className="status-line">Loading…</p>
        ) : data.items.length === 0 ? (
          <p className="empty-inline">
            No transfers yet. Record money from home, a transfer to your savings or money you sent to family.
          </p>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">Date</th>
                  <th scope="col">From → To</th>
                  <th scope="col" className="num">Sent</th>
                  <th scope="col" className="num">Received</th>
                  <th scope="col" className="num">Hidden cost</th>
                  <th scope="col"><span className="visually-hidden">Actions</span></th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((r) => (
                  <tr key={r.id}>
                    <td>{formatDate(r.remit_date)}</td>
                    <td>
                      <span className="txn-category">
                        {walletName[r.from_wallet_id] ?? 'Outside'} → {walletName[r.to_wallet_id] ?? 'Outside'}
                      </span>
                      {(r.provider || r.note) && (
                        <span className="txn-note">{[r.provider, r.note].filter(Boolean).join(' · ')}</span>
                      )}
                    </td>
                    <td className="num money">{formatMoney(r.sent_amount, r.sent_currency)}</td>
                    <td className="num">
                      <span className="money">{formatMoney(r.received_amount, r.received_currency)}</span>
                      {r.sent_currency !== r.received_currency && (
                        <span className="sub-money">
                          {rateText(r.effective_rate, r.sent_currency, r.received_currency)}
                          {r.market_rate && ` · market ${rateText(r.market_rate, r.sent_currency, r.received_currency, true)}`}
                        </span>
                      )}
                    </td>
                    <td className="num">
                      <CostText value={r.hidden_cost_base} currency={user.base_currency} />
                    </td>
                    <td className="row-actions">
                      <button className="link-btn danger" onClick={() => setDialog({ type: 'delete', item: r })}>
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {dialog?.type === 'add' && (
        <Modal title="Record transfer" onClose={close}>
          <RemittanceForm
            wallets={wallets.filter((w) => !w.is_archived)}
            categories={categories}
            user={user}
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
          title="Delete transfer?"
          message="The transfer and the entries it created in your wallets will be removed."
          onConfirm={() => api.delete(`/remittances/${dialog.item.id}`).then(refresh)}
          onClose={close}
        />
      )}
    </>
  )
}

/** Hidden cost; a negative value means the user got a better rate than the market. */
function CostText({ value, currency }) {
  if (value === null || value === undefined) return '–'
  const n = Number(value)
  if (n < 0) {
    return (
      <span className="money pos" title="Your rate was better than the market rate">
        {formatMoney(Math.abs(n).toFixed(2), currency)} better
      </span>
    )
  }
  return <span className="money">{formatMoney(value, currency)}</span>
}

/** Show a rate the readable way round: "1 EUR = 96.15 INR" rather than 0.0104. */
function rateText(value, from, to, short = false) {
  const r = Number(value)
  if (r >= 1) return short ? r.toFixed(2) : `1 ${from} = ${r.toFixed(2)} ${to}`
  return short ? (1 / r).toFixed(2) : `1 ${to} = ${(1 / r).toFixed(2)} ${from}`
}

export function RemittanceForm({ wallets, categories, user, onSaved, onCancel }) {
  const [direction, setDirection] = useState('OWN')
  const [currencies, setCurrencies] = useState([])
  const [form, setForm] = useState({
    from_wallet_id: wallets.find((w) => w.currency_code === user.home_currency)?.id ?? wallets[0]?.id ?? '',
    to_wallet_id: wallets.find((w) => w.currency_code === user.base_currency)?.id ?? wallets[1]?.id ?? '',
    sent_currency: user.home_currency,
    received_currency: user.home_currency,
    sent_amount: '',
    received_amount: '',
    fee_amount: '',
    provider: '',
    remit_date: todayIso(),
    category_id: '',
    note: '',
  })
  const [errors, setErrors] = useState({})
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    loadMasterData().then((m) => setCurrencies(m.currencies)).catch(() => {})
  }, [])

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))
  const from = wallets.find((w) => w.id === form.from_wallet_id)
  const to = wallets.find((w) => w.id === form.to_wallet_id)
  const sentCcy = direction === 'IN' ? form.sent_currency : from?.currency_code
  const recvCcy = direction === 'OUT' ? form.received_currency : to?.currency_code
  const kind = direction === 'IN' ? 'INCOME' : 'EXPENSE'
  const cats = useMemo(() => categories.filter((c) => c.kind === kind), [categories, kind])

  const rate =
    Number(form.sent_amount) > 0 && Number(form.received_amount) > 0
      ? Number(form.received_amount) / Number(form.sent_amount)
      : null

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setErrors({})
    setError(null)
    const payload = {
      sent_amount: form.sent_amount,
      received_amount: form.received_amount,
      remit_date: form.remit_date,
      provider: form.provider || null,
      note: form.note || null,
      from_wallet_id: direction === 'IN' ? null : form.from_wallet_id,
      to_wallet_id: direction === 'OUT' ? null : form.to_wallet_id,
    }
    if (direction === 'IN') payload.sent_currency = form.sent_currency
    if (direction === 'OUT') payload.received_currency = form.received_currency
    if (direction !== 'IN' && form.fee_amount) payload.fee_amount = form.fee_amount
    if (direction !== 'OWN' && form.category_id) payload.category_id = form.category_id
    try {
      await api.post('/remittances', payload)
      onSaved()
    } catch (err) {
      setError(err)
      setErrors(fieldErrors(err))
    } finally {
      setBusy(false)
    }
  }

  const walletSelect = (key, label) => (
    <Field id={`r-${key}`} label={label} error={errors[key]}>
      {(a) => (
        <select {...a} className="input" value={form[key]} onChange={set(key)}>
          {wallets.map((w) => (
            <option key={w.id} value={w.id}>
              {w.name} · {w.currency_code}
            </option>
          ))}
        </select>
      )}
    </Field>
  )

  return (
    <form className="form" onSubmit={submit} noValidate>
      <ErrorBanner error={error} />
      <div className="segmented segmented-wrap" role="group" aria-label="Direction">
        {DIRECTIONS.map(([value, label]) => (
          <button key={value} type="button" aria-pressed={direction === value} onClick={() => setDirection(value)}>
            {label}
          </button>
        ))}
      </div>

      <div className="form-grid">
        {direction === 'IN' ? (
          <Field id="r-sent_currency" label="Sent in currency" error={errors.sent_currency} hint="e.g. your parents' currency">
            {(a) => (
              <CurrencySelect {...a} currencies={currencies} value={form.sent_currency}
                onChange={(v) => setForm((f) => ({ ...f, sent_currency: v }))} />
            )}
          </Field>
        ) : (
          walletSelect('from_wallet_id', 'From wallet')
        )}
        {direction === 'OUT' ? (
          <Field id="r-received_currency" label="Received in currency" error={errors.received_currency}>
            {(a) => (
              <CurrencySelect {...a} currencies={currencies} value={form.received_currency}
                onChange={(v) => setForm((f) => ({ ...f, received_currency: v }))} />
            )}
          </Field>
        ) : (
          walletSelect('to_wallet_id', 'To wallet')
        )}
      </div>

      <div className="form-grid">
        <Field id="r-sent" label={`Amount sent${sentCcy ? ` (${sentCcy})` : ''}`} error={errors.sent_amount}>
          {(a) => <input {...a} className="input input-money" inputMode="decimal" value={form.sent_amount} onChange={set('sent_amount')} />}
        </Field>
        <Field id="r-received" label={`Amount received${recvCcy ? ` (${recvCcy})` : ''}`} error={errors.received_amount}>
          {(a) => <input {...a} className="input input-money" inputMode="decimal" value={form.received_amount} onChange={set('received_amount')} />}
        </Field>
      </div>
      {rate !== null && sentCcy !== recvCcy && (
        <p className="preview" aria-live="polite">
          Your rate: 1 {sentCcy} = <span className="money">{rate.toPrecision(5)}</span> {recvCcy}
          {rate < 1 && (
            <>
              {' '}(1 {recvCcy} = <span className="money">{(1 / rate).toFixed(2)}</span> {sentCcy})
            </>
          )}
        </p>
      )}

      <div className="form-grid">
        <Field id="r-date" label="Date" error={errors.remit_date}>
          {(a) => <input {...a} className="input" type="date" value={form.remit_date} onChange={set('remit_date')} />}
        </Field>
        <Field id="r-provider" label="Provider (optional)" hint="e.g. Wise, bank, Western Union" error={errors.provider}>
          {(a) => <input {...a} className="input" value={form.provider} onChange={set('provider')} />}
        </Field>
      </div>
      <div className="form-grid">
        {direction !== 'IN' && (
          <Field id="r-fee" label={`Fee (optional${sentCcy ? `, ${sentCcy}` : ''})`} error={errors.fee_amount}>
            {(a) => <input {...a} className="input input-money" inputMode="decimal" value={form.fee_amount} onChange={set('fee_amount')} />}
          </Field>
        )}
        {direction !== 'OWN' && (
          <Field id="r-category" label="Category" error={errors.category_id}
            hint={direction === 'IN' ? 'Default: Family support' : 'Default: Gifts & family'}>
            {(a) => (
              <select {...a} className="input" value={form.category_id} onChange={set('category_id')}>
                <option value="">Default</option>
                {cats.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            )}
          </Field>
        )}
      </div>
      <Field id="r-note" label="Note (optional)" error={errors.note}>
        {(a) => <input {...a} className="input" maxLength={255} value={form.note} onChange={set('note')} />}
      </Field>
      <div className="form-actions">
        <button type="button" className="btn btn-secondary" onClick={onCancel}>Cancel</button>
        <button className="btn btn-primary" disabled={busy}>{busy ? 'Saving…' : 'Record transfer'}</button>
      </div>
    </form>
  )
}
