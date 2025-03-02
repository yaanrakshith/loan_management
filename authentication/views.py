from django.shortcuts import render

# Create your views here.
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone

from .models import User
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    VerifyOTPSerializer,
    ResendOTPSerializer
)
from .utils import create_otp
from email_service.services import send_otp_email


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Generate and send OTP
            otp_obj = create_otp(user)
            send_otp_email(user.email, user.first_name, otp_obj.code)

            return Response({
                "status": "success",
                "message": "User registered successfully. Please verify your email with the OTP sent.",
                "data": {
                    "user_id": user.id,
                    "email": user.email
                }
            }, status=status.HTTP_201_CREATED)

        return Response({
            "status": "error",
            "message": "Registration failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            otp_obj = serializer.validated_data['otp_obj']

            # Mark OTP as used
            otp_obj.is_used = True
            otp_obj.save()

            # Mark user as verified
            user.is_verified = True
            user.save()

            # Generate tokens
            refresh = RefreshToken.for_user(user)

            return Response({
                "status": "success",
                "message": "Email verified successfully",
                "data": {
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                    "user": UserSerializer(user).data
                }
            }, status=status.HTTP_200_OK)

        return Response({
            "status": "error",
            "message": "Verification failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ResendOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Generate and send new OTP
            otp_obj = create_otp(user)
            send_otp_email(user.email, user.first_name, otp_obj.code)

            return Response({
                "status": "success",
                "message": "OTP sent successfully",
                "data": {
                    "email": user.email
                }
            }, status=status.HTTP_200_OK)

        return Response({
            "status": "error",
            "message": "Failed to resend OTP",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            user = authenticate(email=email, password=password)

            if user is None:
                return Response({
                    "status": "error",
                    "message": "Invalid credentials"
                }, status=status.HTTP_401_UNAUTHORIZED)

            if not user.is_verified:
                return Response({
                    "status": "error",
                    "message": "Email not verified. Please verify your email first."
                }, status=status.HTTP_401_UNAUTHORIZED)

            refresh = RefreshToken.for_user(user)

            return Response({
                "status": "success",
                "message": "Login successful",
                "data": {
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                    "user": UserSerializer(user).data
                }
            }, status=status.HTTP_200_OK)

        return Response({
            "status": "error",
            "message": "Login failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({
            "status": "success",
            "data": serializer.data
        })

    def put(self, request):
        serializer = UserSerializer(
            request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "message": "Profile updated successfully",
                "data": serializer.data
            })

        return Response({
            "status": "error",
            "message": "Failed to update profile",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
