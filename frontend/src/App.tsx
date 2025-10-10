import { useState } from 'react'
import './App.css'
import Header from './components/Header'
import Landing from './components/Landing'
import GroupPanel from './components/GroupPanel'
import ExpenseForm from './components/ExpenseForm'
import ExpensesList from './components/ExpensesList'

type Group = { id: string; name: string }
type Expense = { id: string; desc: string; amount: number; payer: string }

function App(){
  const [selectedGroup, setSelectedGroup] = useState<Group | null>(null)
  const [expensesByGroup, setExpensesByGroup] = useState<Record<string,Expense[]>>({})

  function handleSelect(g: Group){
    setSelectedGroup(g)
  }

  function addExpense(e: Expense){
    if(!selectedGroup) return
    setExpensesByGroup(prev=>({
      ...prev,
      [selectedGroup.id]: [...(prev[selectedGroup.id]||[]), e]
    }))
  }

  const expenses = selectedGroup ? (expensesByGroup[selectedGroup.id]||[]) : []

  return (
    <div>
      <Header />
      <main className="bg-gray-50 min-h-screen">
        <Landing />
        <div className="max-w-4xl mx-auto px-6 py-6 grid md:grid-cols-2 gap-6">
          <GroupPanel onSelect={handleSelect} />
          <div id="expenses">
            <div className="bg-white p-4 rounded shadow">
              <h3 className="text-xl font-semibold">{selectedGroup? `Group: ${selectedGroup.name}` : 'No group selected'}</h3>
              {selectedGroup && (
                <>
                  <ExpenseForm onAdd={addExpense} />
                  <ExpensesList expenses={expenses} />
                </>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
