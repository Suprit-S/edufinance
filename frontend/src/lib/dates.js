/** Today as YYYY-MM-DD in the user's local time zone. */
export function todayIso() {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

/** Readable label for enum values, e.g. PROOF_OF_FUNDS -> "Proof of funds". */
export function humanize(value) {
  if (!value) return ''
  const s = value.toLowerCase().replaceAll('_', ' ')
  return s.charAt(0).toUpperCase() + s.slice(1)
}
