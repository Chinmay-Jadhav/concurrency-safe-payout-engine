import threading
from django.test import TestCase
from apps.merchants.models import Merchant, BankAccount
from apps.ledger.services import add_credit
from apps.payouts.services import create_payout, InsufficientFundsError

class ConcurrencyTest(TestCase):
    def setUp(self):
        self.merchant = Merchant.objects.create(name='Test', email='t@t.com')
        self.bank = BankAccount.objects.create(
            merchant=self.merchant, account_number='111', ifsc='TEST0001'
        )
        add_credit(self.merchant.id, 10000)  # ₹100

    def test_two_concurrent_60_rupee_requests(self):
        results = []

        def attempt(key):
            try:
                create_payout(self.merchant, 6000, self.bank.id, key)
                results.append('success')
            except InsufficientFundsError:
                results.append('rejected')

        t1 = threading.Thread(target=attempt, args=('key-1',))
        t2 = threading.Thread(target=attempt, args=('key-2',))
        t1.start(); t2.start()
        t1.join(); t2.join()

        self.assertEqual(results.count('success'), 1)
        self.assertEqual(results.count('rejected'), 1)