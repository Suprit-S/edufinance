import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import AffordabilityCard from './AffordabilityCard'
import RunwayBadge from './RunwayBadge'

const base = {
  currency: 'EUR',
  min_part_payment: '10000.00',
  min_part_payment_base: '94.05',
  avg_surplus: '300.00',
  buffered_surplus: '240.00',
  lookback_months: 3,
  buffer_pct: 20,
  interest_saved_if_paid: '5123.40',
  emis_saved_if_paid: 1,
  estimated_rate: false,
}

describe('AffordabilityCard (TC-F11)', () => {
  it('says when the part-payment is affordable', () => {
    render(<AffordabilityCard data={{ ...base, status: 'AFFORDABLE', months_needed: 0 }} loanCurrency="INR" />)
    expect(screen.getByRole('status')).toHaveTextContent('You can afford a part-payment of ₹10,000.00 now.')
    expect(screen.getByText('€240.00')).toBeInTheDocument()
  })
  it('says how many months to save', () => {
    render(<AffordabilityCard data={{ ...base, status: 'SAVE', months_needed: 5 }} loanCurrency="INR" />)
    expect(screen.getByRole('status')).toHaveTextContent('about 5 months')
  })
  it('asks for a minimum part-payment when none is set', () => {
    render(<AffordabilityCard data={null} loanCurrency="INR" />)
    expect(screen.getByText(/Set a minimum part-payment/)).toBeInTheDocument()
  })
})

describe('RunwayBadge (TC-F12)', () => {
  it('shows status as text with days', () => {
    render(<RunwayBadge runway={{ status: 'CRITICAL', days: 16 }} />)
    expect(screen.getByText('Critical · 16 days left')).toHaveClass('badge-critical')
  })
  it('handles wallets without spending', () => {
    render(<RunwayBadge runway={{ status: 'HEALTHY', days: null }} />)
    expect(screen.getByText(/Healthy · no spending/)).toBeInTheDocument()
  })
})
