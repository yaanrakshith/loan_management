from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from decimal import Decimal

from .models import Loan, Installment, LoanHistory
from .serializers import (
    LoanCreateSerializer,
    LoanDetailSerializer,
    LoanListSerializer,
    ForeclosureSerializer,
    LoanPaymentSerializer
)
from .services import calculate_foreclosure_amount
from authentication.models import User
from django.utils import timezone

class IsAdminOrOwner(permissions.BasePermission):
    """
    Custom permission to only allow admins or owners of a loan.
    """

    def has_object_permission(self, request, view, obj):
        # Allow if user is admin
        if request.user.is_admin:
            return True

        # Check if the user is the owner
        return obj.user == request.user


class LoanListCreateView(APIView):
    def get(self, request):
        if request.user.is_admin:
            # Admins can see all loans
            loans = Loan.objects.all()
        else:
            # Regular users can only see their own loans
            loans = Loan.objects.filter(user=request.user)

        serializer = LoanListSerializer(loans, many=True)
        return Response({
            "status": "success",
            "data": {
                "loans": serializer.data
            }
        })

    def post(self, request):
        serializer = LoanCreateSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            loan = serializer.save()

            # Create response with payment schedule
            payment_schedule = []
            for installment in loan.installments.all():
                payment_schedule.append({
                    'installment_no': installment.installment_number,
                    'due_date': installment.due_date.strftime('%Y-%m-%d'),
                    'amount': float(installment.amount)
                })

            return Response({
                "status": "success",
                "data": {
                    "loan_id": loan.loan_id,
                    "amount": float(loan.amount),
                    "tenure": loan.tenure,
                    "interest_rate": f"{loan.interest_rate}% yearly",
                    "monthly_installment": float(loan.monthly_installment),
                    "total_interest": float(loan.total_interest),
                    "total_amount": float(loan.total_amount),
                    "payment_schedule": payment_schedule
                }
            }, status=status.HTTP_201_CREATED)

        return Response({
            "status": "error",
            "message": "Failed to create loan",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LoanDetailView(APIView):
    permission_classes = [IsAdminOrOwner]

    def get_object(self, loan_id):
        loan = get_object_or_404(Loan, loan_id=loan_id)
        self.check_object_permissions(self.request, loan)
        return loan

    def get(self, request, loan_id):
        loan = self.get_object(loan_id)
        serializer = LoanDetailSerializer(loan)
        return Response({
            "status": "success",
            "data": serializer.data
        })

    def delete(self, request, loan_id):
        if not request.user.is_admin:
            return Response({
                "status": "error",
                "message": "Only admins can delete loan records"
            }, status=status.HTTP_403_FORBIDDEN)

        loan = self.get_object(loan_id)

        # Create history record before deletion
        LoanHistory.objects.create(
            loan=loan,
            action='STATUS_CHANGE',
            details={
                'previous_status': loan.status,
                'new_status': 'DELETED',
                'reason': 'Admin deletion'
            },
            performed_by=request.user
        )

        loan.delete()
        return Response({
            "status": "success",
            "message": "Loan deleted successfully"
        }, status=status.HTTP_200_OK)


class LoanForeclosureView(APIView):
    permission_classes = [IsAdminOrOwner]

    def post(self, request, loan_id):
        serializer = ForeclosureSerializer(data={'loan_id': loan_id})
        if serializer.is_valid():
            loan = get_object_or_404(Loan, loan_id=loan_id)
            self.check_object_permissions(request, loan)

            # Calculate foreclosure details
            foreclosure_details = calculate_foreclosure_amount(loan)

            # Update loan status and amounts
            loan.status = 'CLOSED'
            loan.amount_paid = loan.total_amount - \
                Decimal(str(foreclosure_details['foreclosure_discount']))
            loan.amount_remaining = 0
            loan.save()

            # Update installments
            pending_installments = loan.installments.filter(status='PENDING')
            pending_installments.update(
                status='PAID', payment_date=loan.updated_at.date())

            # Create history record
            LoanHistory.objects.create(
                loan=loan,
                action='FORECLOSURE',
                details={
                    'foreclosure_amount': foreclosure_details['foreclosure_amount'],
                    'foreclosure_discount': foreclosure_details['foreclosure_discount'],
                    'final_settlement_amount': foreclosure_details['final_settlement_amount']
                },
                performed_by=request.user
            )

            return Response({
                "status": "success",
                "message": "Loan foreclosed successfully.",
                "data": {
                    "loan_id": loan.loan_id,
                    "amount_paid": float(loan.amount_paid),
                    "foreclosure_discount": foreclosure_details['foreclosure_discount'],
                    "final_settlement_amount": foreclosure_details['final_settlement_amount'],
                    "status": loan.status
                }
            }, status=status.HTTP_200_OK)

        return Response({
            "status": "error",
            "message": "Failed to foreclose loan",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# views.py - add this class
class LoanPaymentView(APIView):
    permission_classes = [IsAdminOrOwner]

    def post(self, request, loan_id):
        serializer = LoanPaymentSerializer(
            data={'loan_id': loan_id, 'amount': request.data.get('amount')})
        if serializer.is_valid():
            loan = get_object_or_404(Loan, loan_id=loan_id)
            self.check_object_permissions(request, loan)

            payment_amount = Decimal(str(serializer.validated_data['amount']))

            # Find the next pending installment
            next_installment = loan.installments.filter(
                status='PENDING').order_by('due_date').first()

            if not next_installment:
                return Response({
                    "status": "error",
                    "message": "No pending installments found for this loan."
                }, status=status.HTTP_400_BAD_REQUEST)

            # Update the installment status
            if payment_amount >= next_installment.amount:
                next_installment.status = 'PAID'
                next_installment.payment_date = timezone.now().date()
                next_installment.save()

                # Update loan details
                loan.amount_paid += next_installment.amount
                loan.amount_remaining -= next_installment.amount

                # Update next due date
                next_pending = loan.installments.filter(
                    status='PENDING').order_by('due_date').first()
                if next_pending:
                    loan.next_due_date = next_pending.due_date
                else:
                    # All installments paid, close the loan
                    loan.status = 'CLOSED'
                    loan.next_due_date = None

                loan.save()

                # Create history record
                LoanHistory.objects.create(
                    loan=loan,
                    action='PAYMENT',
                    details={
                        'installment_number': next_installment.installment_number,
                        'amount': float(next_installment.amount),
                        'payment_date': next_installment.payment_date.strftime('%Y-%m-%d')
                    },
                    performed_by=request.user
                )

                # Handle excess payment
                excess = payment_amount - next_installment.amount
                if excess > 0 and loan.status == 'ACTIVE':
                    return Response({
                        "status": "partial_success",
                        "message": f"Payment successful. You have paid ₹{float(next_installment.amount)} for installment #{next_installment.installment_number}. You have an excess payment of ₹{float(excess)}. Please make a separate payment for the next installment.",
                        "data": {
                            "loan_id": loan.loan_id,
                            "installment_paid": next_installment.installment_number,
                            "amount_paid": float(next_installment.amount),
                            "excess_amount": float(excess),
                            "loan_status": loan.status
                        }
                    })

                return Response({
                    "status": "success",
                    "message": f"Payment successful for installment #{next_installment.installment_number}.",
                    "data": {
                        "loan_id": loan.loan_id,
                        "installment_paid": next_installment.installment_number,
                        "amount_paid": float(next_installment.amount),
                        "next_due_date": loan.next_due_date.strftime('%Y-%m-%d') if loan.next_due_date else None,
                        "loan_status": loan.status
                    }
                })
            else:
                # Partial payment not supported in this implementation
                return Response({
                    "status": "error",
                    "message": f"Payment amount (₹{float(payment_amount)}) is less than the required installment amount (₹{float(next_installment.amount)}). Please pay the full installment amount."
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "status": "error",
            "message": "Failed to process payment",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
