from django.contrib import admin
from .models import AccountType, BankAccount, Transaction


@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ("id", "account_number", "balance", "account_type", "owner", "is_active", "created_at")
    list_filter = ("is_active", "account_type")
    search_fields = ("account_number",)
    raw_id_fields = ("owner",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "account", "amount", "transaction_type", "created_at")
    list_filter = ("transaction_type",)
