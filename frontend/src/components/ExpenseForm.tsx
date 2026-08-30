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
    <div className="bg-white p-6 rounded-lg shadow-lg border-2 border-blue-200">
      <h2 className="text-xl font-bold mb-4 text-gray-900">Add New Expense</h2>
      
      {error && (
        <div className="mb-4 bg-red-100 border-2 border-red-400 text-red-900 px-4 py-3 rounded-md font-semibold">
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
            className="w-full border-2 border-gray-300 px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600 text-gray-900 bg-white"
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
              className="w-full border-2 border-gray-300 px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600 text-gray-900 bg-white"
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
              className="w-full border-2 border-gray-300 px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600 text-gray-900 bg-white"
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
            className="w-full border-2 border-gray-300 px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600 text-gray-900 bg-white"
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
            className="w-full border-2 border-gray-300 px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600 text-gray-900 bg-white"
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
            className="w-full border-2 border-gray-300 px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600 text-gray-900 bg-white"
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
            className="px-6 py-2 bg-blue-700 text-white rounded-md shadow hover:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
            disabled={isLoading}
          >
            {isLoading ? 'Adding...' : 'Add Expense'}
          </button>
        </div>
      </form>
    </div>
  )
}
