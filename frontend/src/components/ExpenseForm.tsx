import { useState } from 'react'

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

const CATEGORIES = [
  { value: 'Lebensmittel', label: 'Lebensmittel' },
  { value: 'Lieferservice', label: 'Lieferservice' },
  { value: 'Drogerieartikel', label: 'Drogerieartikel' },
  { value: 'Urlaubsreisen', label: 'Urlaubsreisen' },
  { value: 'Kleidung', label: 'Kleidung' },
  { value: 'Sonstiges', label: 'Sonstiges' },
]

const CURRENCIES = ['EUR', 'USD', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY']

export default function ExpenseForm({
  onAdd,
  token,
}: {
  onAdd: (expense: Expense) => void
  token: string
}) {
  const [title, setTitle] = useState('')
  const [amount, setAmount] = useState('')
  const [currency, setCurrency] = useState('EUR')
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState('Sonstiges')
  const [vendor, setVendor] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    
    const amountNum = parseFloat(amount)
    if (!title || isNaN(amountNum) || amountNum <= 0) {
      setError('Please enter a valid title and amount')
      return
    }

    setIsLoading(true)
    setError('')

    try {
      const response = await fetch('http://localhost:8000/api/v1/expense', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          title,
          amount: amountNum,
          currency,
          description: description || undefined,
          category,
          expensedate: new Date().toISOString(),
          vendor: vendor || undefined,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to create expense')
      }

      const data = await response.json()
      onAdd(data)
      
      // Reset form
      setTitle('')
      setAmount('')
      setDescription('')
      setVendor('')
      setCurrency('EUR')
      setCategory('Sonstiges')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create expense')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-xl font-semibold mb-4">Add New Expense</h2>
      
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Title *
          </label>
          <input
            type="text"
            className="w-full border px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-rose-500"
            placeholder="e.g., Grocery Shopping"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={isLoading}
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Amount *
            </label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              className="w-full border px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-rose-500"
              placeholder="0.00"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              disabled={isLoading}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Currency
            </label>
            <select
              className="w-full border px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-rose-500"
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              disabled={isLoading}
            >
              {CURRENCIES.map((curr) => (
                <option key={curr} value={curr}>
                  {curr}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Category *
          </label>
          <select
            className="w-full border px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-rose-500"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            disabled={isLoading}
            required
          >
            {CATEGORIES.map((cat) => (
              <option key={cat.value} value={cat.value}>
                {cat.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Vendor
          </label>
          <input
            type="text"
            className="w-full border px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-rose-500"
            placeholder="e.g., Rewe, Amazon"
            value={vendor}
            onChange={(e) => setVendor(e.target.value)}
            disabled={isLoading}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            className="w-full border px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-rose-500"
            placeholder="Optional notes about this expense"
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            disabled={isLoading}
          />
        </div>

        <div className="text-right">
          <button
            type="submit"
            className="px-6 py-2 bg-rose-600 text-white rounded-md shadow hover:bg-rose-700 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={isLoading}
          >
            {isLoading ? 'Adding...' : 'Add Expense'}
          </button>
        </div>
      </form>
    </div>
  )
}
