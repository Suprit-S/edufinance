import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { renderWithAuth } from '../test/renderWithAuth'
import LoginPage from './LoginPage'

describe('LoginPage (TC-F09)', () => {
  it('shows the generic error message for wrong credentials', async () => {
    const login = vi.fn().mockRejectedValue({ status: 401, message: 'E-mail or password is incorrect.' })
    renderWithAuth(<LoginPage />, { path: '/login', auth: { status: 'anonymous', user: null, login } })
    await userEvent.type(screen.getByLabelText('E-mail'), 'ananya@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'wrong')
    await userEvent.click(screen.getByRole('button', { name: 'Log in' }))
    expect(login).toHaveBeenCalledWith('ananya@example.com', 'wrong')
    expect(await screen.findByRole('alert')).toHaveTextContent('E-mail or password is incorrect.')
  })

  it('shows why the user was logged out', () => {
    renderWithAuth(<LoginPage />, {
      path: '/login',
      auth: { status: 'anonymous', user: null, notice: 'Your session has expired. Please log in again.' },
    })
    expect(screen.getByRole('status')).toHaveTextContent('Your session has expired')
  })
})
