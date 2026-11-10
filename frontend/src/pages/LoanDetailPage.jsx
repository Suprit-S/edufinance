import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import api, { fieldErrors } from '../api/client'
import { useAuth } from '../auth/useAuth'
import AffordabilityCard from '../components/AffordabilityCard'
import { LoanBalanceChart } from '../components/charts'
import ConfirmDialog from '../components/ConfirmDialog'
import ErrorBanner from '../components/ErrorBanner'
import Field from '../components/Field'
import LoanForm from '../components/LoanForm'
import Modal from '../components/Modal'
import PageHeader from '../components/PageHeader'
import { todayIso } from '../lib/dates'
import { formatDate, formatMoney } from '../lib/format'
import { currentMonth, monthLabel } from '../lib/months'
import { useFinanceData } from '../lib/useFinanceData'

/** One loan: forecast, affordability, payments (US-10, US-11). */
export default function LoanDetailPage() {
  const { loanId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { wallets } = useFinanceData()
  const [loan, setLoan] = useState(null)
  const [error, setError] = useState(null)
  const [dialog, setDialog] = useState(null)

  const load = useCallback(() => {
    api.get(`/loans/${loanId}`).then(({ data }) => setLoan(data), setError)
  }, [loanId])
  useEffect(load, [load])
  const close = () => setDialog(null)

  if (!loan) {
    return error ? (
      <section className="card empty">
        <h2>Loan not found</h2>
        <Link to="/loans">Back to loans</Link>
      </section>
    ) : (
      <p className="status-line">Loading…</p>
    )
  }

  const ccy = loan.currency_code
  const s = loan.summary
  const startMonth =
    loan.emi_start_date && loan.emi_start_date.slice(0, 7) > currentMonth()
      ? loan.emi_start_date.slice(0, 7)
      : currentMonth()
  const latest = loan.payments[0]

  return (
    <>
      <p className="breadcrumb">
        <Link to="/loans">Loans</Link> / {loan.name}
      </p>
      <PageHeader
        eyebrow={`${loan.lender ? `${loan.lender} · ` : ''}${loan.annual_rate_pct}% p.a. · ${ccy}`}
        title={loan.name}
        actions={
          <div className="actions">
            {loan.status === 'ACTIVE' && (
              <>
                <button className="btn btn-primary" onClick={() => setDialog({ type: 'pay', ptype: 'EMI' })}>
                  Record EMI
                </button>
                <button className="btn btn-secondary" onClick={() => setDialog({ type: 'pay', ptype: 'PART_PAYMENT' })}>
                  Part-payment
                </button>
              </>
            )}
            <button className="btn btn-secondary" onClick={() => setDialog({ type: 'edit' })}>Edit</button>
            <button className="btn btn-danger" onClick={() => setDialog({ type: 'delete' })}>Delete</button>
          </div>
        }
      />
      <ErrorBanner error={error} />

      <div className="grid grid-3">
        <div className="card">
          <p className="stat-label">Outstanding</p>
          <p className="stat-value">{formatMoney(loan.outstanding_amount, ccy)}</p>
          <p className="stat-sub">{s.repaid_pct}% of {formatMoney(loan.sanctioned_amount, ccy)} repaid</p>
        </div>
        <div className="card">
          <p className="stat-label">Debt-free</p>
          <p className="stat-value phase-title">
            {loan.status === 'CLOSED' ? 'Paid off' : s.payoff_month ? monthLabel(s.payoff_month) : 'Never at this EMI'}
          </p>
          <p className="stat-sub">
            {s.months_to_payoff ? `${s.months_to_payoff} EMIs of ${formatMoney(loan.emi_amount, ccy)}` : ''}
            {loan.emi_start_date && loan.status === 'ACTIVE' && ` · first EMI ${formatDate(loan.emi_start_date)}`}
          </p>
        </div>
        <div className="card">
          <p className="stat-label">Interest</p>
          <dl className="kv">
            <dt>Paid so far</dt>
            <dd>{formatMoney(s.interest_paid, ccy)}</dd>
            <dt>Still to pay</dt>
            <dd>{formatMoney(s.future_interest, ccy)}</dd>
            <dt>Saved by part-payments</dt>
            <dd>{formatMoney(s.interest_saved, ccy)}</dd>
          </dl>
        </div>
      </div>
      {loan.status === 'ACTIVE' && !s.emi_covers_interest && (
        <div className="alert alert-danger" role="alert">
          The EMI does not cover the monthly interest — the loan would never be repaid. Increase the EMI.
        </div>
      )}

      <div className="grid grid-2">
        <section className="card">
          <h2>Can I make a part-payment?</h2>
          <AffordabilityCard data={loan.affordability} loanCurrency={ccy} />
        </section>
        <section className="card">
          <h2>Balance until payoff</h2>
          {s.schedule?.length ? (
            <>
              <LoanBalanceChart schedule={s.schedule} currency={ccy} startMonth={startMonth} />
              <details className="schedule">
                <summary>Repayment schedule ({s.schedule.length} months)</summary>
                <div className="table-wrap">
                  <table className="table">
                    <thead>
                      <tr>
                        <th scope="col">#</th>
                        <th scope="col" className="num">Payment</th>
                        <th scope="col" className="num">Interest</th>
                        <th scope="col" className="num">Principal</th>
                        <th scope="col" className="num">Balance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {s.schedule.map((r) => (
                        <tr key={r.month}>
                          <td>{r.month}</td>
                          <td className="num money">{formatMoney(r.payment, ccy)}</td>
                          <td className="num money">{formatMoney(r.interest, ccy)}</td>
                          <td className="num money">{formatMoney(r.principal, ccy)}</td>
                          <td className="num money">{formatMoney(r.balance, ccy)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
            </>
          ) : (
            <p className="empty-inline">{loan.status === 'CLOSED' ? 'This loan is paid off.' : 'No forecast possible.'}</p>
          )}
        </section>
      </div>

      <section className="card">
        <h2>Payments</h2>
        {loan.payments.length === 0 ? (
          <p className="empty-inline">No payments recorded yet.</p>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">Date</th>
                  <th scope="col">Type</th>
                  <th scope="col" className="num">Amount</th>
                  <th scope="col" className="num">Interest</th>
                  <th scope="col" className="num">Principal</th>
                  <th scope="col" className="num">Balance after</th>
                  <th scope="col"><span className="visually-hidden">Actions</span></th>
                </tr>
              </thead>
              <tbody>
                {loan.payments.map((p) => (
                  <tr key={p.id}>
                    <td>{formatDate(p.paid_on)}</td>
                    <td>
                      {p.payment_type === 'EMI' ? 'EMI' : 'Part-payment'}
                      {p.payment_type === 'PART_PAYMENT' && (
                        <span className="txn-note">
                          saves {formatMoney(p.interest_saved, ccy)} · {p.emis_saved} EMIs
                        </span>
                      )}
                    </td>
                    <td className="num money">{formatMoney(p.amount, ccy)}</td>
                    <td className="num money">{formatMoney(p.interest_part, ccy)}</td>
                    <td className="num money">{formatMoney(p.principal_part, ccy)}</td>
                    <td className="num money">{formatMoney(p.balance_after, ccy)}</td>
                    <td className="row-actions">
                      {p.id === latest.id && (
                        <button className="link-btn danger" onClick={() => setDialog({ type: 'undo', payment: p })}>
                          Undo
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="hint">Only the most recent payment can be undone, so the balance history stays correct.</p>
      </section>

      {dialog?.type === 'pay' && (
        <Modal title={dialog.ptype === 'EMI' ? 'Record EMI' : 'Record part-payment'} onClose={close}>
          <PaymentForm
            loan={loan}
            wallets={wallets}
            paymentType={dialog.ptype}
            onCancel={close}
            onSaved={() => {
              close()
              load()
            }}
          />
        </Modal>
      )}
      {dialog?.type === 'edit' && (
        <Modal title="Edit loan" onClose={close}>
          <LoanForm
            loan={loan}
            wallets={wallets}
            defaultCurrency={user.home_currency}
            onCancel={close}
            onSaved={() => {
              close()
              load()
            }}
          />
        </Modal>
      )}
      {dialog?.type === 'undo' && (
        <ConfirmDialog
          title="Undo payment?"
          message={`The ${formatMoney(dialog.payment.amount, ccy)} payment of ${formatDate(dialog.payment.paid_on)} is removed and the balance goes back to ${formatMoney(dialog.payment.balance_before, ccy)}.`}
          confirmLabel="Undo payment"
          onConfirm={() => api.delete(`/loans/${loan.id}/payments/${dialog.payment.id}`).then(load)}
          onClose={close}
        />
      )}
      {dialog?.type === 'delete' && (
        <ConfirmDialog
          title="Delete loan?"
          message="The loan, its payments and its EMI plan line are removed. Wallet entries of past payments stay."
          onConfirm={() => api.delete(`/loans/${loan.id}`).then(() => navigate('/loans'))}
          onClose={close}
        />
      )}
    </>
  )
}

function PaymentForm({ loan, wallets, paymentType, onSaved, onCancel }) {
  const sameCcy = wallets.filter((w) => w.currency_code === loan.currency_code && !w.is_archived)
  const [form, setForm] = useState({
    amount: paymentType === 'EMI' ? loan.emi_amount : (loan.min_part_payment ?? ''),
    paid_on: todayIso(),
    wallet_id: loan.default_wallet_id ?? '',
    note: '',
  })
  const [errors, setErrors] = useState({})
  const [error, setError] = useState(null)
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    setErrors({})
    setError(null)
    try {
      await api.post(`/loans/${loan.id}/payments`, {
        payment_type: paymentType,
        amount: form.amount,
        paid_on: form.paid_on,
        wallet_id: form.wallet_id || null,
        note: form.note || null,
      })
      onSaved()
    } catch (err) {
      setError(err)
      setErrors(fieldErrors(err))
    }
  }

  return (
    <form className="form" onSubmit={submit} noValidate>
      <ErrorBanner error={error} />
      <div className="form-grid">
        <Field id="pay-amount" label={`Amount (${loan.currency_code})`} error={errors.amount}>
          {(a) => <input {...a} className="input input-money" inputMode="decimal" value={form.amount} onChange={set('amount')} />}
        </Field>
        <Field id="pay-date" label="Paid on" error={errors.paid_on}>
          {(a) => <input {...a} className="input" type="date" value={form.paid_on} onChange={set('paid_on')} />}
        </Field>
      </div>
      <Field id="pay-wallet" label="Paid from wallet" error={errors.wallet_id}
        hint="The payment is also booked as an expense in this wallet.">
        {(a) => (
          <select {...a} className="input" value={form.wallet_id} onChange={set('wallet_id')}>
            <option value="">Not from a wallet</option>
            {sameCcy.map((w) => (
              <option key={w.id} value={w.id}>{w.name}</option>
            ))}
          </select>
        )}
      </Field>
      <Field id="pay-note" label="Note (optional)" error={errors.note}>
        {(a) => <input {...a} className="input" value={form.note} onChange={set('note')} />}
      </Field>
      <div className="form-actions">
        <button type="button" className="btn btn-secondary" onClick={onCancel}>Cancel</button>
        <button className="btn btn-primary">Record payment</button>
      </div>
    </form>
  )
}
