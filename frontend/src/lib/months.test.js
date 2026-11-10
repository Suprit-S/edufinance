import { describe, expect, it } from 'vitest'
import { addMonths, currentMonth, monthLabel } from './months'

describe('month helpers (TC-F10)', () => {
  it('adds and subtracts months across years', () => {
    expect(addMonths('2026-11', 3)).toBe('2027-02')
    expect(addMonths('2026-01', -1)).toBe('2025-12')
  })
  it('formats labels and the current month', () => {
    expect(monthLabel('2026-11')).toBe('Nov 2026')
    expect(monthLabel('2026-11', true)).toBe('Nov')
    expect(currentMonth(new Date(2026, 10, 8))).toBe('2026-11')
  })
})
