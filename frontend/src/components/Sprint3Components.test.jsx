import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import api from '../api/client'
import { renderWithAuth } from '../test/renderWithAuth'
import LoginPage from '../pages/LoginPage'
import BarList from './BarList'
import DataPrivacy from './DataPrivacy'

vi.mock('../api/client', async (orig) => {
  const actual = await orig()
  return { ...actual, default: { get: vi.fn(), delete: vi.fn() } }
})

describe('BarList (TC-F14)', () => {
  it('shows amounts and shares as text, largest bar full width', () => {
    const { container } = render(
      <BarList
        currency="EUR"
        label="Spending"
        items={[
          { name: 'Rent', amount: '435.00' },
          { name: 'Groceries', amount: '145.00' },
          { name: 'Other', amount: '20.00' },
        ]}
      />,
    )
    expect(screen.getByRole('list', { name: 'Spending' })).toBeInTheDocument()
    expect(screen.getByText('€435.00')).toBeInTheDocument()
    expect(screen.getByText(/73%/)).toBeInTheDocument()
    const fills = container.querySelectorAll('.bar-fill')
    expect(fills[0]).toHaveStyle({ width: '100%' })
    expect(fills[2]).toHaveClass('other')
  })

  it('has an empty state', () => {
    render(<BarList items={[]} currency="EUR" />)
    expect(screen.getByText('Nothing recorded in this period.')).toBeInTheDocument()
  })
})

describe('Login page without demo credentials (TC-F15)', () => {
  it('starts with empty fields and does not show the demo login', () => {
    renderWithAuth(<LoginPage />, { path: '/login', auth: { status: 'anonymous', user: null } })
    expect(screen.getByLabelText('E-mail')).toHaveValue('')
    expect(screen.getByLabelText('Password')).toHaveValue('')
    expect(screen.queryByText(/demo@edufinance\.app/)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /demo/i })).not.toBeInTheDocument()
  })
})

describe('DataPrivacy (TC-F16)', () => {
  beforeEach(() => vi.clearAllMocks())

  it('deletes the account only with the password and then logs out', async () => {
    api.delete.mockRejectedValueOnce({ status: 422, message: 'Password is incorrect.', details: { password: ['Incorrect password.'] } })
    api.delete.mockResolvedValueOnce({})
    const { auth } = renderWithAuth(<DataPrivacy />)
    const u = userEvent.setup()
    await u.click(screen.getByRole('button', { name: 'Delete my account' }))
    await u.type(screen.getByLabelText('Confirm with your password'), 'wrong')
    await u.click(screen.getByRole('button', { name: 'Delete everything' }))
    expect(await screen.findByText('Incorrect password.')).toBeInTheDocument()
    expect(auth.logout).not.toHaveBeenCalled()
    await u.clear(screen.getByLabelText('Confirm with your password'))
    await u.type(screen.getByLabelText('Confirm with your password'), 'Demo#2026')
    await u.click(screen.getByRole('button', { name: 'Delete everything' }))
    expect(api.delete).toHaveBeenLastCalledWith('/account', { data: { password: 'Demo#2026' } })
    expect(auth.logout).toHaveBeenCalled()
  })
})
