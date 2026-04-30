import type { LedgerEntry } from '../types'

const typeColor: Record<string, string> = {
  credit: 'text-green-600',
  debit: 'text-red-600',
  hold: 'text-yellow-600',
  release: 'text-blue-600',
}

export default function LedgerTable({ entries }: { entries: LedgerEntry[] }) {
  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Ledger</h3>
      {entries.length === 0 ? (
        <p className="text-gray-400">No entries</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500 border-b">
              <th className="pb-2">Type</th>
              <th className="pb-2">Amount</th>
              <th className="pb-2">Description</th>
              <th className="pb-2">Time</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(e => (
              <tr key={e.id} className="border-b last:border-0">
                <td className={`py-2 font-medium ${typeColor[e.entry_type]}`}>
                  {e.entry_type}
                </td>
                <td className="py-2">₹{(e.amount_paise / 100).toFixed(2)}</td>
                <td className="py-2 text-gray-500">{e.description}</td>
                <td className="py-2 text-gray-400">
                  {new Date(e.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}