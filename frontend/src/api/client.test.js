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
