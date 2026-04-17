from django.urls import path, include
from .views import (
    AccountTypeListCreateAPIView,
    AccountTypeDetailAPIView,
    BankAccountListCreateAPIView,
    BankAccountDetailAPIView,
    TransactionViewSet,
    BankAccountWithTransactionsAPIView,
)

urlpatterns = [
    path('', BankAccountListCreateAPIView.as_view()),
    path('<int:id>/', BankAccountDetailAPIView.as_view()),
    path('types/', AccountTypeListCreateAPIView.as_view()),
    path('types/<int:id>/', AccountTypeDetailAPIView.as_view()),
    path('with-transactions/', BankAccountWithTransactionsAPIView.as_view()),
]
