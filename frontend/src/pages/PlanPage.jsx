import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { fieldErrors } from '../api/client'
import { useAuth } from '../auth/useAuth'
import ConfirmDialog from '../components/ConfirmDialog'
import CurrencySelect from '../components/CurrencySelect'
import ErrorBanner from '../components/ErrorBanner'
import Field from '../components/Field'
import Modal from '../components/Modal'
import MonthPicker from '../components/MonthPicker'
import PageHeader from '../components/PageHeader'
import { formatDate, formatMoney } from '../lib/format'
import { loadMasterData } from '../lib/masterData'
import { currentMonth, monthLabel } from '../lib/months'
import { useFinanceData } from '../lib/useFinanceData'

/** Monthly Plan: fixed monthly obligations -> minimum monthly target (US-08). */
export default function PlanPage() {
  const { user } = useAuth()
  const { categories } = useFinanceData()
  const [month, setMonth] = useState(currentMonth())
  const [plan, setPlan] = useState(null)
  const [error, setError] = useState(null)
  const [dialog, setDialog] = useState(null)
  const [version, setVersion] = useState(0)

  useEffect(() => {
    api.get('/plan', { params: { month } }).then(({ data }) => setPlan(data), setError)
  }, [month, version])

  const refresh = () => setVersion((v) => v + 1)
  const close = () => setDialog(null)
  const phaseName = Object.fromEntries(user.phases.map((p) => [p.id, p.name]))
  const items = plan?.items ?? []
  const active = items.filter((i) => i.active_this_month)
  const inactive = items.filter((i) => !i.active_this_month)

  return (
    <>
      <PageHeader
        eyebrow="Monthly Plan"
        title="What you pay every month"
        lead="Rent, insurance, loan EMIs — every fixed obligation. Their total is the least you need to earn each month."
        actions={
          <button className="btn btn-primary" onClick={() => setDialog({ type: 'item' })}>
            Add plan item
          </button>
        }
      />
      <ErrorBanner error={error} />

      <section className="card hero">
        <div>
          <p className="stat-label">Minimum monthly target · {monthLabel(month)}</p>
          <p className="hero-value">{plan ? formatMoney(plan.minimum_target, plan.currency) : '…'}</p>
          <p className="stat-sub">
            Sum of {active.length} active {active.length === 1 ? 'item' : 'items'} in {user.base_currency}
            {plan?.estimated_rates && ' · some exchange rates are estimated'}
          </p>
        </div>
        <div>
          <MonthPicker value={month} onChange={setMonth} />
          <p className="stat-sub">
            <Link to="/target">See how much you earned against it →</Link>
          </p>
        </div>
      </section>

      <section className="card">
        <h2>Active in {monthLabel(month)}</h2>
        <PlanTable
          items={active}
          phaseName={phaseName}
          baseCurrency={user.base_currency}
          onEdit={(i) => setDialog({ type: 'item', item: i })}
          onDelete={(i) => setDialog({ type: 'delete', item: i })}
        />
      </section>
      {inactive.length > 0 && (
        <section className="card">
          <h2>Not active this month</h2>
          <p className="hint">Outside their valid dates or life phase.</p>
          <PlanTable
            items={inactive}
            phaseName={phaseName}
            baseCurrency={user.base_currency}
            onEdit={(i) => setDialog({ type: 'item', item: i })}
            onDelete={(i) => setDialog({ type: 'delete', item: i })}
          />
        </section>
      )}

      {dialog?.type === 'item' && (
        <Modal title={dialog.item ? 'Edit plan item' : 'Add plan item'} onClose={close}>
          <PlanItemForm
            item={dialog.item}
            categories={categories}
            phases={user.phases}
            baseCurrency={user.base_currency}
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
          title="Delete plan item?"
          message={`“${dialog.item.name}” will no longer count towards your monthly target.`}
          onConfirm={() => api.delete(`/plan/${dialog.item.id}`).then(refresh)}
          onClose={close}
        />
      )}
    </>
  )
}

