from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import OTP

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name',
                  'role', 'password', 'is_verified', 'created_at')
        read_only_fields = ('id', 'is_verified', 'created_at')

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name',
                  'password', 'confirm_password')

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()

    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
            otp_obj = OTP.objects.filter(
                user=user,
                code=data['otp'],
                is_used=False,
                expires_at__gt=timezone.now()
            ).first()

            if not otp_obj:
                raise serializers.ValidationError("Invalid or expired OTP.")

            data['user'] = user
            data['otp_obj'] = otp_obj
            return data
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "User with this email does not exist.")


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
            if user.is_verified:
                raise serializers.ValidationError("User is already verified.")
            data['user'] = user
            return data
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "User with this email does not exist.")
