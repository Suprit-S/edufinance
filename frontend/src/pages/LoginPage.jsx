import { useState } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import ErrorBanner from '../components/ErrorBanner'
import Field from '../components/Field'
import AuthLayout from './AuthLayout'

export default function LoginPage() {
  const { login, status, notice } = useAuth()
  const location = useLocation()
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  if (status === 'authenticated') return <Navigate to={location.state?.from || '/'} replace />

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await login(form.email, form.password)
    } catch (err) {
      setError(err)
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthLayout title="Welcome back" lead="Log in to continue planning your money.">
      {notice && !error && (
        <div className="alert alert-info" role="status">
          {notice}
        </div>
      )}
      <ErrorBanner error={error} />
      <form className="form" onSubmit={submit} noValidate>
        <Field id="email" label="E-mail">
          {(a) => (
            <input
              {...a}
              className="input"
              type="email"
              autoComplete="email"
              required
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
          )}
        </Field>
        <Field id="password" label="Password">
          {(a) => (
            <input
              {...a}
              className="input"
              type="password"
              autoComplete="current-password"
              required
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
          )}
        </Field>
        <button className="btn btn-primary btn-block" disabled={busy}>
          {busy ? 'Logging in…' : 'Log in'}
        </button>
      </form>
      <p className="auth-switch">
        New here? <Link to="/register">Create an account</Link>
      </p>
    </AuthLayout>
  )
}
