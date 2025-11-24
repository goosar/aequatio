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
  const total = expenses.reduce((s, e) => s + e.amount, 0)
  
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('de-DE', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    })
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-xl font-semibold mb-4">Your Expenses</h2>
      
      {expenses.length === 0 && (
        <div className="p-8 border-2 border-dashed border-gray-300 rounded-lg text-center text-gray-500">
          No expenses yet. Add your first expense above!
        </div>
      )}
      
      {expenses.length > 0 && (
        <>
          <ul className="divide-y divide-gray-200">
            {expenses.map((expense) => (
              <li key={expense.id} className="py-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-start justify-between">
                      <h3 className="font-semibold text-gray-900">{expense.title}</h3>
                      <span className="font-mono text-lg font-bold text-rose-600 ml-4">
                        {expense.amount.toFixed(2)} {expense.currency}
                      </span>
                    </div>
                    
                    <div className="mt-1 space-y-1 text-sm text-gray-600">
                      <div className="flex items-center gap-2">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                          {expense.category}
                        </span>
                        {expense.vendor && (
                          <span className="text-gray-500">• {expense.vendor}</span>
                        )}
                      </div>
                      
                      {expense.description && (
                        <p className="text-gray-600">{expense.description}</p>
                      )}
                      
                      <div className="text-xs text-gray-400">
                        {formatDate(expense.expensedate)}
                      </div>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
          
          <div className="mt-6 pt-4 border-t border-gray-200">
            <div className="flex justify-between items-center">
              <span className="text-lg font-semibold text-gray-700">Total:</span>
              <span className="text-2xl font-bold text-rose-600">
                {total.toFixed(2)} {expenses[0]?.currency || 'EUR'}
              </span>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
