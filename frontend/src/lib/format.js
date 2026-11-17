/**
 * Display helpers. The backend sends money as strings ("1234.50") so no
 * precision is lost in JSON; we only turn them into numbers for display.
 */

/** Format an amount in a currency, e.g. formatMoney('1234.5', 'EUR') -> "€1,234.50". */
export function formatMoney(amount, currency, { locale = 'en-IE', signed = false } = {}) {
  if (amount === null || amount === undefined || amount === '') return '–'
  const value = Number(amount)
  if (Number.isNaN(value)) return '–'
  const formatted = new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    currencyDisplay: 'narrowSymbol',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Math.abs(value))
  if (value < 0) return `-${formatted}`
  return signed && value > 0 ? `+${formatted}` : formatted
}

/** Format a percentage with one decimal, e.g. 22.645 -> "22.6%". */
export function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '–'
  return `${Number(value).toFixed(1)}%`
}

/** Format an ISO date (YYYY-MM-DD) for display, e.g. "5 Nov 2026". */
export function formatDate(iso, locale = 'en-GB') {
  if (!iso) return '–'
  const [y, m, d] = iso.split('-').map(Number)
  return new Intl.DateTimeFormat(locale, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(Date.UTC(y, m - 1, d)))
}
