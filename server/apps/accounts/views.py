"""REST endpoints for registration, authentication, sessions, and settings."""

import logging

from django.contrib.auth import logout as django_logout
from django.db import IntegrityError
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.accounts import services
from apps.accounts.models import User, UserSettings
from apps.accounts.permissions import IsActiveAccount
from apps.accounts.serializers import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    GoogleLoginSerializer,
    LoginSerializer,
    OnboardingPatchSerializer,
    ProfileSerializer,
    RefreshTokenSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    SessionSerializer,
    SettingsSerializer,
)

logger = logging.getLogger(__name__)


def _success(data, message=""):
    return {"success": True, "data": data, "message": message}


def _failure(code, message, fields=None):
    return {
        "success": False,
        "error": {"code": code, "message": message, "fields": fields or {}},
    }


def _request_ip(request):
    return request.META.get("REMOTE_ADDR") or None


def _device_fields(request, device_label=""):
    return {
        "device_label": device_label,
        "user_agent": request.META.get("HTTP_USER_AGENT", "")[:400],
        "ip_address": _request_ip(request),
    }


def _user_summary(user):
    return {
        "public_id": str(user.public_id),
        "full_name": user.full_name,
        "display_name": user.display_name,
        "email": user.email,
        "phone": user.phone,
        "status": user.status,
    }


def _token_data(user, token_pair):
    return {**token_pair, "user": _user_summary(user)}


