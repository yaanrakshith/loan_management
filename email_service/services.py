from django.core.mail import send_mail
from django.conf import settings


def send_otp_email(email, name, otp):
    """Send OTP email to user."""
    subject = 'Verify Your Email - Loan Management System'
    message = f"""
    Hello {name},

    Thank you for registering with the Loan Management System. To verify your email, please use the following OTP:

    {otp}

    This OTP is valid for 10 minutes.

    If you did not register for an account, please ignore this email.

    Regards,
    Loan Management System Team
    """

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
    return True
