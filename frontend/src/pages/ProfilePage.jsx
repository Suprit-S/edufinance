import { useEffect, useState } from 'react'
import api, { fieldErrors } from '../api/client'
import { useAuth } from '../auth/useAuth'
import ConfirmDialog from '../components/ConfirmDialog'
import CurrencySelect from '../components/CurrencySelect'
import ErrorBanner from '../components/ErrorBanner'
import Field from '../components/Field'
import Modal from '../components/Modal'
import PageHeader from '../components/PageHeader'
import { formatDate } from '../lib/format'
import { loadMasterData } from '../lib/masterData'
import { GENDERS } from '../lib/options'

/** Profile, life phases and password (US-01, US-02, US-03). */
export default function ProfilePage() {
  const { user, refresh } = useAuth()
  const [dialog, setDialog] = useState(null)
  const close = () => setDialog(null)
  const afterChange = () => {
    close()
    refresh()
  }

  return (
    <>
      <PageHeader
        eyebrow="Profile"
        title="Profile & life phases"
        lead="Your journey in phases. Every transaction is assigned to the phase of its date — change your dates and the history follows."
      />

      <section className="card">
        <div className="section-head">
          <h2>Your journey</h2>
          <button className="btn btn-secondary" onClick={() => setDialog({ type: 'phase' })}>
            Add phase
          </button>
        </div>
        <ol className="phase-list">
          {user.phases.map((p) => (
            <li key={p.id} className={`phase-item ${p.is_current ? 'current' : ''}`}>
              <div className="phase-main">
                <p className="phase-name">
                  {p.name}
                  {p.is_current && <span className="badge badge-healthy">Now</span>}
                  {!p.is_system && <span className="tag">custom</span>}
                </p>
                <p className="phase-dates">
                  {formatDate(p.start_date)} – {p.end_date ? formatDate(p.end_date) : 'open-ended'}
                </p>
                {p.progress_pct !== null && (
                  <div
                    className="progress"
                    role="progressbar"
                    aria-label={`${p.name} progress`}
                    aria-valuenow={p.progress_pct}
                    aria-valuemin={0}
                    aria-valuemax={100}
                  >
                    <span style={{ width: `${p.progress_pct}%` }} />
                  </div>
                )}
              </div>
              <div className="row-actions">
                <button className="link-btn" onClick={() => setDialog({ type: 'phase', phase: p })}>
                  {p.is_system ? 'Rename' : 'Edit'}
                </button>
                {!p.is_system && (
                  <button className="link-btn danger" onClick={() => setDialog({ type: 'delete-phase', phase: p })}>
                    Delete
                  </button>
                )}
              </div>
            </li>
          ))}
        </ol>
        <p className="hint">
          Dates of Pre-departure, Settling in, Study and Work come from your profile below. Add a
          phase such as “Job search” for periods that are not covered.
        </p>
      </section>

      <ProfileForm user={user} onSaved={refresh} />
      <PasswordForm />

      {dialog?.type === 'phase' && (
        <Modal title={dialog.phase ? `Edit “${dialog.phase.name}”` : 'Add phase'} onClose={close}>
          <PhaseForm phase={dialog.phase} onSaved={afterChange} onCancel={close} />
        </Modal>
      )}
      {dialog?.type === 'delete-phase' && (
        <ConfirmDialog
          title="Delete phase?"
          message={`“${dialog.phase.name}” will be removed. Its transactions are assigned to other phases by date.`}
          onConfirm={() => api.delete(`/phases/${dialog.phase.id}`).then(refresh)}
          onClose={close}
        />
      )}
    </>
  )
}

