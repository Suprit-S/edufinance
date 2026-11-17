import { formatDate, formatMoney } from '../lib/format'

/**
 * Transactions as a table (desktop) that turns into stacked cards on phones.
 * Amounts: original currency, plus base-currency value when different.
 */
export default function TransactionList({ items, wallets = [], baseCurrency, showWallet = true, onEdit, onDelete }) {
  if (!items.length) {
    return <p className="empty-inline">No transactions yet.</p>
  }
  const walletName = Object.fromEntries(wallets.map((w) => [w.id, w.name]))
  return (
    <table className="table txn-table">
      <thead>
        <tr>
          <th scope="col">Date</th>
          <th scope="col">Category</th>
          {showWallet && <th scope="col">Wallet</th>}
          <th scope="col">Phase</th>
          <th scope="col" className="num">Amount</th>
          <th scope="col">
            <span className="visually-hidden">Actions</span>
          </th>
        </tr>
      </thead>
      <tbody>
        {items.map((t) => {
          const inflow = t.kind === 'INCOME' || t.kind === 'TRANSFER_IN'
          const linked = Boolean(t.remittance_id)
          return (
            <tr key={t.id}>
              <td data-label="Date">{formatDate(t.txn_date)}</td>
              <td data-label="Category">
                <span className="txn-category">{t.category_name ?? 'Transfer'}</span>
                {t.note && <span className="txn-note">{t.note}</span>}
              </td>
              {showWallet && <td data-label="Wallet">{walletName[t.wallet_id] ?? '–'}</td>}
              <td data-label="Phase">
                {t.phase_name}
                {t.phase_is_manual && <span className="tag" title="Chosen by you">manual</span>}
              </td>
              <td data-label="Amount" className="num">
                <span className={`money ${inflow ? 'pos' : 'neg'}`}>
                  {inflow ? '+' : '−'}
                  {formatMoney(t.amount, t.currency_code)}
                </span>
                {t.currency_code !== baseCurrency && (
                  <span className="sub-money">
                    ≈ {formatMoney(t.amount_base, baseCurrency)}
                    {t.estimated && <span className="tag tag-warn" title="Exchange rate was estimated">est.</span>}
                  </span>
                )}
              </td>
              <td className="row-actions">
                {!linked && (
                  <>
                    <button type="button" className="link-btn" onClick={() => onEdit(t)}>
                      Edit
                    </button>
                    <button type="button" className="link-btn danger" onClick={() => onDelete(t)}>
                      Delete
                    </button>
                  </>
                )}
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
