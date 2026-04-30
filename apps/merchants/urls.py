from django.urls import path
from .views import MerchantBalanceView, LedgerEntriesView

urlpatterns = [
    path('merchants/balance/', MerchantBalanceView.as_view()),
    path('merchants/ledger/', LedgerEntriesView.as_view()),
]