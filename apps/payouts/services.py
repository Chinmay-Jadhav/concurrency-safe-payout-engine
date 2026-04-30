from django.db import transaction
from django.utils import timezone
from apps.ledger.services import get_balance, add_hold
from apps.ledger.models import LedgerEntry
from .models import Payout, IdempotencyKey
from .state_machine import transition

class InsufficientFundsError(Exception):
    pass

class DuplicateIdempotencyError(Exception):
    """Raised internally when key already exists — caller returns stored response."""
    def __init__(self, stored_response):
        self.stored_response = stored_response

def create_payout(merchant, amount_paise: int, bank_account_id: int, idempotency_key: str) -> dict:
    """
    Steps inside a single transaction:
    1. Lock the IdempotencyKey row (or create it)
    2. SELECT FOR UPDATE on Merchant row — serializes concurrent requests
    3. Compute balance from ledger (DB aggregation, not Python fetch)
    4. Check sufficiency
    5. Create Payout in pending
    6. Create HOLD ledger entry
    7. Store idempotency response
    8. Enqueue Celery task
    """
    from .tasks import process_payout  # avoid circular import at module level

    with transaction.atomic():
        # Step 1: idempotency check inside the lock
        # get_or_create is atomic on the unique_together constraint
        idem_obj, created = IdempotencyKey.objects.select_for_update().get_or_create(
            merchant=merchant,
            key=idempotency_key,
            defaults={'response_body': {}}  # placeholder until we build response
        )

        if not created:
            # Key already exists — check if it's within 24h
            age = timezone.now() - idem_obj.created_at
            if age.total_seconds() < 86400:
                return idem_obj.response_body
            # expired — fall through and treat as new request
            idem_obj.delete()

        # Step 2: Lock merchant row
        # This is the database primitive that prevents overdraw.
        # SELECT FOR UPDATE acquires a row-level lock.
        # Any concurrent transaction trying to lock the same row
        # will block here until this transaction commits or rolls back.
        merchant_locked = merchant.__class__.objects.select_for_update().get(pk=merchant.pk)

        # Step 3: balance from DB aggregation
        balance = get_balance(merchant_locked.id)
        available = balance['available_paise']

        # Step 4: check
        if available < amount_paise:
            raise InsufficientFundsError(
                f'Available {available} paise, requested {amount_paise} paise'
            )

        # Step 5: create payout
        payout = Payout.objects.create(
            merchant=merchant_locked,
            bank_account_id=bank_account_id,
            amount_paise=amount_paise,
            status=Payout.PENDING,
            idempotency_key=idempotency_key,
        )

        # Step 6: hold funds
        add_hold(merchant_locked.id, amount_paise, payout)

        # Step 7: store response
        response = {
            'id': payout.id,
            'amount_paise': payout.amount_paise,
            'status': payout.status,
            'created_at': payout.created_at.isoformat(),
        }
        idem_obj.response_body = response
        idem_obj.save(update_fields=['response_body'])

    # Step 8: enqueue AFTER transaction commits
    # If enqueued inside the transaction, Celery might pick it up
    # before the commit, finding no payout row.
    process_payout.delay(payout.id)
    return response