function PhaseForm({ phase, onSaved, onCancel }) {
  const system = phase?.is_system
  const [form, setForm] = useState({
    name: phase?.name ?? 'Job search',
    phase_type: 'JOB_SEARCH',
    start_date: phase?.start_date ?? '',
    end_date: phase?.end_date ?? '',
  })
  const [errors, setErrors] = useState({})
  const [error, setError] = useState(null)
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    setErrors({})
    const payload = system
      ? { name: form.name }
      : { name: form.name, start_date: form.start_date, end_date: form.end_date || null }
    try {
      if (phase) await api.patch(`/phases/${phase.id}`, payload)
      else await api.post('/phases', { ...payload, phase_type: form.phase_type })
      onSaved()
    } catch (err) {
      setError(err)
      setErrors(fieldErrors(err))
    }
  }

  return (
    <form className="form" onSubmit={submit} noValidate>
      <ErrorBanner error={error} />
      <Field id="p-name" label="Name" error={errors.name}>
        {(a) => <input {...a} className="input" value={form.name} onChange={set('name')} />}
      </Field>
      {!phase && (
        <Field id="p-type" label="Kind of phase">
          {(a) => (
            <select {...a} className="input" value={form.phase_type} onChange={set('phase_type')}>
              <option value="JOB_SEARCH">Job search</option>
              <option value="CUSTOM">Other (e.g. internship, semester abroad)</option>
            </select>
          )}
        </Field>
      )}
      {!system && (
        <div className="form-grid">
          <Field id="p-start" label="Start" error={errors.start_date}>
            {(a) => <input {...a} className="input" type="date" value={form.start_date} onChange={set('start_date')} />}
          </Field>
          <Field id="p-end" label="End (optional)" error={errors.end_date}>
            {(a) => <input {...a} className="input" type="date" value={form.end_date} onChange={set('end_date')} />}
          </Field>
        </div>
      )}
      <div className="form-actions">
        <button type="button" className="btn btn-secondary" onClick={onCancel}>
          Cancel
        </button>
        <button className="btn btn-primary">Save</button>
      </div>
    </form>
  )
}

const PROFILE_KEYS = [
  'full_name',
  'email',
  'date_of_birth',
  'gender',
  'destination_country',
  'home_currency',
  'base_currency',
  'planning_start_date',
  'arrival_date',
  'study_start_date',
  'study_end_date',
  'settling_in_days',
]

