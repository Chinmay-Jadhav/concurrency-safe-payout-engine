from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Merchant
from apps.ledger.services import get_balance
from apps.ledger.models import LedgerEntry

class MerchantBalanceView(APIView):
    def get(self, request):
        merchant = Merchant.objects.first()
        balance = get_balance(merchant.id)
        return Response({
            'merchant_id': merchant.id,
            'name': merchant.name,
            **balance
        })

class LedgerEntriesView(APIView):
    def get(self, request):
        merchant = Merchant.objects.first()
        entries = LedgerEntry.objects.filter(merchant=merchant).order_by('-created_at')[:50]
        data = [
            {
                'id': e.id,
                'entry_type': e.entry_type,
                'amount_paise': e.amount_paise,
                'description': e.description,
                'created_at': e.created_at.isoformat(),
            }
            for e in entries
        ]
        return Response(data)