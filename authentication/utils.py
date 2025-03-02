import random
import string
from datetime import timedelta
from django.utils import timezone
from .models import OTP

def generate_otp(length=6):
    """Generate a random OTP of specified length."""
    return ''.join(random.choices(string.digits, k=length))

def create_otp(user, expiry_minutes=10):
    """Create and save an OTP for a user."""
    # Invalidate existing OTPs
    OTP.objects.filter(user=user, is_used=False).update(is_used=True)
    
    # Create new OTP
    code = generate_otp()
    expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
    otp_obj = OTP.objects.create(
        user=user,
        code=code,
        expires_at=expires_at
    )
    
    return otp_obj