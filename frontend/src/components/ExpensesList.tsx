type Expense = { id: string; desc: string; amount: number; payer: string }

export default function ExpensesList({expenses}:{expenses:Expense[]}){
  const total = expenses.reduce((s,e)=>s+e.amount,0)
  return (
    <div className="mt-4 bg-white p-4 rounded-lg shadow-sm">
      <h4 className="font-medium mb-3">Expenses</h4>
      {expenses.length===0 && (
        <div className="p-4 border border-dashed rounded text-gray-500">No expenses yet — add your first one.</div>
      )}
      <ul className="divide-y">
        {expenses.map(e=> (
          <li key={e.id} className="py-3 flex justify-between items-center">
            <div>
              <div className="font-semibold">{e.desc}</div>
              <div className="text-sm text-gray-500">paid by {e.payer}</div>
            </div>
            <div className="font-mono text-lg font-semibold">€{e.amount.toFixed(2)}</div>
          </li>
        ))}
      </ul>
      <div className="mt-4 text-right text-indigo-700 font-semibold">Total: €{total.toFixed(2)}</div>
    </div>
  )
}
