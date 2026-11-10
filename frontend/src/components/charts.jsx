import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { formatMoney } from '../lib/format'
import { monthLabel } from '../lib/months'

const axis = { stroke: 'var(--text-faint)', fontSize: 12, tickLine: false, axisLine: false }
const tooltipStyle = {
  contentStyle: {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 8,
    color: 'var(--text)',
    fontSize: 13,
  },
  labelStyle: { color: 'var(--text)', fontWeight: 600 },
  itemStyle: { color: 'var(--text)' },
}

function compact(value, currency) {
  return new Intl.NumberFormat('en-IE', {
    style: 'currency',
    currency,
    currencyDisplay: 'narrowSymbol',
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value)
}

/**
 * Last months: earned and spent as bars, the minimum target as a dashed line.
 * One axis, one currency. A table version sits underneath (accessibility).
 */
export function TargetHistoryChart({ history, currency }) {
  const data = history.map((h) => ({
    month: monthLabel(h.month, true),
    full: monthLabel(h.month),
    Earned: Number(h.earned),
    Spent: Number(h.spent),
    Target: Number(h.target),
  }))
  return (
    <figure className="chart">
      <div className="chart-box" role="img" aria-label="Earned, spent and target for the last six months">
        <ResponsiveContainer width="100%" height={260}>
          <ComposedChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }} barGap={2}>
            <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
            <XAxis dataKey="month" {...axis} />
            <YAxis {...axis} width={56} tickFormatter={(v) => compact(v, currency)} />
            <Tooltip
              {...tooltipStyle}
              cursor={{ fill: 'var(--surface-muted)' }}
              labelFormatter={(_, p) => p?.[0]?.payload.full}
              formatter={(v, name) => [formatMoney(v, currency), name]}
            />
            <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 13, color: 'var(--text-muted)' }} />
            <Bar dataKey="Earned" animationDuration={400} fill="var(--series-1)" radius={[4, 4, 0, 0]} maxBarSize={22} />
            <Bar dataKey="Spent" animationDuration={400} fill="var(--series-2)" radius={[4, 4, 0, 0]} maxBarSize={22} />
            <Line
              dataKey="Target"
              type="stepAfter"
              stroke="var(--chart-ref)"
              strokeWidth={2}
              strokeDasharray="5 4"
              dot={false}
              animationDuration={400}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <details className="chart-table">
        <summary>Show as table</summary>
        <table className="table">
          <thead>
            <tr>
              <th scope="col">Month</th>
              <th scope="col" className="num">Target</th>
              <th scope="col" className="num">Earned</th>
              <th scope="col" className="num">Spent</th>
            </tr>
          </thead>
          <tbody>
            {history.map((h) => (
              <tr key={h.month}>
                <td>{monthLabel(h.month)}</td>
                <td className="num money">{formatMoney(h.target, currency)}</td>
                <td className="num money">{formatMoney(h.earned, currency)}</td>
                <td className="num money">{formatMoney(h.spent, currency)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  )
}

/** Projected outstanding balance month by month at the current EMI. */
export function LoanBalanceChart({ schedule, currency, startMonth }) {
  const [y, m] = startMonth.split('-').map(Number)
  const data = schedule.map((row) => {
    const index = y * 12 + m - 1 + row.month - 1
    const key = `${Math.floor(index / 12)}-${String((index % 12) + 1).padStart(2, '0')}`
    return { label: monthLabel(key), balance: Number(row.balance) }
  })
  return (
    <div className="chart-box" role="img" aria-label="Projected outstanding balance until payoff">
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
          <XAxis dataKey="label" {...axis} minTickGap={40} />
          <YAxis {...axis} width={60} tickFormatter={(v) => compact(v, currency)} />
          <Tooltip
            {...tooltipStyle}
            formatter={(v) => [formatMoney(v, currency), 'Outstanding']}
          />
          <Line dataKey="balance" stroke="var(--series-1)" strokeWidth={2} dot={false} activeDot={{ r: 4 }} animationDuration={400} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
