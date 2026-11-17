import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import Sidebar from './Sidebar'
import { NAV_ITEMS } from './navItems'

function renderAt(path = '/') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Sidebar />
    </MemoryRouter>,
  )
}

describe('Sidebar (TC-F03)', () => {
  it('shows every main navigation link', () => {
    renderAt()
    for (const item of NAV_ITEMS) {
      expect(screen.getByRole('link', { name: item.label })).toBeInTheDocument()
    }
  })

  it('marks the current page as active', () => {
    renderAt('/wallets')
    expect(screen.getByRole('link', { name: 'Wallets' })).toHaveClass('active')
    expect(screen.getByRole('link', { name: 'Dashboard' })).not.toHaveClass('active')
  })
})

describe('ThemeToggle (TC-F04)', () => {
  it('switches to dark mode and remembers the choice', async () => {
    renderAt()
    await userEvent.click(screen.getByRole('button', { name: 'Dark' }))
    expect(document.documentElement).toHaveAttribute('data-theme', 'dark')
    expect(localStorage.getItem('edufinance.theme')).toBe('dark')
    await userEvent.click(screen.getByRole('button', { name: 'Auto' }))
    expect(document.documentElement).not.toHaveAttribute('data-theme')
  })
})
