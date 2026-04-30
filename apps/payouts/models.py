from django.db import models
from django.utils import timezone

class Payout(models.Model):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
    ]

    merchant = models.ForeignKey(
        'merchants.Merchant',
        on_delete=models.PROTECT,
        related_name='payouts'
    )
    bank_account = models.ForeignKey(
        'merchants.BankAccount',
        on_delete=models.PROTECT
    )
    amount_paise = models.BigIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    attempt_count = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    idempotency_key = models.CharField(max_length=255, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('merchant', 'idempotency_key')

class IdempotencyKey(models.Model):
    merchant = models.ForeignKey(
        'merchants.Merchant',
        on_delete=models.CASCADE
    )
    key = models.CharField(max_length=255)
    response_body = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('merchant', 'key')