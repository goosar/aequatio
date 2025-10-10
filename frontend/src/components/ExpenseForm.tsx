import { useState } from 'react'

export default function ExpenseForm({onAdd}:{onAdd:(e:{id:string,desc:string,amount:number,payer:string})=>void}){
  const [desc,setDesc] = useState('')
  const [amount,setAmount] = useState('')
  const [payer,setPayer] = useState('Me')

  function add(){
    const a = parseFloat(amount)
    if(!desc||isNaN(a)) return
    onAdd({id:Math.random().toString(36).slice(2,9), desc, amount:a, payer})
    setDesc(''); setAmount('')
  }

  return (
    <div className="bg-white p-4 rounded-lg shadow-sm">
      <h4 className="font-medium mb-3">Add Expense</h4>
      <div className="grid gap-3">
        <input className="border px-3 py-2 rounded-md" placeholder="Description" value={desc} onChange={e=>setDesc(e.target.value)} />
        <div className="grid grid-cols-2 gap-2">
          <input className="border px-3 py-2 rounded-md" placeholder="Amount" value={amount} onChange={e=>setAmount(e.target.value)} />
          <input className="border px-3 py-2 rounded-md" placeholder="Payer" value={payer} onChange={e=>setPayer(e.target.value)} />
        </div>
        <div className="text-right">
          <button onClick={add} className="px-4 py-2 bg-rose-600 text-white rounded-md shadow">Add expense</button>
        </div>
      </div>
    </div>
  )
}
