import { useState } from 'react'
import { api, generateIdempotencyKey } from '../api/client'

export default function PayoutForm({ onSuccess }: { onSuccess: () => void }) {
  const [amount, setAmount] = useState('')
  const [bankAccountId, setBankAccountId] = useState('1')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleSubmit = async () => {
    setError('')
    setSuccess('')
    setLoading(true)
    try {
      const res = await api.post(
        '/payouts/',
        {
          amount_paise: parseInt(amount),
          bank_account_id: parseInt(bankAccountId),
        },
        { headers: { 'Idempotency-Key': generateIdempotencyKey() } }
      )
      setSuccess(`Payout #${res.data.id} created — status: ${res.data.status}`)
      setAmount('')
      onSuccess()
    } catch (e: any) {
      setError(e.response?.data?.error || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Request Payout</h3>
      <div className="flex flex-col gap-3">
        <div>
          <label className="text-sm text-gray-500">Amount (paise)</label>
          <input
            type="number"
            value={amount}
            onChange={e => setAmount(e.target.value)}
            placeholder="e.g. 5000 = ₹50"
            className="w-full border rounded px-3 py-2 mt-1"
          />
          {amount && (
            <p className="text-xs text-gray-400 mt-1">
              = ₹{(parseInt(amount) / 100).toFixed(2)}
            </p>
          )}
        </div>
        <div>
          <label className="text-sm text-gray-500">Bank Account ID</label>
          <input
            type="number"
            value={bankAccountId}
            onChange={e => setBankAccountId(e.target.value)}
            className="w-full border rounded px-3 py-2 mt-1"
          />
        </div>
        {error && <p className="text-red-500 text-sm">{error}</p>}
        {success && <p className="text-green-500 text-sm">{success}</p>}
        <button
          onClick={handleSubmit}
          disabled={loading || !amount}
          className="bg-blue-600 text-white rounded px-4 py-2 hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Submitting...' : 'Submit Payout'}
        </button>
      </div>
    </div>
  )
}