import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import api from '../api/client'
import { RemittanceForm } from './RemittancesPage'

vi.mock('../api/client', async (orig) => {
  const actual = await orig()
  return { ...actual, default: { get: vi.fn(), post: vi.fn() } }
})
vi.mock('../lib/masterData', () => ({
  loadMasterData: () => Promise.resolve({ currencies: [{ code: 'INR', name: 'Indian Rupee' }, { code: 'EUR', name: 'Euro' }], countries: [] }),
}))

const wallets = [
  { id: 'w-inr', name: 'Home Account', currency_code: 'INR' },
  { id: 'w-eur', name: 'Daily Spending', currency_code: 'EUR' },
]
const user = { home_currency: 'INR', base_currency: 'EUR' }

function setup() {
  const onSaved = vi.fn()
  render(<RemittanceForm wallets={wallets} categories={[]} user={user} onSaved={onSaved} onCancel={vi.fn()} />)
  return { onSaved, u: userEvent.setup() }
}

describe('RemittanceForm (TC-F13)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.post.mockResolvedValue({ data: {} })
  })

  it('shows the real rate and sends both own wallets', async () => {
    const { u, onSaved } = setup()
    await u.type(screen.getByLabelText('Amount sent (INR)'), '50000')
    await u.type(screen.getByLabelText('Amount received (EUR)'), '520')
    expect(screen.getByText(/1 EUR =/)).toHaveTextContent('96.15')
    await u.click(screen.getByRole('button', { name: 'Record transfer' }))
    expect(api.post).toHaveBeenCalledWith('/remittances', expect.objectContaining({
      from_wallet_id: 'w-inr', to_wallet_id: 'w-eur', sent_amount: '50000', received_amount: '520',
    }))
    expect(onSaved).toHaveBeenCalled()
  })

  it('money from family: no sender wallet, sent currency instead', async () => {
    const { u } = setup()
    await u.click(screen.getByRole('button', { name: 'Received from outside' }))
    expect(screen.queryByLabelText('From wallet')).not.toBeInTheDocument()
    await u.type(screen.getByLabelText('Amount sent (INR)'), '25000')
    await u.type(screen.getByLabelText('Amount received (EUR)'), '250')
    await u.click(screen.getByRole('button', { name: 'Record transfer' }))
    const payload = api.post.mock.calls[0][1]
    expect(payload).toMatchObject({ from_wallet_id: null, to_wallet_id: 'w-eur', sent_currency: 'INR' })
    expect(payload).not.toHaveProperty('fee_amount')
  })
})
