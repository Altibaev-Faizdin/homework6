from django.db import models

from users.models import CustomUser
from common.models import BaseModel


class AccountType(BaseModel):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Account Type"
        verbose_name_plural = "Account Types"


class BankAccount(BaseModel):
    account_number = models.CharField(max_length=20, unique=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    account_type = models.ForeignKey(AccountType, on_delete=models.CASCADE)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return self.account_number

    class Meta:
        verbose_name = "Bank Account"
        verbose_name_plural = "Bank Accounts"


TRANSACTION_TYPES = (
    (i, t)
    for i, t in enumerate(["deposit", "withdrawal", "transfer"], start=1)
)


class Transaction(models.Model):
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(null=True, blank=True)
    account = models.ForeignKey(
        BankAccount, on_delete=models.CASCADE, related_name="transactions"
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=[
            ("deposit", "Deposit"),
            ("withdrawal", "Withdrawal"),
            ("transfer", "Transfer"),
        ],
        default="deposit",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount}"

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
