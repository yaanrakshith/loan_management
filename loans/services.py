from datetime import date, timedelta
from decimal import Decimal
import math


def calculate_monthly_rate(yearly_rate):
    """Convert yearly interest rate to monthly rate."""
    return Decimal(str(yearly_rate)) / Decimal('12') / Decimal('100')


def calculate_compound_interest_loan(principal, tenure, yearly_interest_rate):
    """
    Calculate monthly installment, total interest, and total amount for a compound interest loan.

    Args:
        principal (Decimal): The loan amount
        tenure (int): The loan tenure in months
        yearly_interest_rate (Decimal): Yearly interest rate as a percentage

    Returns:
        dict: A dictionary containing loan calculation details
    """
    # Convert inputs to Decimal for precision
    principal = Decimal(str(principal))
    monthly_rate = calculate_monthly_rate(yearly_interest_rate)

    # Monthly installment formula for compound interest: P * r * (1 + r)^n / ((1 + r)^n - 1)
    numerator = principal * monthly_rate * \
        (Decimal('1') + monthly_rate) ** tenure
    denominator = (Decimal('1') + monthly_rate) ** tenure - Decimal('1')
    monthly_installment = numerator / denominator

    # Round to 2 decimal places
    monthly_installment = round(monthly_installment, 2)

    # Total amount to be paid
    total_amount = monthly_installment * tenure

    # Total interest
    total_interest = total_amount - principal

    # Generate payment schedule
    payment_schedule = []
    remaining_balance = principal
    current_date = date.today()

    for i in range(1, tenure + 1):
        due_date = (current_date + timedelta(days=30 * i))

        interest_for_month = remaining_balance * monthly_rate
        principal_for_month = monthly_installment - interest_for_month

        if i == tenure:
            # Adjust the last payment to account for rounding errors
            principal_for_month = remaining_balance
            monthly_installment = principal_for_month + interest_for_month

        payment_schedule.append({
            'installment_no': i,
            'due_date': due_date.strftime('%Y-%m-%d'),
            'amount': float(round(monthly_installment, 2)),
            'principal_component': float(round(principal_for_month, 2)),
            'interest_component': float(round(interest_for_month, 2)),
            'remaining_balance': float(round(remaining_balance - principal_for_month, 2))
        })

        remaining_balance -= principal_for_month

    return {
        'monthly_installment': float(monthly_installment),
        'total_interest': float(total_interest),
        'total_amount': float(total_amount),
        'payment_schedule': payment_schedule
    }


def calculate_foreclosure_amount(loan, foreclosure_date=None):
    """
    Calculate foreclosure amount including any applicable discount.

    Args:
        loan: The loan object
        foreclosure_date: The date of foreclosure (defaults to today)

    Returns:
        dict: A dictionary containing foreclosure details
    """
    if foreclosure_date is None:
        foreclosure_date = date.today()

    # Calculate number of installments paid
    paid_installments = loan.installments.filter(status='PAID').count()

    # Get remaining installments
    remaining_installments = loan.installments.filter(
        status='PENDING').order_by('due_date')

    if not remaining_installments.exists():
        return {
            'foreclosure_amount': 0,
            'foreclosure_discount': 0,
            'final_settlement_amount': 0
        }

    # Calculate total remaining principal
    total_remaining_principal = sum(
        inst.principal_component for inst in remaining_installments)

    # Calculate total remaining interest
    total_remaining_interest = sum(
        inst.interest_component for inst in remaining_installments)

    # Apply discount (for example, 10% discount on remaining interest)
    foreclosure_discount = Decimal(
        round(float(total_remaining_interest) * 0.10, 2))

    # Final settlement amount
    final_settlement_amount = total_remaining_principal + \
        total_remaining_interest - foreclosure_discount

    return {
        'foreclosure_amount': float(total_remaining_principal + total_remaining_interest),
        'foreclosure_discount': float(foreclosure_discount),
        'final_settlement_amount': float(final_settlement_amount)
    }
