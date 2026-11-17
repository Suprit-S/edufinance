import { describe, expect, it } from 'vitest'
import { normaliseError } from './client'

describe('normaliseError (TC-F05)', () => {
  it('keeps the backend error code and message', () => {
    const err = {
      response: {
        status: 422,
        data: { error: { code: 'VALIDATION_ERROR', message: 'Invalid', details: { amount: ['x'] } } },
      },
    }
    expect(normaliseError(err)).toEqual({
      status: 422,
      code: 'VALIDATION_ERROR',
      message: 'Invalid',
      details: { amount: ['x'] },
    })
  })

  it('explains network failures', () => {
    expect(normaliseError(new Error('fail')).code).toBe('NETWORK_ERROR')
  })
})

describe('fieldErrors (TC-F05b)', () => {
  it('maps marshmallow details to one message per field', async () => {
    const { fieldErrors } = await import('./client')
    expect(
      fieldErrors({ details: { amount: ['Not a valid number.', 'x'], start_date: ['Bad'] } }),
    ).toEqual({ amount: 'Not a valid number.', start_date: 'Bad' })
    expect(fieldErrors({ details: null })).toEqual({})
  })
})
