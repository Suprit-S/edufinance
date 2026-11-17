/** Month helpers on 'YYYY-MM' strings (no time-zone surprises). */
export function currentMonth(d = new Date()) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

export function addMonths(value, n) {
  const [y, m] = value.split('-').map(Number)
  const index = y * 12 + (m - 1) + n
  return `${Math.floor(index / 12)}-${String((index % 12) + 1).padStart(2, '0')}`
}

/** 'YYYY-MM' -> 'Nov 2026' (or 'Nov' when short). */
export function monthLabel(value, short = false) {
  if (!value) return '–'
  const [y, m] = value.split('-').map(Number)
  const name = new Intl.DateTimeFormat('en-GB', { month: 'short', timeZone: 'UTC' }).format(
    new Date(Date.UTC(y, m - 1, 1)),
  )
  return short ? name : `${name} ${y}`
}
