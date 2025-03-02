from rest_framework import serializers
from .models import Loan, Installment, LoanHistory
from .services import calculate_compound_interest_loan
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


class InstallmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Installment
        fields = (
            'id', 'installment_number', 'due_date', 'amount',
            'principal_component', 'interest_component',
            'payment_date', 'status'
        )
        read_only_fields = fields


class LoanCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ('amount', 'tenure', 'interest_rate')

    def validate_amount(self, value):
        # Check if amount is a number
        if not isinstance(value, (int, float, Decimal)):
            raise serializers.ValidationError(
                "Loan amount must be a number.")

        # Convert to Decimal for precise comparison
        amount = Decimal(str(value))

        # Validate minimum and maximum amounts
        if amount < Decimal('1000'):
            raise serializers.ValidationError(
                "Loan amount must be at least ₹1,000.")
        if amount > Decimal('100000'):
            raise serializers.ValidationError(
                "Loan amount cannot exceed ₹100,000.")
        return value

    def validate_tenure(self, value):
        # Check if tenure is a whole number
        if not isinstance(value, int) or value != int(value):
            raise serializers.ValidationError(
                "Loan tenure must be a whole number.")

        # Validate minimum and maximum tenure
        if value < 3:
            raise serializers.ValidationError(
                "Loan tenure must be at least 3 months.")
        if value > 24:
            raise serializers.ValidationError(
                "Loan tenure cannot exceed 24 months.")
        return value

    def validate_interest_rate(self, value):
        if value <= 0 or value > 50:  # Maximum 50% interest
            raise serializers.ValidationError(
                "Interest rate must be between 0.1 and 50%.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user

        # Calculate loan details
        loan_details = calculate_compound_interest_loan(
            principal=validated_data['amount'],
            tenure=validated_data['tenure'],
            yearly_interest_rate=validated_data['interest_rate']
        )

        # Create the loan object
        loan = Loan.objects.create(
            user=user,
            amount=validated_data['amount'],
            tenure=validated_data['tenure'],
            interest_rate=validated_data['interest_rate'],
            monthly_installment=loan_details['monthly_installment'],
            total_interest=loan_details['total_interest'],
            total_amount=loan_details['total_amount'],
            amount_remaining=loan_details['total_amount'],
            next_due_date=timezone.now().date() + timedelta(days=30)
        )

        # Create installment records
        for installment in loan_details['payment_schedule']:
            Installment.objects.create(
                loan=loan,
                installment_number=installment['installment_no'],
                due_date=installment['due_date'],
                amount=installment['amount'],
                principal_component=installment['principal_component'],
                interest_component=installment['interest_component']
            )

        # Create loan history record
        LoanHistory.objects.create(
            loan=loan,
            action='CREATED',
            details={
                'amount': float(validated_data['amount']),
                'tenure': validated_data['tenure'],
                'interest_rate': float(validated_data['interest_rate'])
            },
            performed_by=user
        )

        return loan


class LoanDetailSerializer(serializers.ModelSerializer):
    installments = InstallmentSerializer(many=True, read_only=True)

    class Meta:
        model = Loan
        fields = (
            'id', 'loan_id', 'amount', 'tenure', 'interest_rate',
            'monthly_installment', 'total_interest', 'total_amount',
            'amount_paid', 'amount_remaining', 'next_due_date', 'status',
            'created_at', 'installments'
        )
        read_only_fields = fields


class LoanListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = (
            'id', 'loan_id', 'amount', 'tenure', 'monthly_installment',
            'total_amount', 'amount_paid', 'amount_remaining',
            'next_due_date', 'status', 'created_at'
        )
        read_only_fields = fields


class ForeclosureSerializer(serializers.Serializer):
    loan_id = serializers.CharField()

    def validate_loan_id(self, value):
        try:
            loan = Loan.objects.get(loan_id=value)
            if loan.status != 'ACTIVE':
                raise serializers.ValidationError(
                    "Only active loans can be foreclosed.")
            return value
        except Loan.DoesNotExist:
            raise serializers.ValidationError("Loan not found.")

class LoanPaymentSerializer(serializers.Serializer):
    loan_id = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate_loan_id(self, value):
        try:
            loan = Loan.objects.get(loan_id=value)
            if loan.status != 'ACTIVE':
                raise serializers.ValidationError(
                    "Payment can only be made for active loans.")
            return value
        except Loan.DoesNotExist:
            raise serializers.ValidationError("Loan not found.")

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Payment amount must be greater than zero.")
        return value
