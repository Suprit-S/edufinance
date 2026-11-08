import { useEffect, useRef } from 'react'

/**
 * Accessible dialog: focus moves inside on open and back on close,
 * Escape and the backdrop close it.
 */
export default function Modal({ title, onClose, children, wide = false }) {
  const panel = useRef(null)

  useEffect(() => {
    const previous = document.activeElement
    const first = panel.current?.querySelector(
      'input:not([type=hidden]), select, textarea, button:not(.modal-close)',
    )
    first?.focus()
    const onKey = (e) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
      previous?.focus?.()
    }
  }, [onClose])

  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div
        ref={panel}
        className={`modal ${wide ? 'modal-wide' : ''}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        <header className="modal-header">
          <h2 id="modal-title">{title}</h2>
          <button type="button" className="modal-close" aria-label="Close" onClick={onClose}>
            ×
          </button>
        </header>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  )
}
