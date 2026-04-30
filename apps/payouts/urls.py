from django.urls import path
from .views import PayoutCreateView, PayoutListView

urlpatterns = [
    path('payouts/', PayoutCreateView.as_view()),
    path('payouts/list/', PayoutListView.as_view()),
]