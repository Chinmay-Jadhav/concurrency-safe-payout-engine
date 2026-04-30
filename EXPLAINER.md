1. The Ledger

Balance calculation query:

result = LedgerEntry.objects.filter(merchant_id=merchant_id).aggregate(
    total_credits=Sum('amount_paise', filter=Q(entry_type__in=['credit', 'release'])),
    total_debits=Sum('amount_paise', filter=Q(entry_type__in=['debit', 'hold']))
)
available_paise = (result['total_credits'] or 0) - (result['total_debits'] or 0)

Balance is never stored as a column. It is derived on every read fromLedgerEntry rows using a single DB-level aggregation. This means thereis no balance field that can drift out of sync with actual entries.

Credits and debits are modelled as separate entry types (credit, debit,hold, release) rather than signed integers because it makes the audittrail human-readable and makes partial queries (e.g. "show only holds")trivial. The invariant — sum(credits + releases) minus sum(debits + holds)equals displayed balance — is structurally guaranteed because the balanceIS that calculation, not a cached copy of it.

2. The Lock

Exact code that prevents overdraw:

with transaction.atomic():
    merchant_locked = Merchant.objects.select_for_update().get(pk=merchant.pk)
    balance = get_balance(merchant_locked.id)
    available = balance['available_paise']

    if available < amount_paise:
        raise InsufficientFundsError(...)

    payout = Payout.objects.create(...)
    add_hold(merchant_locked.id, amount_paise, payout)

The database primitive is PostgreSQL row-level locking via SELECT FOR UPDATE.

When two concurrent requests arrive for the same merchant, both hitselect_for_update(). PostgreSQL allows only one transaction to holdthe lock at a time. The second transaction blocks at this line untilthe first commits. By the time the second transaction reads the balance,the first transaction has already written the hold entry — so thebalance is already reduced. The second request sees insufficient fundsand is rejected cleanly.

This is database-level serialization, not Python-level. A threading.Lock()or in-process check would fail under multiple workers. SELECT FOR UPDATEworks correctly across multiple Celery workers, multiple Django processes,and multiple dynos.

3. The Idempotency

How the system recognises a seen key:

The IdempotencyKey model has a unique_together constraint on(merchant, key). On every payout request:

idem_obj, created = IdempotencyKey.objects.select_for_update().get_or_create(
    merchant=merchant,
    key=idempotency_key,
    defaults={'response_body': {}}
)
if not created:
    if age < 24 hours:
        return idem_obj.response_body

get_or_create is atomic on the unique constraint. If the row exists,created=False and we return the stored response immediately withouttouching the payout table.

In-flight race (two simultaneous first requests with the same key):

Both requests enter the transaction and call select_for_update() onthe IdempotencyKey row. The first one creates the row and proceeds. Thesecond one blocks on the lock, then sees created=False when the lockreleases, and returns the stored response. Only one payout is evercreated. Using select_for_update here instead of a bare get_or_createcloses the window where both requests could pass the existence checksimultaneously.

Keys expire after 24 hours — checked by comparing created_at totimezone.now().

4. The State Machine

Where failed-to-completed is blocked:

# apps/payouts/state_machine.py

LEGAL_TRANSITIONS = {
    'pending': ['processing'],
    'processing': ['completed', 'failed'],
}

def transition(payout, to_state: str):
    allowed = LEGAL_TRANSITIONS.get(payout.status, [])
    if to_state not in allowed:
        raise IllegalTransitionError(
            f'Transition {payout.status} → {to_state} is not allowed'
        )
    payout.status = to_state

failed is not a key in LEGAL_TRANSITIONS so LEGAL_TRANSITIONS.get('failed', [])returns an empty list. Any transition out of failed raises IllegalTransitionError.Same for completed. Nothing in the codebase sets payout.status directly —every status change goes through transition(). The fund release in thefailure path is atomic with the state transition because both happen insidethe same transaction.atomic() block in tasks.py.

5. The AI Audit

While generating the retry logic in tasks.py, the AI produced this:

# What AI gave
@shared_task
def retry_stuck_payouts():
    stuck = Payout.objects.filter(
        status=Payout.PROCESSING,
        locked_until__lt=timezone.now()
    )
    for payout in stuck:
        with transaction.atomic():
            if payout.attempt_count >= 3:
                payout.status = 'failed'
                payout.save()
                release_hold(...)

Three problems with this:

No select_for_update() on the queryset — two beat workers runningsimultaneously could pick up the same stuck payout and release fundstwice.

payout.status = 'failed' bypasses the state machine entirely.Direct assignment means illegal transitions are never caught here.

The queryset is evaluated before the per-row transactions open,so rows locked by an active worker are included. This causes thebeat task to attempt to process payouts that are legitimatelyin-flight.

What I replaced it with:

stuck = Payout.objects.filter(
    status=Payout.PROCESSING,
    locked_until__lt=now
).select_for_update(skip_locked=True)  # skip rows held by active workers

with transaction.atomic():
    for payout in stuck:
        if payout.attempt_count >= 3:
            transition(payout, 'failed')   # goes through state machine
            release_hold(...)
            payout.save(update_fields=['status', 'locked_until'])

skip_locked=True means rows being processed by an active worker areskipped entirely. transition() enforces the state machine. Theselect_for_update must be inside the transaction.atomic() block —locks are only held for the duration of the transaction.