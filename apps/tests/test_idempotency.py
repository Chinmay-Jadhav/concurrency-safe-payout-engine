from django.test import TestCase
from apps.merchants.models import Merchant, BankAccount
from apps.ledger.services import add_credit
from apps.payouts.services import create_payout

class IdempotencyTest(TestCase):
    def setUp(self):
        self.merchant = Merchant.objects.create(name='Test', email='t@t.com')
        self.bank = BankAccount.objects.create(
            merchant=self.merchant, account_number='111', ifsc='TEST0001'
        )
        add_credit(self.merchant.id, 100000)

    def test_same_key_returns_same_response(self):
        r1 = create_payout(self.merchant, 5000, self.bank.id, 'idem-key-abc')
        r2 = create_payout(self.merchant, 5000, self.bank.id, 'idem-key-abc')

        self.assertEqual(r1['id'], r2['id'])

        from apps.payouts.models import Payout
        count = Payout.objects.filter(
            merchant=self.merchant, idempotency_key='idem-key-abc'
        ).count()
        self.assertEqual(count, 1)