function PlanTable({ items, phaseName, baseCurrency, onEdit, onDelete }) {
  if (!items.length) return <p className="empty-inline">No items.</p>
  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th scope="col">Item</th>
            <th scope="col">Valid</th>
            <th scope="col" className="num">Amount</th>
            <th scope="col" className="num">In {baseCurrency}</th>
            <th scope="col"><span className="visually-hidden">Actions</span></th>
          </tr>
        </thead>
        <tbody>
          {items.map((i) => (
            <tr key={i.id}>
              <td>
                <span className="txn-category">{i.name}</span>
                {i.phase_id && <span className="txn-note">Only during {phaseName[i.phase_id]}</span>}
              </td>
              <td>
                {formatDate(i.valid_from)} – {i.valid_to ? formatDate(i.valid_to) : 'open'}
              </td>
              <td className="num money">{formatMoney(i.amount, i.currency_code)}</td>
              <td className="num money">{i.amount_base ? formatMoney(i.amount_base, baseCurrency) : '–'}</td>
              <td className="row-actions">
                {i.loan_id ? (
                  <Link className="link-btn" to={`/loans/${i.loan_id}`}>Loan →</Link>
                ) : (
                  <>
                    <button className="link-btn" onClick={() => onEdit(i)}>Edit</button>
                    <button className="link-btn danger" onClick={() => onDelete(i)}>Delete</button>
                  </>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function PlanItemForm({ item, categories, phases, baseCurrency, onSaved, onCancel }) {
  const [currencies, setCurrencies] = useState([])
  const [form, setForm] = useState({
    name: item?.name ?? '',
    category_id: item?.category_id ?? '',
    amount: item?.amount ?? '',
    currency_code: item?.currency_code ?? baseCurrency,
    valid_from: item?.valid_from ?? `${currentMonth()}-01`,
    valid_to: item?.valid_to ?? '',
    phase_id: item?.phase_id ?? '',
  })
  const [errors, setErrors] = useState({})
  const [error, setError] = useState(null)
  const expense = useMemo(() => categories.filter((c) => c.kind === 'EXPENSE'), [categories])

  useEffect(() => {
    loadMasterData().then((m) => setCurrencies(m.currencies)).catch(() => {})
  }, [])

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))
  const submit = async (e) => {
    e.preventDefault()
    setErrors({})
    setError(null)
    const payload = { ...form, valid_to: form.valid_to || null, phase_id: form.phase_id || null }
    try {
      if (item) await api.patch(`/plan/${item.id}`, payload)
      else await api.post('/plan', payload)
      onSaved()
    } catch (err) {
      setError(err)
      setErrors(fieldErrors(err))
    }
  }

  return (
    <form className="form" onSubmit={submit} noValidate>
      <ErrorBanner error={error} />
      <Field id="pi-name" label="Name" error={errors.name} hint="e.g. Rent, Health insurance (TK), Semester ticket">
        {(a) => <input {...a} className="input" value={form.name} onChange={set('name')} />}
      </Field>
      <Field id="pi-category" label="Category" error={errors.category_id}>
        {(a) => (
          <select {...a} className="input" value={form.category_id} onChange={set('category_id')}>
            <option value="">Choose…</option>
            {expense.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        )}
      </Field>
      <div className="form-grid">
        <Field id="pi-amount" label="Amount per month" error={errors.amount}>
          {(a) => <input {...a} className="input input-money" inputMode="decimal" value={form.amount} onChange={set('amount')} />}
        </Field>
        <Field id="pi-currency" label="Currency" error={errors.currency_code}>
          {(a) => (
            <CurrencySelect {...a} currencies={currencies} value={form.currency_code}
              onChange={(v) => setForm((f) => ({ ...f, currency_code: v }))} />
          )}
        </Field>
      </div>
      <div className="form-grid">
        <Field id="pi-from" label="Valid from" error={errors.valid_from}>
          {(a) => <input {...a} className="input" type="date" value={form.valid_from} onChange={set('valid_from')} />}
        </Field>
        <Field id="pi-to" label="Valid until (optional)" error={errors.valid_to}>
          {(a) => <input {...a} className="input" type="date" value={form.valid_to} onChange={set('valid_to')} />}
        </Field>
      </div>
      <Field id="pi-phase" label="Only during phase (optional)" error={errors.phase_id}>
        {(a) => (
          <select {...a} className="input" value={form.phase_id} onChange={set('phase_id')}>
            <option value="">Any phase</option>
            {phases.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        )}
      </Field>
      <div className="form-actions">
        <button type="button" className="btn btn-secondary" onClick={onCancel}>Cancel</button>
        <button className="btn btn-primary">{item ? 'Save' : 'Add item'}</button>
      </div>
    </form>
  )
}
