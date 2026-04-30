import random
import time
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from .models import Payout
from .state_machine import transition, IllegalTransitionError
from apps.ledger.services import release_hold, finalize_debit

@shared_task(bind=True, max_retries=3)
def process_payout(self, payout_id: int):
    try:
        with transaction.atomic():
            payout = Payout.objects.select_for_update().get(id=payout_id)

            if payout.status != Payout.PENDING:
                return  # already processed

            transition(payout, 'processing')
            payout.attempt_count += 1
            payout.locked_until = timezone.now() + timedelta(seconds=60)
            payout.save(update_fields=['status', 'attempt_count', 'locked_until'])

        # Simulate bank call OUTSIDE the transaction
        # We don't hold the DB lock while waiting for network
        outcome = random.choices(
            ['success', 'failure', 'processing'],
            weights=[70, 20, 10]
        )[0]

        with transaction.atomic():
            payout = Payout.objects.select_for_update().get(id=payout_id)

            if outcome == 'success':
                with transaction.atomic():
                    payout = Payout.objects.select_for_update().get(id=payout_id)
                    transition(payout, 'completed')
                    release_hold(payout.merchant_id, payout.amount_paise, payout)  # cancel the hold
                    finalize_debit(payout.merchant_id, payout.amount_paise, payout)  # final debit
                    payout.locked_until = None
                    payout.save(update_fields=['status', 'locked_until'])

            elif outcome == 'failure':
                transition(payout, 'failed')
                release_hold(payout.merchant_id, payout.amount_paise, payout)
                payout.locked_until = None
                payout.save(update_fields=['status', 'locked_until'])

            # outcome == 'processing': stays in processing, retry_stuck_payouts picks it up

    except IllegalTransitionError:
        pass  # another worker already moved this payout


@shared_task
def retry_stuck_payouts():
    """
    Runs every 30 seconds via Celery beat.
    Finds payouts stuck in processing past locked_until.
    Max 3 attempts then fail and release funds.
    """
    now = timezone.now()
    stuck = Payout.objects.filter(
        status=Payout.PROCESSING,
        locked_until__lt=now
    ).select_for_update(skip_locked=True)  # skip rows locked by active workers

    with transaction.atomic():
        for payout in stuck:
            if payout.attempt_count >= 3:
                transition(payout, 'failed')
                release_hold(payout.merchant_id, payout.amount_paise, payout)
                payout.locked_until = None
                payout.save(update_fields=['status', 'locked_until'])
            else:
                # reset to pending so process_payout can pick it up
                payout.status = Payout.PENDING
                payout.locked_until = None
                payout.save(update_fields=['status', 'locked_until'])
                process_payout.apply_async(
                    args=[payout.id],
                    countdown=2 ** payout.attempt_count  # exponential backoff
                )