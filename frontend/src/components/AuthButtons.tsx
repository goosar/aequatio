export default function AuthButtons(){
  return (
    <div className="flex gap-3">
      <button className="px-4 py-2 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 shadow">Log in</button>
      <button className="px-4 py-2 border border-indigo-600 text-indigo-600 rounded-full hover:bg-indigo-50">Register</button>
    </div>
  )
}
