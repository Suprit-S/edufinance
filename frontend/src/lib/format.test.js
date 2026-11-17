import { describe, expect, it } from 'vitest'
import { formatDate, formatMoney, formatPercent } from './format'

describe('formatMoney (TC-F01)', () => {
  it('formats euros with two decimals and grouping', () => {
    expect(formatMoney('1234.5', 'EUR')).toBe('€1,234.50')
  })
  it('formats rupees and negative values', () => {
    expect(formatMoney('-14000', 'INR')).toBe('-₹14,000.00')
  })
  it('adds a plus sign when asked', () => {
    expect(formatMoney('250', 'EUR', { signed: true })).toBe('+€250.00')
  })
  it('shows a dash for missing values', () => {
    expect(formatMoney(null, 'EUR')).toBe('–')
    expect(formatMoney('abc', 'EUR')).toBe('–')
  })
})

describe('formatPercent and formatDate (TC-F02)', () => {
  it('rounds percentages to one decimal', () => {
    expect(formatPercent(22.645)).toBe('22.6%')
  })
  it('formats ISO dates without timezone shifts', () => {
    expect(formatDate('2026-11-05')).toBe('5 Nov 2026')
  })
})
