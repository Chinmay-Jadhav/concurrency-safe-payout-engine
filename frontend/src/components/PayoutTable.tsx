import type { Payout } from '../types'

const statusColor: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  processing: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
}

export default function PayoutTable({ payouts }: { payouts: Payout[] }) {
  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Payout History</h3>
      {payouts.length === 0 ? (
        <p className="text-gray-400">No payouts yet</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500 border-b">
              <th className="pb-2">ID</th>
              <th className="pb-2">Amount</th>
              <th className="pb-2">Status</th>
              <th className="pb-2">Attempts</th>
              <th className="pb-2">Created</th>
            </tr>
          </thead>
          <tbody>
            {payouts.map(p => (
              <tr key={p.id} className="border-b last:border-0">
                <td className="py-2">#{p.id}</td>
                <td className="py-2">₹{(p.amount_paise / 100).toFixed(2)}</td>
                <td className="py-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColor[p.status]}`}>
                    {p.status}
                  </span>
                </td>
                <td className="py-2">{p.attempt_count}</td>
                <td className="py-2 text-gray-400">
                  {new Date(p.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}