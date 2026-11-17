/**
 * Labelled form field. The error text is linked to the input with
 * aria-describedby so screen readers announce it (NFR-12).
 */
export default function Field({ id, label, error, hint, children, className = '' }) {
  const describedBy = [error ? `${id}-error` : null, hint ? `${id}-hint` : null]
    .filter(Boolean)
    .join(' ')
  const child =
    typeof children === 'function'
      ? children({ id, 'aria-invalid': Boolean(error), 'aria-describedby': describedBy || undefined })
      : children
  return (
    <div className={`field ${error ? 'has-error' : ''} ${className}`}>
      <label htmlFor={id} className="label">
        {label}
      </label>
      {child}
      {hint && !error && (
        <p id={`${id}-hint`} className="hint">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} className="error-text">
          {error}
        </p>
      )}
    </div>
  )
}
