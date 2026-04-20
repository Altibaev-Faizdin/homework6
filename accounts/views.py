from collections import OrderedDict
from django.core.cache import cache
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from common.permissions import IsAnonymous, IsOwner, IsModerator, IsOwnerOrModerator
from common.validators import validate_user_age_from_token

from .models import AccountType, BankAccount, Transaction
from .serializers import (
    AccountTypeSerializer,
    AccountTypeValidateSerializer,
    BankAccountSerializer,
    BankAccountValidateSerializer,
    BankAccountWithTransactionsSerializer,
    TransactionSerializer,
    TransactionValidateSerializer,
)

PAGE_SIZE = 5

class CustomPagination(PageNumberPagination):
    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("total", self.page.paginator.count),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                ]
            )
        )

    def get_page_size(self, request):
        return PAGE_SIZE


class AccountTypeListCreateAPIView(ListCreateAPIView):
    queryset = AccountType.objects.all()
    serializer_class = AccountTypeSerializer
    pagination_class = CustomPagination

    def post(self, request, *args, **kwargs):
        serializer = AccountTypeValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        account_type = AccountType.objects.create(**serializer.validated_data)
        return Response(
            data=AccountTypeSerializer(account_type).data, status=status.HTTP_201_CREATED
        )


class AccountTypeDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = AccountType.objects.all()
    serializer_class = AccountTypeSerializer
    lookup_field = "id"

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = AccountTypeValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        instance.name = serializer.validated_data.get("name")
        instance.save()

        return Response(data=AccountTypeSerializer(instance).data)


class BankAccountListCreateAPIView(ListCreateAPIView):
    queryset = BankAccount.objects.select_related("account_type").all()
    serializer_class = BankAccountSerializer
    pagination_class = CustomPagination
    permission_classes = [IsOwnerOrModerator]

    def get(self, request, *args, **kwargs):
        cached_data = cache.get("bank_account_list")
        if cached_data:
            print("Redis cache")
            return Response(data=cached_data, status=status.HTTP_200_OK)
        response = super().get(self, request, *args, **kwargs)
        print("Postgres data")
        if response.data.get("total", 0) > 0:
            cache.set("bank_account_list", response.data, timeout=300)
        return response

    def post(self, request, *args, **kwargs):
        validate_user_age_from_token(request)

        serializer = BankAccountValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        print("email: ", request.auth.get("email"))
        print("call_me: ", request.auth.get("call_me"))

        account_number = serializer.validated_data.get("account_number")
        balance = serializer.validated_data.get("balance")
        account_type = serializer.validated_data.get("account_type")

        bank_account = BankAccount.objects.create(
            account_number=account_number,
            balance=balance,
            account_type=account_type,
            owner=request.user,
        )

        return Response(
            data=BankAccountSerializer(bank_account).data, status=status.HTTP_201_CREATED
        )


class BankAccountDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = BankAccount.objects.select_related("account_type").all()
    serializer_class = BankAccountSerializer
    lookup_field = "id"
    permission_classes = [IsOwnerOrModerator]

    def put(self, request, *args, **kwargs):
        bank_account = self.get_object()
        serializer = BankAccountValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        bank_account.account_number = serializer.validated_data.get("account_number")
        bank_account.balance = serializer.validated_data.get("balance")
        bank_account.account_type = serializer.validated_data.get("account_type")
        bank_account.save()

        return Response(data=BankAccountSerializer(bank_account).data)


class TransactionViewSet(ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    pagination_class = CustomPagination
    lookup_field = "id"

    def create(self, request, *args, **kwargs):
        serializer = TransactionValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data.get("amount")
        description = serializer.validated_data.get("description")
        account = serializer.validated_data.get("account")
        transaction_type = serializer.validated_data.get("transaction_type")

        transaction = Transaction.objects.create(
            amount=amount,
            description=description,
            account=account,
            transaction_type=transaction_type,
        )

        return Response(
            data=TransactionSerializer(transaction).data, status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        transaction = self.get_object()
        serializer = TransactionValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        transaction.amount = serializer.validated_data.get("amount")
        transaction.description = serializer.validated_data.get("description")
        transaction.account = serializer.validated_data.get("account")
        transaction.transaction_type = serializer.validated_data.get("transaction_type")
        transaction.save()

        return Response(data=TransactionSerializer(transaction).data)


class BankAccountWithTransactionsAPIView(APIView):
    def get(self, request):
        paginator = CustomPagination()
        accounts = (
            BankAccount.objects.select_related("account_type").prefetch_related("transactions").all()
        )
        result_page = paginator.paginate_queryset(accounts, request)

        serializer = BankAccountWithTransactionsSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
