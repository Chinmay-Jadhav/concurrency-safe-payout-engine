from apps.merchants.models import Merchant, BankAccount
from apps.ledger.services import add_credit

m1 = Merchant.objects.create(name='Ravi Designs', email='ravi@example.com')
m2 = Merchant.objects.create(name='Priya Studio', email='priya@example.com')

BankAccount.objects.create(merchant=m1, account_number='1234567890', ifsc='HDFC0001234', is_primary=True)
BankAccount.objects.create(merchant=m2, account_number='0987654321', ifsc='ICIC0004321', is_primary=True)

add_credit(m1.id, 100000, 'Initial credit from client USD payment')  # ₹1000
add_credit(m1.id, 50000,  'Second payment')                          # ₹500
add_credit(m2.id, 75000,  'Client payment')                          # ₹750

from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json

schedule, _ = IntervalSchedule.objects.get_or_create(
    every=30,
    period=IntervalSchedule.SECONDS,
)

PeriodicTask.objects.get_or_create(
    name='Retry stuck payouts every 30s',
    defaults={
        'interval': schedule,
        'task': 'apps.payouts.tasks.retry_stuck_payouts',
        'args': json.dumps([]),
    }
)
print("Beat task registered")
exit()