import { useEffect, useMemo, useState } from 'react'
import api, { fieldErrors } from '../api/client'
import { todayIso } from '../lib/dates'
import { formatMoney } from '../lib/format'
import ErrorBanner from './ErrorBanner'
import Field from './Field'

/**
 * Create or edit an income/expense (FR-13 to FR-16).
 *
 * For a wallet in a foreign currency the market rate to the base currency is
 * pre-filled; the user may overwrite it. The rate is only sent to the API when
 * the user changed it, otherwise the server freezes the market rate itself.
 */
export default function TransactionForm({
  wallets,
  categories,
  phases,
  baseCurrency,
  initial = null,
  defaultWalletId = '',
  onSaved,
  onCancel,
}) {
  const editing = Boolean(initial)
  const activeWallets = wallets.filter((w) => !w.is_archived || w.id === initial?.wallet_id)
  const [form, setForm] = useState(() => ({
    kind: initial?.kind ?? 'EXPENSE',
    amount: initial?.amount ?? '',
    wallet_id: initial?.wallet_id ?? (defaultWalletId || activeWallets[0]?.id || ''),
    category_id: initial?.category_id ?? '',
    txn_date: initial?.txn_date ?? todayIso(),
    note: initial?.note ?? '',
    phase_id: initial?.phase_is_manual ? initial.phase_id : '',
    rate_to_base: initial?.rate_to_base ?? '',
  }))
  const [rateInfo, setRateInfo] = useState(null)
  const [rateTouched, setRateTouched] = useState(false)
  const [errors, setErrors] = useState({})
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const wallet = wallets.find((w) => w.id === form.wallet_id)
  const foreign = wallet && wallet.currency_code !== baseCurrency
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  // Categories of the chosen kind, grouped for <optgroup>.
  const groups = useMemo(() => {
    const map = new Map()
    for (const c of categories.filter((c) => c.kind === form.kind)) {
      if (!map.has(c.group_name)) map.set(c.group_name, [])
      map.get(c.group_name).push(c)
    }
    return [...map.entries()]
  }, [categories, form.kind])

  // Pre-fill the market rate for new foreign-currency entries.
  useEffect(() => {
    if (!foreign || editing || rateTouched) return undefined
    let cancelled = false
    const t = setTimeout(() => {
      api
        .get('/fx/rate', {
          params: { from: wallet.currency_code, to: baseCurrency, date: form.txn_date || undefined },
        })
        .then(({ data }) => {
          if (cancelled) return
          setRateInfo(data)
          setForm((f) => ({ ...f, rate_to_base: data.rate }))
        })
        .catch(() => !cancelled && setRateInfo(null))
    }, 250)
    return () => {
      cancelled = true
      clearTimeout(t)
    }
  }, [foreign, editing, rateTouched, wallet?.currency_code, baseCurrency, form.txn_date])

  const preview =
    foreign && form.amount && form.rate_to_base
      ? Number(form.amount) * Number(form.rate_to_base)
      : null

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setErrors({})
    const payload = {
      category_id: form.category_id,
      amount: form.amount,
      txn_date: form.txn_date,
      note: form.note || null,
      phase_id: form.phase_id || null,
    }
    if (foreign && rateTouched && form.rate_to_base) payload.rate_to_base = form.rate_to_base
    try {
      const res = editing
        ? await api.patch(`/transactions/${initial.id}`, payload)
        : await api.post('/transactions', { ...payload, kind: form.kind, wallet_id: form.wallet_id })
      onSaved(res.data)
    } catch (err) {
      setError(err)
      setErrors(fieldErrors(err))
    } finally {
      setBusy(false)
    }
  }

  if (!editing && activeWallets.length === 0) {
    return <p className="hint">Create a wallet first — every transaction belongs to one.</p>
  }

  return (
    <form className="form" onSubmit={submit} noValidate>
      <ErrorBanner error={error} />
      {!editing && (
        <div className="segmented" role="group" aria-label="Type">
          {['EXPENSE', 'INCOME'].map((k) => (
            <button
              key={k}
              type="button"
              aria-pressed={form.kind === k}
              onClick={() => setForm((f) => ({ ...f, kind: k, category_id: '' }))}
            >
              {k === 'EXPENSE' ? 'Expense' : 'Income'}
            </button>
          ))}
        </div>
      )}

      <div className="form-grid">
        <Field id="amount" label={`Amount${wallet ? ` (${wallet.currency_code})` : ''}`} error={errors.amount}>
          {(a) => (
            <input
              {...a}
              className="input input-money"
              inputMode="decimal"
              placeholder="0.00"
              value={form.amount}
              onChange={set('amount')}
            />
          )}
        </Field>
        <Field id="wallet_id" label="Wallet" error={errors.wallet_id}>
          {(a) => (
            <select {...a} className="input" value={form.wallet_id} onChange={set('wallet_id')} disabled={editing}>
              {activeWallets.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name} · {w.currency_code}
                </option>
              ))}
            </select>
          )}
        </Field>
      </div>

      <div className="form-grid">
        <Field id="category_id" label="Category" error={errors.category_id}>
          {(a) => (
            <select {...a} className="input" value={form.category_id} onChange={set('category_id')}>
              <option value="">Choose…</option>
              {groups.map(([group, items]) => (
                <optgroup key={group} label={group}>
                  {items.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          )}
        </Field>
        <Field id="txn_date" label="Date" error={errors.txn_date}>
          {(a) => <input {...a} className="input" type="date" value={form.txn_date} onChange={set('txn_date')} />}
        </Field>
      </div>

      <Field id="note" label="Note (optional)" error={errors.note}>
        {(a) => (
          <input {...a} className="input" maxLength={255} placeholder="e.g. Lidl, IELTS Mumbai" value={form.note} onChange={set('note')} />
        )}
      </Field>

      {foreign && (
        <Field
          id="rate_to_base"
          label={`Exchange rate: 1 ${wallet.currency_code} = ? ${baseCurrency}`}
          error={errors.rate_to_base}
          hint={
            rateTouched
              ? 'Your rate will be saved with this entry.'
              : rateInfo
                ? `Market rate of ${rateInfo.rate_date}${rateInfo.estimated ? ' (estimated)' : ''}. Change it if you know the real rate.`
                : editing
                  ? 'The rate saved with this entry. Change it only to correct it.'
                  : 'Loading market rate…'
          }
        >
          {(a) => (
            <input
              {...a}
              className="input input-money"
              inputMode="decimal"
              value={form.rate_to_base}
              onChange={(e) => {
                setRateTouched(true)
                setForm((f) => ({ ...f, rate_to_base: e.target.value }))
              }}
            />
          )}
        </Field>
      )}
      {preview !== null && !Number.isNaN(preview) && (
        <p className="preview" aria-live="polite">
          ≈ <span className="money">{formatMoney(preview.toFixed(2), baseCurrency)}</span> in your base currency
        </p>
      )}

      <details className="more-options">
        <summary>Life phase</summary>
        <Field id="phase_id" label="Phase" hint="Automatic uses the date of the entry." error={errors.phase_id}>
          {(a) => (
            <select {...a} className="input" value={form.phase_id} onChange={set('phase_id')}>
              <option value="">Automatic (by date)</option>
              {phases.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          )}
        </Field>
      </details>

      <div className="form-actions">
        <button type="button" className="btn btn-secondary" onClick={onCancel}>
          Cancel
        </button>
        <button className="btn btn-primary" disabled={busy}>
          {busy ? 'Saving…' : editing ? 'Save changes' : form.kind === 'EXPENSE' ? 'Add expense' : 'Add income'}
        </button>
      </div>
    </form>
  )
}
