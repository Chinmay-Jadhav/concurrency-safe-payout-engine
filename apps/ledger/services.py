from django.db.models import Sum, Q
from .models import LedgerEntry

def get_balance(merchant_id: int) -> dict:
    result = LedgerEntry.objects.filter(merchant_id=merchant_id).aggregate(
        total_credits=Sum(
            'amount_paise',
            filter=Q(entry_type__in=['credit', 'release'])
        ),
        total_debits=Sum(
            'amount_paise',
            filter=Q(entry_type__in=['debit', 'hold'])
        )
    )
    credits = result['total_credits'] or 0
    debits = result['total_debits'] or 0
    return {
        'available_paise': credits - debits,
    }

def add_credit(merchant_id: int, amount_paise: int, description: str = '') -> LedgerEntry:
    return LedgerEntry.objects.create(
        merchant_id=merchant_id,
        entry_type=LedgerEntry.CREDIT,
        amount_paise=amount_paise,
        description=description
    )

def add_hold(merchant_id: int, amount_paise: int, payout) -> LedgerEntry:
    return LedgerEntry.objects.create(
        merchant_id=merchant_id,
        entry_type=LedgerEntry.HOLD,
        amount_paise=amount_paise,
        payout=payout,
        description=f'Hold for payout {payout.id}'
    )

def release_hold(merchant_id: int, amount_paise: int, payout) -> LedgerEntry:
    return LedgerEntry.objects.create(
        merchant_id=merchant_id,
        entry_type=LedgerEntry.RELEASE,
        amount_paise=amount_paise,
        payout=payout,
        description=f'Release hold for failed payout {payout.id}'
    )

def finalize_debit(merchant_id: int, amount_paise: int, payout) -> LedgerEntry:
    return LedgerEntry.objects.create(
        merchant_id=merchant_id,
        entry_type=LedgerEntry.DEBIT,
        amount_paise=amount_paise,
        payout=payout,
        description=f'Settled payout {payout.id}'
    )