from django.db import models
import uuid
from authentication.models import User
from django.utils import timezone
from datetime import timedelta


class Loan(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('CLOSED', 'Closed'),
        ('DEFAULTED', 'Defaulted'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan_id = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='loans')

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    tenure = models.IntegerField(help_text="Loan tenure in months")
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="Yearly interest rate in percentage")

    monthly_installment = models.DecimalField(max_digits=12, decimal_places=2)
    total_interest = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    amount_paid = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00)
    amount_remaining = models.DecimalField(max_digits=12, decimal_places=2)

    next_due_date = models.DateField()
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='ACTIVE')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.loan_id} - {self.user.email}"

    def save(self, *args, **kwargs):
        # Generate loan_id if it doesn't exist
        if not self.loan_id:
            last_loan = Loan.objects.order_by('-created_at').first()
            if last_loan and last_loan.loan_id.startswith('LOAN'):
                try:
                    num = int(last_loan.loan_id[4:]) + 1
                    self.loan_id = f"LOAN{num:03d}"
                except ValueError:
                    self.loan_id = "LOAN001"
            else:
                self.loan_id = "LOAN001"

        # Calculate next_due_date if not already set
        if not self.next_due_date:
            self.next_due_date = timezone.now().date() + timedelta(days=30)

        # Set amount_remaining if not already set
        if not self.amount_remaining:
            self.amount_remaining = self.total_amount

        super().save(*args, **kwargs)


class Installment(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan = models.ForeignKey(
        Loan, on_delete=models.CASCADE, related_name='installments')

    installment_number = models.IntegerField()
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    principal_component = models.DecimalField(max_digits=12, decimal_places=2)
    interest_component = models.DecimalField(max_digits=12, decimal_places=2)

    payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='PENDING')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['installment_number']
        unique_together = ['loan', 'installment_number']

    def __str__(self):
        return f"{self.loan.loan_id} - Installment {self.installment_number}"


class LoanHistory(models.Model):
    ACTION_CHOICES = (
        ('CREATED', 'Created'),
        ('PAYMENT', 'Payment'),
        ('FORECLOSURE', 'Foreclosure'),
        ('STATUS_CHANGE', 'Status Change'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan = models.ForeignKey(
        Loan, on_delete=models.CASCADE, related_name='history')

    action = models.CharField(max_length=15, choices=ACTION_CHOICES)
    details = models.JSONField()
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.loan.loan_id} - {self.action} at {self.created_at}"
