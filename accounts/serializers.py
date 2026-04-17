from rest_framework import serializers
from .models import AccountType, BankAccount, Transaction
from rest_framework.exceptions import ValidationError


class AccountTypeSerializer(serializers.ModelSerializer):
    accounts_count = serializers.SerializerMethodField()

    class Meta:
        model = AccountType
        fields = ['id', 'name', 'accounts_count']

    def get_accounts_count(self, account_type):
        return BankAccount.objects.filter(account_type=account_type).count()


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = '__all__'


class BankAccountWithTransactionsSerializer(serializers.ModelSerializer):
    total_transactions = serializers.SerializerMethodField()

    class Meta:
        model = BankAccount
        fields = ['id', 'account_number', 'balance', 'account_type', 'transactions', 'total_transactions']
        depth = 1

    def get_total_transactions(self, obj):
        return obj.transactions.count()


class AccountTypeValidateSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, min_length=2, max_length=100)


class BankAccountValidateSerializer(serializers.Serializer):
    account_number = serializers.CharField(required=True, min_length=8, max_length=20)
    balance = serializers.FloatField(min_value=0.0)
    account_type = serializers.IntegerField(min_value=1)

    def validate_account_number(self, value):
        if BankAccount.objects.filter(account_number=value).exists():
            raise ValidationError('Account number already exists')
        return value

    def validate_account_type(self, account_type_id):
        try:
            return AccountType.objects.get(id=account_type_id)
        except AccountType.DoesNotExist:
            raise ValidationError('Account type does not exist')


class TransactionValidateSerializer(serializers.Serializer):
    amount = serializers.FloatField(min_value=0.01)
    description = serializers.CharField(required=False, allow_blank=True)
    account = serializers.IntegerField(min_value=1)
    transaction_type = serializers.ChoiceField(
        choices=["deposit", "withdrawal", "transfer"]
    )

    def validate_account(self, account_id):
        try:
            return BankAccount.objects.get(id=account_id)
        except BankAccount.DoesNotExist:
            raise ValidationError('Bank account does not exist')
