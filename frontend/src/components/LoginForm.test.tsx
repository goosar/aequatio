import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, test, vi } from 'vitest'

import LoginForm from './LoginForm'

afterEach(() => vi.restoreAllMocks())

test('uses the user returned by login without requesting an arbitrary profile', async () => {
  const user = userEvent.setup()
  const onSuccess = vi.fn()
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
    new Response(
      JSON.stringify({
        access_token: 'signed-token',
        token_type: 'bearer',
        user: {
          id: '550e8400-e29b-41d4-a716-446655440000',
          username: 'testuser',
          email: 'test@example.com',
          is_active: true,
          created_at: '2026-08-30T10:00:00Z',
        },
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } },
    ),
  )

  render(<LoginForm onClose={() => undefined} onSuccess={onSuccess} />)
  await user.type(screen.getByLabelText('Email'), 'test@example.com')
  await user.type(screen.getByLabelText('Password'), 'SecurePass123!')
  await user.click(screen.getByRole('button', { name: 'Login' }))

  expect(fetchMock).toHaveBeenCalledTimes(1)
  expect(onSuccess).toHaveBeenCalledWith(
    expect.objectContaining({ username: 'testuser' }),
    'signed-token',
  )
})
