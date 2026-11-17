import { useEffect, useState } from 'react'
import api, { fieldErrors } from '../api/client'
import { humanize, todayIso } from '../lib/dates'
import { loadMasterData } from '../lib/masterData'
import { WALLET_TYPES } from '../lib/walletTypes'
import CurrencySelect from './CurrencySelect'
import ErrorBanner from './ErrorBanner'
import Field from './Field'

/** Create or edit a wallet (FR-11). */
export default function WalletForm({ initial = null, defaultCurrency, onSaved, onCancel }) {
  const editing = Boolean(initial)
  const [currencies, setCurrencies] = useState([])
  const [form, setForm] = useState({
    name: initial?.name ?? '',
    currency_code: initial?.currency_code ?? defaultCurrency ?? '',
    wallet_type: initial?.wallet_type ?? 'BANK',
    opening_balance: initial?.opening_balance ?? '0.00',
    opening_date: initial?.opening_date ?? todayIso(),
  })
  const [errors, setErrors] = useState({})
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    loadMasterData().then((m) => setCurrencies(m.currencies)).catch(setError)
  }, [])

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setErrors({})
    try {
      const res = editing
        ? await api.patch(`/wallets/${initial.id}`, form)
        : await api.post('/wallets', form)
      onSaved(res.data)
    } catch (err) {
      setError(err)
      setErrors(fieldErrors(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="form" onSubmit={submit} noValidate>
      <ErrorBanner error={error} />
      <Field id="w-name" label="Name" error={errors.name} hint="e.g. Daily Spending, Home Account, Blocked Account">
        {(a) => <input {...a} className="input" value={form.name} onChange={set('name')} />}
      </Field>
      <div className="form-grid">
        <Field id="w-currency" label="Currency" error={errors.currency_code}>
          {(a) => (
            <CurrencySelect
              {...a}
              currencies={currencies}
              value={form.currency_code}
              onChange={(v) => setForm((f) => ({ ...f, currency_code: v }))}
            />
          )}
        </Field>
        <Field id="w-type" label="Type" error={errors.wallet_type}>
          {(a) => (
            <select {...a} className="input" value={form.wallet_type} onChange={set('wallet_type')}>
              {WALLET_TYPES.map((t) => (
                <option key={t} value={t}>
                  {humanize(t)}
                </option>
              ))}
            </select>
          )}
        </Field>
      </div>
      <div className="form-grid">
        <Field id="w-opening" label="Opening balance" error={errors.opening_balance}>
          {(a) => (
            <input {...a} className="input input-money" inputMode="decimal" value={form.opening_balance} onChange={set('opening_balance')} />
          )}
        </Field>
        <Field id="w-date" label="Balance on date" error={errors.opening_date}>
          {(a) => <input {...a} className="input" type="date" value={form.opening_date} onChange={set('opening_date')} />}
        </Field>
      </div>
      <div className="form-actions">
        <button type="button" className="btn btn-secondary" onClick={onCancel}>
          Cancel
        </button>
        <button className="btn btn-primary" disabled={busy}>
          {busy ? 'Saving…' : editing ? 'Save wallet' : 'Create wallet'}
        </button>
      </div>
    </form>
  )
}