def _audit_request(user, action, request, *, entity_type="user", entity_id=None, metadata=None):
    services.record_audit(
        user,
        action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=_request_ip(request),
        metadata=metadata,
    )


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_register"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = services.create_account(serializer.validated_data)
            user.last_login = timezone.now()
            user.save(update_fields=("last_login",))
            token_pair = services.create_session(user, **_device_fields(request))
        except IntegrityError:
            logger.info("Registration rejected by a unique constraint")
            return Response(
                _failure("ACCOUNT_EXISTS", "An account with these details already exists."),
                status=status.HTTP_409_CONFLICT,
            )
        _audit_request(user, "register", request)
        return Response(
            _success(_token_data(user, token_pair), "Account created successfully."),
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.authenticate_credentials(
            serializer.validated_data["identifier"], serializer.validated_data["password"]
        )
        if user is None:
            return Response(
                _failure("INVALID_CREDENTIALS", "Email/phone or password is incorrect."),
                status=status.HTTP_401_UNAUTHORIZED,
                headers={"WWW-Authenticate": "Bearer"},
            )
        user.last_login = timezone.now()
        user.save(update_fields=("last_login",))
        token_pair = services.create_session(
            user, **_device_fields(request, serializer.validated_data.get("device_label", ""))
        )
        _audit_request(user, "login", request)
        return Response(_success(_token_data(user, token_pair), "Login successful."))


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_google"

    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        claims = services.verify_google_id_token(serializer.validated_data["id_token"])
        if claims is None:
            return Response(
                _failure("INVALID_GOOGLE_TOKEN", "Google could not verify this sign-in."),
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            user, created = services.google_login(claims)
        except (IntegrityError, ValueError):
            return Response(
                _failure("ACCOUNT_UNAVAILABLE", "This account is unavailable."),
                status=status.HTTP_403_FORBIDDEN,
            )
        user.last_login = timezone.now()
        user.save(update_fields=("last_login",))
        token_pair = services.create_session(
            user, **_device_fields(request, serializer.validated_data.get("device_label", ""))
        )
        _audit_request(user, "google_login", request, metadata={"created": created})
        return Response(_success(_token_data(user, token_pair), "Google sign-in successful."))


class RefreshView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_refresh"

    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.refresh_session(serializer.validated_data["refresh_token"])
        if result is None:
            return Response(
                _failure("INVALID_REFRESH_TOKEN", "Refresh token is invalid, expired, or revoked."),
                status=status.HTTP_401_UNAUTHORIZED,
            )
        user, token_pair = result
        return Response(_success(_token_data(user, token_pair), "Session refreshed."))


class LogoutView(APIView):
    permission_classes = [IsActiveAccount]

    def post(self, request):
        user = request.user
        session_handle = request.auth.get("sid") if isinstance(request.auth, dict) else None
        if session_handle:
            services.revoke_session_by_handle(user, session_handle)
        else:
            django_logout(request)
        _audit_request(user, "logout", request)
        return Response(_success({}, "Logged out."))


class MeView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request):
        return Response(_success(ProfileSerializer(request.user).data))


class ProfileView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request):
        return Response(_success(ProfileSerializer(request.user).data))

    def patch(self, request):
        serializer = ProfileSerializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            user = services.update_profile(request.user, serializer.validated_data)
        except IntegrityError:
            return Response(
                _failure("PHONE_IN_USE", "That phone number is already in use."),
                status=status.HTTP_409_CONFLICT,
            )
        _audit_request(user, "profile_update", request)
        return Response(_success(ProfileSerializer(user).data, "Profile updated."))


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_forgot_password"

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.request_password_reset(serializer.validated_data["email"])
        return Response(
            _success({}, "If an active account matches that email, a reset link has been sent.")
        )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_reset_password"

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not services.reset_password(
            serializer.validated_data["token"], serializer.validated_data["password"]
        ):
            return Response(
                _failure("INVALID_RESET_TOKEN", "This password reset link is invalid or expired."),
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(_success({}, "Password updated. Please sign in again."))


class ChangePasswordView(APIView):
    permission_classes = [IsActiveAccount]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        current_handle = request.auth.get("sid") if isinstance(request.auth, dict) else None
        updated = services.change_password(
            request.user,
            serializer.validated_data["current_password"],
            serializer.validated_data["new_password"],
            current_handle,
        )
        if not updated:
            return Response(
                _failure("INVALID_CURRENT_PASSWORD", "Current password is incorrect."),
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(_success({}, "Password updated."))


class SessionsView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request):
        current = request.auth.get("sid") if isinstance(request.auth, dict) else None
        data = services.list_user_sessions(request.user, current)
        return Response(_success(SessionSerializer(data, many=True).data))

    def delete(self, request):
        count = services.revoke_all_sessions(request.user)
        _audit_request(request.user, "sessions_revoke_all", request, metadata={"count": count})
        return Response(_success({"revoked": count}, "All sessions revoked."))


class SessionDetailView(APIView):
    permission_classes = [IsActiveAccount]

    def delete(self, request, public_id):
        revoked = services.revoke_session_by_handle(request.user, public_id)
        if not revoked:
            return Response(
                _failure("SESSION_NOT_FOUND", "Session not found."),
                status=status.HTTP_404_NOT_FOUND,
            )
        _audit_request(request.user, "session_revoke", request, metadata={"session_public_id": public_id})
        return Response(_success({}, "Session revoked."))


class SettingsView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request):
        settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
        return Response(_success(SettingsSerializer(settings_obj).data))

    def patch(self, request):
        serializer = SettingsSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            settings_obj = services.update_settings(request.user, serializer.validated_data)
        except ValueError as exc:
            return Response(
                _failure("INVALID_SETTING", str(exc)),
                status=status.HTTP_400_BAD_REQUEST,
            )
        _audit_request(request.user, "settings_update", request)
        return Response(_success(SettingsSerializer(settings_obj).data, "Settings updated."))


class OnboardingView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request):
        return Response(_success(services.onboarding_data(request.user)))

    def patch(self, request):
        serializer = OnboardingPatchSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            settings_obj = services.patch_onboarding(request.user, serializer.validated_data)
        except ValueError as exc:
            return Response(
                _failure("INVALID_ONBOARDING_DATA", str(exc)),
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = services.onboarding_data(request.user)
        _audit_request(request.user, "onboarding_update", request)
        return Response(_success(data, "Onboarding progress saved."))


class CompleteOnboardingView(APIView):
    permission_classes = [IsActiveAccount]

    def post(self, request):
        settings_obj = services.complete_onboarding(request.user)
        _audit_request(request.user, "onboarding_complete", request)
        return Response(
            _success(
                {"onboarding_step": settings_obj.onboarding_step,
                 "onboarding_completed_at": settings_obj.onboarding_completed_at},
                "Onboarding complete.",
            )
        )
