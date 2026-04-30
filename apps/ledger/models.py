from django.db import models

class LedgerEntry(models.Model):
    CREDIT = 'credit'
    DEBIT = 'debit'
    HOLD = 'hold'
    RELEASE = 'release'

    ENTRY_TYPES = [
        (CREDIT, 'Credit'),
        (DEBIT, 'Debit'),
        (HOLD, 'Hold'),
        (RELEASE, 'Release'),
    ]

    merchant = models.ForeignKey(
        'merchants.Merchant',
        on_delete=models.PROTECT,
        related_name='ledger_entries'
    )
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPES)
    amount_paise = models.BigIntegerField()  # always positive
    payout = models.ForeignKey(
        'payouts.Payout',
        null=True, blank=True,
        on_delete=models.PROTECT,
        related_name='ledger_entries'
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']