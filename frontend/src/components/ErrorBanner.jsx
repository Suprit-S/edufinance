/** Page- or form-level error message (role=alert so it is announced). */
export default function ErrorBanner({ error }) {
  if (!error) return null
  const message = typeof error === 'string' ? error : error.message
  return (
    <div className="alert alert-danger" role="alert">
      {message}
    </div>
  )
}
