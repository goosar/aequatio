import { useState } from 'react'
import './App.css'
import RegisterForm from './components/RegisterForm'
import LoginForm from './components/LoginForm'
import ExpenseForm from './components/ExpenseForm'
import ExpensesList from './components/ExpensesList'
import type { User } from './types'

type RegistrationUser = Pick<User, 'id' | 'username' | 'email'>
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

function App() {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [showRegister, setShowRegister] = useState(false)
  const [showLogin, setShowLogin] = useState(false)
  const [expenses, setExpenses] = useState<Expense[]>([])

  function handleLoginSuccess(userData: User, authToken: string) {
    setUser(userData)
    setToken(authToken)
    setShowLogin(false)
    // Fetch user's expenses
    fetchExpenses(authToken)
  }

  function handleRegisterSuccess(userData: RegistrationUser) {
    console.log('User registered:', userData)
    setShowRegister(false)
    setShowLogin(true)
  }

  function handleLogout() {
    setUser(null)
    setToken(null)
    setExpenses([])
  }

  async function fetchExpenses(authToken: string) {
    try {
      const response = await fetch('http://localhost:8000/api/v1/expenses', {
        headers: { Authorization: `Bearer ${authToken}` },
      })
      if (!response.ok) {
        console.error('Failed to fetch expenses:', response.statusText)
        return
      }
      setExpenses(await response.json())
    } catch (error) {
      console.error('Error fetching expenses:', error)
    }
  }

  function handleExpenseAdded(expense: Expense) {
    setExpenses(prev => [expense, ...prev])
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-blue-700 shadow-lg">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-white">Aequatio</h1>
          <div className="flex gap-3">
            {!user ? (
              <>
                <button
                  onClick={() => setShowLogin(true)}
                  className="px-4 py-2 text-white border-2 border-white rounded-md hover:bg-blue-800 font-semibold"
                >
                  Login
                </button>
                <button
                  onClick={() => setShowRegister(true)}
                  className="px-4 py-2 bg-white text-blue-700 rounded-md hover:bg-blue-50 font-semibold"
                >
                  Register
                </button>
              </>
            ) : (
              <div className="flex items-center gap-4">
                <span className="text-white font-semibold">Welcome, {user.username}!</span>
                <button
                  onClick={handleLogout}
                  className="px-4 py-2 text-white border-2 border-white rounded-md hover:bg-blue-800 font-semibold"
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-6 py-8">
        {!user ? (
          <div className="bg-white rounded-lg shadow-lg p-8 text-center border-2 border-blue-200">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Expense Tracker</h2>
            <p className="text-gray-800 mb-6 text-lg">
              Track your expenses easily. Please login or register to get started.
            </p>
            <div className="flex gap-4 justify-center">
              <button
                onClick={() => setShowLogin(true)}
                className="px-6 py-3 text-blue-700 border-2 border-blue-700 rounded-md hover:bg-blue-50 font-semibold"
              >
                Login
              </button>
              <button
                onClick={() => setShowRegister(true)}
                className="px-6 py-3 bg-blue-700 text-white rounded-md hover:bg-blue-800 font-semibold"
              >
                Register
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <ExpenseForm onAdd={handleExpenseAdded} token={token!} />
            <ExpensesList expenses={expenses} />
          </div>
        )}
      </main>

      {/* Register Modal */}
      {showRegister && (
        <RegisterForm
          onClose={() => setShowRegister(false)}
          onSuccess={handleRegisterSuccess}
        />
      )}

      {/* Login Modal */}
      {showLogin && (
        <LoginForm
          onClose={() => setShowLogin(false)}
          onSuccess={handleLoginSuccess}
        />
      )}
    </div>
  )
}

export default App
