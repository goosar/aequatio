import AuthButtons from './AuthButtons'

export default function Landing(){
  return (
    <section className="min-h-[60vh] flex items-center">
      <div className="max-w-6xl mx-auto px-6 py-12 grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
        <div>
          <h2 className="text-5xl font-extrabold mb-4">Welcome to Aequatio</h2>
          <p className="text-gray-700 mb-6 text-lg">Split expenses, track groups and settle up easily. Beautiful, minimal, and private-first.</p>
          <div className="flex items-center gap-4">
            <AuthButtons />
            <a href="#groups" className="px-4 py-2 bg-white text-indigo-600 rounded shadow hover:shadow-md">Get started</a>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-xl font-semibold mb-2">How it works</h3>
          <ol className="list-decimal list-inside text-gray-700 space-y-1">
            <li>Create or join a group</li>
            <li>Add expenses and assign payers</li>
            <li>See balances and settle up</li>
          </ol>
        </div>
      </div>
    </section>
  )
}
