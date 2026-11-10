import { formatMoney } from '../lib/format'

/** "Can I afford my minimum part-payment?" (FR-34). An estimate, not advice. */
export default function AffordabilityCard({ data, loanCurrency }) {
  if (!data) {
    return (
      <div className="verdict verdict-none">
        <strong>Part-payment check</strong>
        <p className="hint">Set a minimum part-payment on this loan to see whether you can afford it.</p>
      </div>
    )
  }
  const ccy = data.currency
  const min = formatMoney(data.min_part_payment, loanCurrency)
  const text = {
    AFFORDABLE: `You can afford a part-payment of ${min} now.`,
    SAVE: `Set aside your surplus for about ${data.months_needed} ${data.months_needed === 1 ? 'month' : 'months'} to pay ${min}.`,
    NOT_AFFORDABLE: `At your current surplus a part-payment of ${min} is not affordable.`,
  }[data.status]
  const cls = { AFFORDABLE: 'verdict-good', SAVE: 'verdict-save', NOT_AFFORDABLE: 'verdict-none' }[data.status]
  return (
    <div className={`verdict ${cls}`} role="status">
      <strong>{text}</strong>
      <dl className="kv">
        <dt>Average monthly surplus (last {data.lookback_months} months)</dt>
        <dd>{formatMoney(data.avg_surplus, ccy, { signed: true })}</dd>
        <dt>After {data.buffer_pct}% safety buffer</dt>
        <dd>{formatMoney(data.buffered_surplus, ccy)}</dd>
        <dt>Minimum part-payment</dt>
        <dd>{formatMoney(data.min_part_payment_base, ccy)}{data.estimated_rate ? ' (est.)' : ''}</dd>
        <dt>Interest it would save</dt>
        <dd>{formatMoney(data.interest_saved_if_paid, loanCurrency)}</dd>
        <dt>EMIs it would save</dt>
        <dd>{data.emis_saved_if_paid}</dd>
      </dl>
      <p className="hint">An estimate from your own records — not financial advice.</p>
    </div>
  )
}
