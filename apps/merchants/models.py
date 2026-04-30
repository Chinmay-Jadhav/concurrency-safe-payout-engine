from django.db import models

class Merchant(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    # balance_paise is DERIVED — never written directly
    # it is always SUM(credits) - SUM(debits) from LedgerEntry
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class BankAccount(models.Model):
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name='bank_accounts')
    account_number = models.CharField(max_length=50)
    ifsc = models.CharField(max_length=20)
    is_primary = models.BooleanField(default=False)