function ProfileForm({ user, onSaved }) {
  const [master, setMaster] = useState({ currencies: [], countries: [] })
  const [form, setForm] = useState(() =>
    Object.fromEntries(PROFILE_KEYS.map((k) => [k, user[k] ?? ''])),
  )
  const [errors, setErrors] = useState({})
  const [error, setError] = useState(null)
  const [saved, setSaved] = useState(false)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    loadMasterData().then(setMaster).catch(setError)
  }, [])

  const set = (key) => (e) => {
    setSaved(false)
    setForm((f) => ({ ...f, [key]: e.target.value }))
  }
  const currencyChanged =
    form.base_currency !== user.base_currency || form.home_currency !== user.home_currency

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setErrors({})
    const payload = {}
    for (const k of PROFILE_KEYS) {
      if (String(form[k] ?? '') !== String(user[k] ?? '')) payload[k] = form[k] === '' ? null : form[k]
    }
    if (payload.settling_in_days != null) payload.settling_in_days = Number(payload.settling_in_days)
    try {
      if (Object.keys(payload).length) await api.patch('/me', payload)
      await onSaved()
      setSaved(true)
    } catch (err) {
      setError(err)
      setErrors(fieldErrors(err))
    } finally {
      setBusy(false)
    }
  }

  const input = (key, label, type = 'text', hint) => (
    <Field id={`pf-${key}`} label={label} error={errors[key]} hint={hint}>
      {(a) => <input {...a} className="input" type={type} value={form[key] ?? ''} onChange={set(key)} />}
    </Field>
  )

  return (
    <section className="card">
      <h2>Profile</h2>
      <p className="hint">Age: {user.age} years (calculated from your date of birth, not stored).</p>
      <ErrorBanner error={error} />
      {saved && (
        <div className="alert alert-info" role="status">
          Profile saved. Phases and transactions were updated.
        </div>
      )}
      <form className="form" onSubmit={submit} noValidate>
        <div className="form-grid">
          {input('full_name', 'Full name')}
          {input('email', 'E-mail', 'email')}
          {input('date_of_birth', 'Date of birth', 'date')}
          <Field id="pf-gender" label="Gender (optional)" error={errors.gender}>
            {(a) => (
              <select {...a} className="input" value={form.gender ?? ''} onChange={set('gender')}>
                {GENDERS.map(([v, l]) => (
                  <option key={v} value={v}>{l}</option>
                ))}
              </select>
            )}
          </Field>
        </div>
        <div className="form-grid form-grid-3">
          <Field id="pf-country" label="Country you study in" error={errors.destination_country}>
            {(a) => (
              <select {...a} className="input" value={form.destination_country} onChange={set('destination_country')}>
                {master.countries.map((c) => (
                  <option key={c.code} value={c.code}>{c.name}</option>
                ))}
              </select>
            )}
          </Field>
          <Field id="pf-home" label="Home currency" error={errors.home_currency}>
            {(a) => (
              <CurrencySelect {...a} currencies={master.currencies} value={form.home_currency}
                onChange={(v) => setForm((f) => ({ ...f, home_currency: v }))} />
            )}
          </Field>
          <Field id="pf-base" label="Base currency" error={errors.base_currency}>
            {(a) => (
              <CurrencySelect {...a} currencies={master.currencies} value={form.base_currency}
                onChange={(v) => setForm((f) => ({ ...f, base_currency: v }))} />
            )}
          </Field>
        </div>
        {currencyChanged && (
          <div className="alert alert-warning" role="status">
            Existing entries keep the values converted with your old currencies; only new entries
            use the new ones.
          </div>
        )}
        <div className="form-grid">
          {input('planning_start_date', 'Started planning', 'date')}
          {input('arrival_date', 'Arrival abroad', 'date')}
          {input('study_start_date', 'Study starts', 'date')}
          {input('study_end_date', 'Study ends', 'date')}
          {input('settling_in_days', 'Settling-in period (days)', 'number', 'Default 60 days after arrival')}
        </div>
        <div className="form-actions">
          <button className="btn btn-primary" disabled={busy}>
            {busy ? 'Saving…' : 'Save profile'}
          </button>
        </div>
      </form>
    </section>
  )
}

function PasswordForm() {
  const [form, setForm] = useState({ current_password: '', new_password: '' })
  const [errors, setErrors] = useState({})
  const [message, setMessage] = useState(null)
  const [error, setError] = useState(null)

  const submit = async (e) => {
    e.preventDefault()
    setErrors({})
    setError(null)
    setMessage(null)
    try {
      await api.post('/auth/password', form)
      setForm({ current_password: '', new_password: '' })
      setMessage('Password changed.')
    } catch (err) {
      setError(err)
      setErrors(fieldErrors(err))
    }
  }

  return (
    <section className="card">
      <h2>Change password</h2>
      <ErrorBanner error={error} />
      {message && (
        <div className="alert alert-info" role="status">
          {message}
        </div>
      )}
      <form className="form" onSubmit={submit} noValidate>
        <div className="form-grid">
          <Field id="pw-current" label="Current password" error={errors.current_password}>
            {(a) => (
              <input {...a} className="input" type="password" autoComplete="current-password"
                value={form.current_password} onChange={(e) => setForm({ ...form, current_password: e.target.value })} />
            )}
          </Field>
          <Field id="pw-new" label="New password" error={errors.new_password} hint="8+ characters, a letter and a number">
            {(a) => (
              <input {...a} className="input" type="password" autoComplete="new-password"
                value={form.new_password} onChange={(e) => setForm({ ...form, new_password: e.target.value })} />
            )}
          </Field>
        </div>
        <div className="form-actions">
          <button className="btn btn-secondary">Change password</button>
        </div>
      </form>
    </section>
  )
}
