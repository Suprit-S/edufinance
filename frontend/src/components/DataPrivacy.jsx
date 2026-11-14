import { useState } from 'react'
import api, { fieldErrors } from '../api/client'
import { useAuth } from '../auth/useAuth'
import ErrorBanner from './ErrorBanner'
import Field from './Field'
import Modal from './Modal'

/** Export all own data and delete the account (FR-42, GDPR). */
export default function DataPrivacy() {
  const { logout } = useAuth()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [deleting, setDeleting] = useState(false)

  const download = async () => {
    setBusy(true)
    setError(null)
    try {
      const res = await api.get('/account/export', { responseType: 'blob' })
      const name =
        res.headers?.['content-disposition']?.match(/filename="(.+)"/)?.[1] ?? 'edufinance-export.json'
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = name
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="card">
      <h2>Data &amp; privacy</h2>
      <p className="hint">Your data belongs to you. Download everything as a JSON file, or delete your account for good.</p>
      <ErrorBanner error={error} />
      <div className="actions" style={{ marginTop: 12 }}>
        <button className="btn btn-secondary" onClick={download} disabled={busy}>
          {busy ? 'Preparing…' : 'Download my data'}
        </button>
        <button className="btn btn-danger" onClick={() => setDeleting(true)}>
          Delete my account
        </button>
      </div>
      {deleting && <DeleteAccount onClose={() => setDeleting(false)} onDeleted={() => logout()} />}
    </section>
  )
}

function DeleteAccount({ onClose, onDeleted }) {
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState({})
  const [error, setError] = useState(null)

  const submit = async (e) => {
    e.preventDefault()
    setErrors({})
    setError(null)
    try {
      await api.delete('/account', { data: { password } })
      onDeleted()
    } catch (err) {
      setError(err)
      setErrors(fieldErrors(err))
    }
  }

  return (
    <Modal title="Delete your account?" onClose={onClose}>
      <form className="form" onSubmit={submit} noValidate>
        <ErrorBanner error={error} />
        <p>
          All wallets, transactions, transfers, loans and your profile are deleted permanently. This cannot be
          undone — download your data first if you want to keep it.
        </p>
        <Field id="del-password" label="Confirm with your password" error={errors.password}>
          {(a) => (
            <input {...a} className="input" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
          )}
        </Field>
        <div className="form-actions">
          <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-danger">Delete everything</button>
        </div>
      </form>
    </Modal>
  )
}
