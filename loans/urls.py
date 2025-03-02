from django.urls import path
from .views import (
    LoanListCreateView,
    LoanDetailView,
    LoanForeclosureView,
    LoanPaymentView
)

urlpatterns = [
    path('loans/', LoanListCreateView.as_view(), name='loan-list-create'),
    path('loans/<str:loan_id>/', LoanDetailView.as_view(), name='loan-detail'),
    path('loans/<str:loan_id>/foreclose/',
         LoanForeclosureView.as_view(), name='loan-foreclose'),
    path('loans/<str:loan_id>/payment/', LoanPaymentView.as_view(),
         name='loan-payment'),  # New endpoint
]
