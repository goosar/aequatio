import { useState } from 'react'
import './App.css'
import RegisterForm from './components/RegisterForm'
import LoginForm from './components/LoginForm'
import ExpenseForm from './components/ExpenseForm'
import ExpensesList from './components/ExpensesList'

type User = { id: string; username: string; email: string }
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

  function handleRegisterSuccess(userData: User) {
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
    // TODO: Implement fetch expenses from API
    console.log('Fetching expenses with token:', authToken)
  }

  function handleExpenseAdded(expense: Expense) {
    setExpenses(prev => [expense, ...prev])
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-rose-600">Aequatio</h1>
          <div className="flex gap-3">
            {!user ? (
              <>
                <button
                  onClick={() => setShowLogin(true)}
                  className="px-4 py-2 text-rose-600 border border-rose-600 rounded-md hover:bg-rose-50"
                >
                  Login
                </button>
                <button
                  onClick={() => setShowRegister(true)}
                  className="px-4 py-2 bg-rose-600 text-white rounded-md hover:bg-rose-700"
                >
                  Register
                </button>
              </>
            ) : (
              <div className="flex items-center gap-4">
                <span className="text-gray-700">Welcome, {user.username}!</span>
                <button
                  onClick={handleLogout}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
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
          <div className="bg-white rounded-lg shadow-md p-8 text-center">
            <h2 className="text-3xl font-bold text-gray-800 mb-4">Expense Tracker</h2>
            <p className="text-gray-600 mb-6">
              Track your expenses easily. Please login or register to get started.
            </p>
            <div className="flex gap-4 justify-center">
              <button
                onClick={() => setShowLogin(true)}
                className="px-6 py-3 text-rose-600 border border-rose-600 rounded-md hover:bg-rose-50"
              >
                Login
              </button>
              <button
                onClick={() => setShowRegister(true)}
                className="px-6 py-3 bg-rose-600 text-white rounded-md hover:bg-rose-700"
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
