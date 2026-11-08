import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import api from '../api/client'
import TransactionForm from './TransactionForm'

vi.mock('../api/client', async (orig) => {
  const actual = await orig()
  return { ...actual, default: { get: vi.fn(), post: vi.fn(), patch: vi.fn() } }
})

const wallets = [
  { id: 'w-eur', name: 'Daily Spending', currency_code: 'EUR', is_archived: false },
  { id: 'w-inr', name: 'Home Account', currency_code: 'INR', is_archived: false },
]
const categories = [
  { id: 'c-groc', name: 'Groceries', kind: 'EXPENSE', group_name: 'Living' },
  { id: 'c-ielts', name: 'Language test', kind: 'EXPENSE', group_name: 'Exams & tests' },
  { id: 'c-sal', name: 'Part-time salary', kind: 'INCOME', group_name: 'Work' },
]

function setup(props = {}) {
  const onSaved = vi.fn()
  render(
    <TransactionForm
      wallets={wallets}
      categories={categories}
      phases={[{ id: 'p1', name: 'Study' }]}
      baseCurrency="EUR"
      onSaved={onSaved}
      onCancel={vi.fn()}
      {...props}
    />,
  )
  return { onSaved, user: userEvent.setup() }
}

describe('TransactionForm (TC-F06)', () => {
  beforeEach(() => vi.clearAllMocks())

  it('offers only categories of the selected type', async () => {
    const { user } = setup()
    const select = screen.getByLabelText('Category')
    expect(select).toHaveTextContent('Groceries')
    expect(select).not.toHaveTextContent('Part-time salary')
    await user.click(screen.getByRole('button', { name: 'Income' }))
    expect(screen.getByLabelText('Category')).toHaveTextContent('Part-time salary')
    expect(screen.getByLabelText('Category')).not.toHaveTextContent('Groceries')
  })

  it('creates a base-currency expense without sending a rate', async () => {
    api.post.mockResolvedValue({ data: { id: 't1' } })
    const { user, onSaved } = setup()
    await user.type(screen.getByLabelText(/Amount/), '41.20')
    await user.selectOptions(screen.getByLabelText('Category'), 'c-groc')
    await user.type(screen.getByLabelText('Note (optional)'), 'Lidl')
    await user.click(screen.getByRole('button', { name: 'Add expense' }))
    expect(api.post).toHaveBeenCalledWith(
      '/transactions',
      expect.objectContaining({ kind: 'EXPENSE', amount: '41.20', wallet_id: 'w-eur', note: 'Lidl', category_id: 'c-groc' }),
    )
    expect(api.post.mock.calls[0][1]).not.toHaveProperty('rate_to_base')
    expect(onSaved).toHaveBeenCalled()
  })

  it('pre-fills the market rate and sends a rate the user changed (TC-F07)', async () => {
    api.get.mockResolvedValue({
      data: { rate: '0.00939891', rate_date: '2026-11-07', estimated: false },
    })
    api.post.mockResolvedValue({ data: { id: 't2' } })
    const { user } = setup({ defaultWalletId: 'w-inr' })
    const rate = await screen.findByLabelText(/1 INR = \? EUR/)
    await waitFor(() => expect(rate).toHaveValue('0.00939891'))
    await user.type(screen.getByLabelText(/Amount/), '2000')
    expect(screen.getByText('€18.80')).toBeInTheDocument()
    await user.clear(rate)
    await user.type(rate, '0.01')
    await user.selectOptions(screen.getByLabelText('Category'), 'c-ielts')
    await user.click(screen.getByRole('button', { name: 'Add expense' }))
    expect(api.post.mock.calls[0][1]).toMatchObject({ wallet_id: 'w-inr', rate_to_base: '0.01' })
  })

  it('shows field errors from the API', async () => {
    api.post.mockRejectedValue({
      status: 422,
      message: 'Some fields are invalid.',
      details: { amount: ['Must be greater than 0.'] },
    })
    const { user } = setup()
    await user.click(screen.getByRole('button', { name: 'Add expense' }))
    expect(await screen.findByText('Must be greater than 0.')).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('Some fields are invalid.')
  })
})
