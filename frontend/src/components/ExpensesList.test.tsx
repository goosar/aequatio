import { render, screen } from '@testing-library/react'
import { test, expect } from 'vitest'

import ExpensesList from './ExpensesList'

test('shows separate totals for expenses in different currencies', () => {
  render(
    <ExpensesList
      expenses={[
        { id: '1', title: 'Euro', amount: 10, currency: 'EUR', category: 'Other', expensedate: '2026-01-01', created_at: '2026-01-01' },
        { id: '2', title: 'Dollar', amount: 12, currency: 'USD', category: 'Other', expensedate: '2026-01-02', created_at: '2026-01-02' },
      ]}
    />,
  )

  expect(screen.getAllByText('10.00 EUR')).toHaveLength(2)
  expect(screen.getAllByText('12.00 USD')).toHaveLength(2)
  expect(screen.queryByText('22.00 EUR')).not.toBeInTheDocument()
})
