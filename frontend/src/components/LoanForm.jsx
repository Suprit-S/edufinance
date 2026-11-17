import { useEffect, useState } from 'react'
import api, { fieldErrors } from '../api/client'
import { loadMasterData } from '../lib/masterData'
import CurrencySelect from './CurrencySelect'
import ErrorBanner from './ErrorBanner'
import Field from './Field'

const FIELDS = [
  'name', 'lender', 'currency_code', 'annual_rate_pct', 'sanctioned_amount', 'outstanding_amount',
  'emi_amount', 'emi_start_date', 'min_part_payment', 'default_wallet_id', 'note',
]

/** Create or edit a loan (FR-28, FR-29). */
export default function LoanForm({ loan, wallets, defaultCurrency, onSaved, onCancel }) {
  const [currencies, setCurrencies] = useState([])
  const [form, setForm] = useState(() =>
    Object.fromEntries(FIELDS.map((k) => [k, loan?.[k] ?? (k === 'currency_code' ? defaultCurrency : '')])),
  )
  const [errors, setErrors] = useState({})
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    loadMasterData().then((m) => setCurrencies(m.currencies)).catch(() => {})
  }, [])

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))
  const sameCcy = wallets.filter((w) => w.currency_code === form.currency_code && !w.is_archived)

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setErrors({})
    setError(null)
    const payload = Object.fromEntries(FIELDS.map((k) => [k, form[k] === '' ? null : form[k]]))
    if (!loan && payload.outstanding_amount === null) payload.outstanding_amount = payload.sanctioned_amount
    try {
      const res = loan ? await api.patch(`/loans/${loan.id}`, payload) : await api.post('/loans', payload)
      onSaved(res.data)
    } catch (err) {
      setError(err)
      setErrors(fieldErrors(err))
    } finally {
      setBusy(false)
    }
  }

  const money = (key, label, hint) => (
    <Field id={`l-${key}`} label={label} error={errors[key]} hint={hint}>
      {(a) => <input {...a} className="input input-money" inputMode="decimal" value={form[key] ?? ''} onChange={set(key)} />}
    </Field>
  )

  return (
    <form className="form" onSubmit={submit} noValidate>
      <ErrorBanner error={error} />
      <div className="form-grid">
        <Field id="l-name" label="Name" error={errors.name}>
          {(a) => <input {...a} className="input" placeholder="e.g. Education loan" value={form.name} onChange={set('name')} />}
        </Field>
        <Field id="l-lender" label="Lender (optional)" error={errors.lender}>
          {(a) => <input {...a} className="input" placeholder="e.g. SBI" value={form.lender ?? ''} onChange={set('lender')} />}
        </Field>
      </div>
      <div className="form-grid form-grid-3">
        <Field id="l-currency" label="Currency" error={errors.currency_code}>
          {(a) => (
            <CurrencySelect {...a} currencies={currencies} value={form.currency_code}
              onChange={(v) => setForm((f) => ({ ...f, currency_code: v, default_wallet_id: '' }))} />
          )}
        </Field>
        <Field id="l-rate" label="Interest % per year" error={errors.annual_rate_pct}>
          {(a) => <input {...a} className="input input-money" inputMode="decimal" value={form.annual_rate_pct} onChange={set('annual_rate_pct')} />}
        </Field>
        {money('emi_amount', 'EMI per month')}
      </div>
      <div className="form-grid">
        {money('sanctioned_amount', 'Sanctioned amount')}
        {money('outstanding_amount', 'Outstanding now', loan ? 'Correct it any time to match your bank statement.' : 'Leave empty if nothing is repaid yet.')}
      </div>
      <div className="form-grid">
        <Field id="l-emi-start" label="First EMI (optional)" error={errors.emi_start_date} hint="e.g. after the moratorium">
          {(a) => <input {...a} className="input" type="date" value={form.emi_start_date ?? ''} onChange={set('emi_start_date')} />}
        </Field>
        {money('min_part_payment', 'Minimum part-payment (optional)', 'Used for the “can I afford it?” check')}
      </div>
      <Field id="l-wallet" label="Pay from wallet (optional)" error={errors.default_wallet_id}
        hint={sameCcy.length ? 'Payments are booked as expenses in this wallet.' : `No ${form.currency_code} wallet yet — payments are recorded without a wallet.`}>
        {(a) => (
          <select {...a} className="input" value={form.default_wallet_id ?? ''} onChange={set('default_wallet_id')}>
            <option value="">No wallet</option>
            {sameCcy.map((w) => (
              <option key={w.id} value={w.id}>{w.name}</option>
            ))}
          </select>
        )}
      </Field>
      <div className="form-actions">
        <button type="button" className="btn btn-secondary" onClick={onCancel}>Cancel</button>
        <button className="btn btn-primary" disabled={busy}>{busy ? 'Saving…' : loan ? 'Save loan' : 'Add loan'}</button>
      </div>
    </form>
  )
}
