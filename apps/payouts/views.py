from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.merchants.models import Merchant
from .services import create_payout, InsufficientFundsError
from .models import Payout

class PayoutCreateView(APIView):
    def post(self, request):
        idempotency_key = request.headers.get('Idempotency-Key')
        if not idempotency_key:
            return Response({'error': 'Idempotency-Key header required'}, status=400)

        amount_paise = request.data.get('amount_paise')
        bank_account_id = request.data.get('bank_account_id')

        # TODO: replace with real auth
        merchant = Merchant.objects.first()

        try:
            response = create_payout(merchant, amount_paise, bank_account_id, idempotency_key)
            return Response(response, status=status.HTTP_201_CREATED)
        except InsufficientFundsError as e:
            return Response({'error': str(e)}, status=400)

class PayoutListView(APIView):
    def get(self, request):
        merchant = Merchant.objects.first()
        payouts = Payout.objects.filter(merchant=merchant).order_by('-created_at')[:50]
        data = [
            {
                'id': p.id,
                'amount_paise': p.amount_paise,
                'status': p.status,
                'attempt_count': p.attempt_count,
                'created_at': p.created_at.isoformat(),
            }
            for p in payouts
        ]
        return Response(data)