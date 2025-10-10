import { useState } from 'react'

type Group = { id: string; name: string }

export default function GroupPanel({onSelect}:{onSelect:(g:Group)=>void}){
  const [groups, setGroups] = useState<Group[]>([])
  const [name, setName] = useState('')
  const [joinId, setJoinId] = useState('')

  function create(){
    if(!name) return
    const g = {id: Math.random().toString(36).slice(2,9), name}
    setGroups(s=>[...s,g])
    setName('')
  }

  function join(){
    if(!joinId) return
    const g = {id: joinId, name: `Group ${joinId}`}
    setGroups(s=>{ if(s.find(x=>x.id===g.id)) return s; return [...s,g] })
    setJoinId('')
  }

  return (
    <section id="groups" className="max-w-4xl mx-auto px-6 py-8">
      <h3 className="text-2xl font-semibold mb-4">Groups</h3>
      <div className="grid md:grid-cols-2 gap-4">
        <div className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition">
          <h4 className="font-medium mb-2">Create Group</h4>
          <div className="flex gap-2">
            <input value={name} onChange={e=>setName(e.target.value)} className="flex-1 border px-3 py-2 rounded" placeholder="Group name" />
            <button onClick={create} className="px-3 py-2 bg-cyan-600 text-white rounded">Create</button>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition">
          <h4 className="font-medium mb-2">Join Group</h4>
          <div className="flex gap-2">
            <input value={joinId} onChange={e=>setJoinId(e.target.value)} className="flex-1 border px-3 py-2 rounded" placeholder="Group id" />
            <button onClick={join} className="px-3 py-2 bg-emerald-600 text-white rounded">Join</button>
          </div>
        </div>
      </div>

      <div className="mt-6 grid md:grid-cols-3 gap-3">
        {groups.length===0 && <div className="text-gray-600">No groups yet</div>}
        {groups.map(g=> (
          <div key={g.id} className="p-3 bg-white rounded-lg shadow-sm hover:shadow-md flex items-center justify-between transition">
            <div>
              <div className="font-semibold">{g.name}</div>
              <div className="text-sm text-gray-500">id: {g.id}</div>
            </div>
            <div>
              <button onClick={()=>onSelect(g)} className="px-3 py-1 bg-indigo-600 text-white rounded-md">Open</button>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
