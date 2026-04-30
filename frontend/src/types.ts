export interface Balance {
  merchant_id: number
  name: string
  available_paise: number
}

export interface LedgerEntry {
  id: number
  entry_type: 'credit' | 'debit' | 'hold' | 'release'
  amount_paise: number
  description: string
  created_at: string
}

export interface Payout {
  id: number
  amount_paise: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  attempt_count: number
  created_at: string
}