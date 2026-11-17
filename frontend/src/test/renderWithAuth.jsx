import { render } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AuthContext } from '../auth/useAuth'

export const TEST_USER = {
  id: 'u1',
  full_name: 'Ananya Rao',
  email: 'ananya@example.com',
  age: 25,
  home_currency: 'INR',
  base_currency: 'EUR',
  phases: [
    { id: 'p1', name: 'Pre-departure', phase_type: 'PRE_DEPARTURE', is_system: true },
    { id: 'p3', name: 'Study', phase_type: 'STUDY', is_system: true, is_current: true },
  ],
}

/** Render inside a router and a fake auth context. */
export function renderWithAuth(ui, { path = '/', auth = {} } = {}) {
  const value = {
    user: TEST_USER,
    status: 'authenticated',
    notice: null,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    refresh: vi.fn(),
    setUser: vi.fn(),
    ...auth,
  }
  return {
    auth: value,
    ...render(
      <MemoryRouter initialEntries={[path]}>
        <AuthContext.Provider value={value}>{ui}</AuthContext.Provider>
      </MemoryRouter>,
    ),
  }
}
