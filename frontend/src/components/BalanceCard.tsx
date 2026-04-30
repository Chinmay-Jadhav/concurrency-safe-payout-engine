import type { Balance } from '../types'

export default function BalanceCard({ balance }: { balance: Balance | null }) {
  if (!balance) return <div className="p-4 text-gray-400">Loading...</div>

  const toRupees = (paise: number) => (paise / 100).toFixed(2)

  return (
    <div className="bg-white rounded-xl shadow p-6">
      <p className="text-gray-500 text-sm">Merchant</p>
      <h2 className="text-xl font-bold mb-4">{balance.name}</h2>
      <div className="flex gap-8">
        <div>
          <p className="text-gray-500 text-sm">Available Balance</p>
          <p className="text-3xl font-bold text-green-600">
            ₹{toRupees(balance.available_paise)}
          </p>
        </div>
      </div>
    </div>
  )
}