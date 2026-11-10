import { addMonths } from '../lib/months'

/** Previous / month input / next. Value format: YYYY-MM. */
export default function MonthPicker({ value, onChange, label = 'Month' }) {
  return (
    <div className="month-picker" role="group" aria-label={label}>
      <button type="button" className="btn btn-secondary btn-small" aria-label="Previous month" onClick={() => onChange(addMonths(value, -1))}>
        ‹
      </button>
      <input
        className="input"
        type="month"
        aria-label={label}
        value={value}
        onChange={(e) => e.target.value && onChange(e.target.value)}
      />
      <button type="button" className="btn btn-secondary btn-small" aria-label="Next month" onClick={() => onChange(addMonths(value, 1))}>
        ›
      </button>
    </div>
  )
}
