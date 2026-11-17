import { formatMoney } from '../lib/format'

/**
 * Ranked horizontal bars for "how much per category / phase". Plain HTML, so
 * values are real text (readable by screen readers, never colour-only).
 */
export default function BarList({ items, currency, label }) {
  if (!items?.length) return <p className="empty-inline">Nothing recorded in this period.</p>
  const max = Math.max(...items.map((i) => Number(i.amount)), 1)
  const total = items.reduce((s, i) => s + Number(i.amount), 0)
  return (
    <ul className="bar-list" aria-label={label}>
      {items.map((i) => {
        const value = Number(i.amount)
        return (
          <li key={i.name}>
            <div className="bar-list-row">
              <span className="bar-list-name">{i.name}</span>
              <span className="money">
                {formatMoney(i.amount, currency)}
                <span className="bar-list-share"> · {Math.round((value * 100) / (total || 1))}%</span>
              </span>
            </div>
            <div className="bar-track" aria-hidden="true">
              <span className={i.name === 'Other' ? 'bar-fill other' : 'bar-fill'} style={{ width: `${(value * 100) / max}%` }} />
            </div>
          </li>
        )
      })}
    </ul>
  )
}
