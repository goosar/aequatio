export default function Header(){
  return (
    <header className="bg-gradient-to-r from-indigo-600 via-sky-500 to-cyan-400 text-white shadow-md">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-white/20 p-2 rounded-md">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L15 8H9L12 2Z" fill="white" opacity="0.9"/></svg>
          </div>
          <h1 className="text-2xl font-extrabold tracking-tight">Equation</h1>
        </div>
        <nav className="space-x-6 text-sm opacity-95">
          <a className="hover:underline" href="#">Home</a>
          <a className="hover:underline" href="#groups">Groups</a>
          <a className="hover:underline" href="#expenses">Expenses</a>
        </nav>
      </div>
    </header>
  )
}
