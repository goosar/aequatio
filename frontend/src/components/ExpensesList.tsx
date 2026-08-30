type Expense = {
  id: string
  title: string
  amount: number
  currency: string
  description?: string
  category: string
  expensedate: string
  vendor?: string
  created_at: string
}

export default function ExpensesList({ expenses }: { expenses: Expense[] }) {
  const totals = expenses.reduce<Record<string, number>>((byCurrency, expense) => {
    byCurrency[expense.currency] = (byCurrency[expense.currency] || 0) + expense.amount
    return byCurrency
  }, {})

  const formatDate = (dateString: string) => new Date(dateString).toLocaleDateString('de-DE', {
    year: 'numeric', month: 'short', day: 'numeric',
  })

  return (
    <div className="bg-white p-6 rounded-xl shadow-lg border border-blue-100">
      <h2 className="text-xl font-semibold mb-4 text-blue-900">Your Expenses</h2>

      {expenses.length === 0 && (
        <div className="p-8 border-2 border-dashed border-blue-200 rounded-lg text-center text-blue-700">
          No expenses yet. Add your first expense above!
        </div>
      )}

      {expenses.length > 0 && (
        <>
          <ul className="divide-y divide-blue-100">
            {expenses.map((expense) => (
              <li key={expense.id} className="py-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-start justify-between">
                      <h3 className="font-semibold text-blue-950">{expense.title}</h3>
                      <span className="font-mono text-lg font-bold text-blue-700 ml-4">
                        {expense.amount.toFixed(2)} {expense.currency}
                      </span>
                    </div>
                    <div className="mt-1 space-y-1 text-sm text-blue-800">
                      <div className="flex items-center gap-2">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                          {expense.category}
                        </span>
                        {expense.vendor && <span className="text-blue-600">• {expense.vendor}</span>}
                      </div>
                      {expense.description && <p className="text-blue-700">{expense.description}</p>}
                      <div className="text-xs text-blue-500">{formatDate(expense.expensedate)}</div>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
          <div className="mt-6 pt-4 border-t border-blue-100 space-y-2">
            {Object.entries(totals).map(([currency, total]) => (
              <div className="flex justify-between items-center" key={currency}>
                <span className="text-lg font-semibold text-blue-900">Total ({currency}):</span>
                <span className="text-2xl font-bold text-blue-700">{total.toFixed(2)} {currency}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
