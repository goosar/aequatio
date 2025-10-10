import { useState } from 'react'

export default function ApiButton() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  async function callApi() {
    setLoading(true)
    setResult(null)
    try {
      const res = await fetch('http://127.0.0.1:8000/ping')
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
      const json = await res.json()
      setResult(JSON.stringify(json))
    } catch (err: any) {
      setResult(`Error: ${err.message ?? String(err)}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mt-6">
      <button onClick={callApi} disabled={loading} className="px-4 py-2 bg-indigo-600 text-white rounded-md shadow hover:bg-indigo-700 disabled:opacity-60">
        {loading ? 'Calling API...' : 'Call backend /ping'}
      </button>
      <div className="mt-3 bg-white p-3 rounded shadow-sm">
        <div className="text-sm font-medium text-gray-700">Response</div>
        <pre className="mt-2 text-xs text-gray-600 whitespace-pre-wrap">{result ?? '—'}</pre>
      </div>
    </div>
  )
}
