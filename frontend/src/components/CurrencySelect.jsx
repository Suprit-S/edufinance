/** <select> of ISO currencies, e.g. "EUR – Euro". */
export default function CurrencySelect({ currencies = [], value, onChange, ...props }) {
  return (
    <select className="input" value={value} onChange={(e) => onChange(e.target.value)} {...props}>
      <option value="">Choose…</option>
      {currencies.map((c) => (
        <option key={c.code} value={c.code}>
          {c.code} – {c.name}
        </option>
      ))}
    </select>
  )
}
