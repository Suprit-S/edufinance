import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { renderWithAuth } from '../test/renderWithAuth'
import Sidebar from './Sidebar'
import { NAV_ITEMS } from './navItems'

describe('Sidebar (TC-F03)', () => {
  it('shows every main navigation link and the user', () => {
    renderWithAuth(<Sidebar />)
    for (const item of NAV_ITEMS) {
      expect(screen.getByRole('link', { name: item.label })).toBeInTheDocument()
    }
    expect(screen.getByText('Ananya Rao')).toBeInTheDocument()
    expect(screen.getByText('INR → EUR')).toBeInTheDocument()
  })

  it('marks the current page as active', () => {
    renderWithAuth(<Sidebar />, { path: '/wallets' })
    expect(screen.getByRole('link', { name: 'Wallets' })).toHaveClass('active')
    expect(screen.getByRole('link', { name: 'Dashboard' })).not.toHaveClass('active')
  })

  it('logs out (TC-F08)', async () => {
    const { auth } = renderWithAuth(<Sidebar />)
    await userEvent.click(screen.getByRole('button', { name: 'Log out' }))
    expect(auth.logout).toHaveBeenCalled()
  })
})

describe('ThemeToggle (TC-F04)', () => {
  it('switches to dark mode and remembers the choice', async () => {
    renderWithAuth(<Sidebar />)
    await userEvent.click(screen.getByRole('button', { name: 'Dark' }))
    expect(document.documentElement).toHaveAttribute('data-theme', 'dark')
    expect(localStorage.getItem('edufinance.theme')).toBe('dark')
    await userEvent.click(screen.getByRole('button', { name: 'Auto' }))
    expect(document.documentElement).not.toHaveAttribute('data-theme')
  })
})
