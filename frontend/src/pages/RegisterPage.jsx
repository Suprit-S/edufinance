import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { fieldErrors } from '../api/client'
import { useAuth } from '../auth/useAuth'
import CurrencySelect from '../components/CurrencySelect'
import ErrorBanner from '../components/ErrorBanner'
import Field from '../components/Field'
import { loadMasterData } from '../lib/masterData'
import { GENDERS } from '../lib/options'
import AuthLayout from './AuthLayout'

const EMPTY = {
  full_name: '',
  email: '',
  password: '',
  date_of_birth: '',
  gender: '',
  home_currency: '',
  destination_country: '',
  base_currency: '',
  planning_start_date: '',
  arrival_date: '',
  study_start_date: '',
  study_end_date: '',
}

/** Registration (FR-01): account, about you, currencies, journey dates. */
export default function RegisterPage() {
  const { register, status } = useAuth()
  const [form, setForm] = useState(EMPTY)
  const [master, setMaster] = useState({ currencies: [], countries: [] })
  const [errors, setErrors] = useState({})
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    loadMasterData().then(setMaster).catch(setError)
  }, [])

  // After successful registration the user starts with creating wallets.
  if (status === 'authenticated') return <Navigate to="/wallets" replace state={{ welcome: true }} />

  const set = (key) => (value) => setForm((f) => ({ ...f, [key]: value }))
  const onInput = (key) => (e) => set(key)(e.target.value)

  const chooseCountry = (code) => {
    const country = master.countries.find((c) => c.code === code)
    setForm((f) => ({
      ...f,
      destination_country: code,
      // Suggest the local currency as base currency (can be changed).
      base_currency: country ? country.default_currency : f.base_currency,
    }))
  }

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setErrors({})
    const payload = { ...form, gender: form.gender || null }
    try {
      await register(payload)
    } catch (err) {
      setError(err)
      setErrors(fieldErrors(err))
    } finally {
      setBusy(false)
    }
  }

  const date = (key, label, hint) => (
    <Field id={key} label={label} error={errors[key]} hint={hint}>
      {(a) => (
        <input {...a} className="input" type="date" required value={form[key]} onChange={onInput(key)} />
      )}
    </Field>
  )

  return (
    <AuthLayout
      title="Create your account"
      lead="Two minutes now, and every cost of your journey has a home."
    >
      <ErrorBanner error={error} />
      <form className="form" onSubmit={submit} noValidate>
        <fieldset className="form-section">
          <legend>Account</legend>
          <Field id="full_name" label="Full name" error={errors.full_name}>
            {(a) => (
              <input {...a} className="input" autoComplete="name" value={form.full_name} onChange={onInput('full_name')} />
            )}
          </Field>
          <Field id="email" label="E-mail" error={errors.email}>
            {(a) => (
              <input {...a} className="input" type="email" autoComplete="email" value={form.email} onChange={onInput('email')} />
            )}
          </Field>
          <Field
            id="password"
            label="Password"
            error={errors.password}
            hint="At least 8 characters with a letter and a number."
          >
            {(a) => (
              <input {...a} className="input" type="password" autoComplete="new-password" value={form.password} onChange={onInput('password')} />
            )}
          </Field>
        </fieldset>

        <fieldset className="form-section">
          <legend>About you</legend>
          <div className="form-grid">
            <Field id="date_of_birth" label="Date of birth" error={errors.date_of_birth}>
              {(a) => (
                <input {...a} className="input" type="date" value={form.date_of_birth} onChange={onInput('date_of_birth')} />
              )}
            </Field>
            <Field id="gender" label="Gender (optional)" error={errors.gender}>
              {(a) => (
                <select {...a} className="input" value={form.gender} onChange={onInput('gender')}>
                  {GENDERS.map(([v, l]) => (
                    <option key={v} value={v}>{l}</option>
                  ))}
                </select>
              )}
            </Field>
          </div>
        </fieldset>

        <fieldset className="form-section">
          <legend>Your money</legend>
          <Field id="destination_country" label="Country you study in" error={errors.destination_country}>
            {(a) => (
              <select {...a} className="input" value={form.destination_country} onChange={(e) => chooseCountry(e.target.value)}>
                <option value="">Choose…</option>
                {master.countries.map((c) => (
                  <option key={c.code} value={c.code}>{c.name}</option>
                ))}
              </select>
            )}
          </Field>
          <div className="form-grid">
            <Field id="home_currency" label="Home currency" error={errors.home_currency} hint="Loans, family support">
              {(a) => (
                <CurrencySelect {...a} currencies={master.currencies} value={form.home_currency} onChange={set('home_currency')} />
              )}
            </Field>
            <Field id="base_currency" label="Base currency (abroad)" error={errors.base_currency} hint="Rent, groceries, salary">
              {(a) => (
                <CurrencySelect {...a} currencies={master.currencies} value={form.base_currency} onChange={set('base_currency')} />
              )}
            </Field>
          </div>
        </fieldset>

        <fieldset className="form-section">
          <legend>Your journey</legend>
          <p className="hint">Not sure yet? Use your best guess — you can change every date later.</p>
          <div className="form-grid">
            {date('planning_start_date', 'Started planning', 'First test, application or fee')}
            {date('arrival_date', 'Arrival abroad')}
            {date('study_start_date', 'Study starts')}
            {date('study_end_date', 'Study ends (planned)')}
          </div>
        </fieldset>

        <button className="btn btn-primary btn-block" disabled={busy}>
          {busy ? 'Creating account…' : 'Create account'}
        </button>
      </form>
      <p className="auth-switch">
        Already registered? <Link to="/login">Log in</Link>
      </p>
    </AuthLayout>
  )
}
