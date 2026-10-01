"""Authentication, account, session, and onboarding operations."""

import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core import signing
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.accounts.constants import (
    ACCESS_TOKEN_SALT,
)
from apps.accounts.models import (
    AuthSession,
    OAuthIdentity,
    PasswordResetToken,
    User,
    UserSettings,
)
from apps.audit.models import AuditLog
from apps.categories.models import Category, UserCategory
from apps.payments.models import UpiApp

_DUMMY_PASSWORD_HASH = make_password(secrets.token_urlsafe(24))


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def session_public_id(session_pk: int) -> str:
    """Return a stable opaque handle without exposing an auth_sessions.id."""
    message = f"student-finance.auth-session:{session_pk}".encode("ascii")
    return hmac.new(settings.SECRET_KEY.encode("utf-8"), message, hashlib.sha256).hexdigest()


def create_access_token(user: User, session: AuthSession) -> str:
    payload = {
        "sub": str(user.public_id),
        "sid": session_public_id(session.pk),
        "jti": secrets.token_urlsafe(12),
    }
    return signing.dumps(payload, salt=ACCESS_TOKEN_SALT, compress=True)


def _token_response(user: User, session: AuthSession, refresh_token: str) -> dict:
    return {
        "access_token": create_access_token(user, session),
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": settings.ACCESS_TOKEN_TTL_SECONDS,
        "session_public_id": session_public_id(session.pk),
    }


@transaction.atomic
def create_session(user: User, *, device_label: str = "", user_agent: str = "", ip_address: str | None = None) -> dict:
    refresh_token = secrets.token_urlsafe(48)
    now = timezone.now()
    session = AuthSession.objects.create(
        user=user,
        refresh_token_hash=_sha256(refresh_token),
        device_label=device_label or None,
        user_agent=user_agent[:400] or None,
        ip_address=ip_address or None,
        last_active_at=now,
        expires_at=now + timedelta(days=settings.REFRESH_SESSION_TTL_DAYS),
    )
    return _token_response(user, session, refresh_token)


def authenticate_credentials(identifier: str, password: str) -> User | None:
    normalized = identifier.strip()
    user = User.objects.filter(
        Q(email__iexact=normalized) | Q(phone=normalized)
    ).first()
    encoded = user.password if user and user.password else _DUMMY_PASSWORD_HASH
    valid = check_password(password, encoded)
    if not user or not valid or not user.is_active:
        return None
    return user


def authenticate_access_token(token: str) -> tuple[User, dict] | None:
    try:
        payload = signing.loads(
            token,
            salt=ACCESS_TOKEN_SALT,
            max_age=settings.ACCESS_TOKEN_TTL_SECONDS,
        )
    except signing.BadSignature:
        return None
    except signing.SignatureExpired:
        return None

    if not isinstance(payload, dict) or not payload.get("sub") or not payload.get("sid"):
        return None
    user = User.objects.filter(public_id=payload["sub"], status=User.Status.ACTIVE).first()
    if user is None:
        return None

    now = timezone.now()
    # The session table has no public UUID. Match our HMAC-derived handle across
    # this user's small session set so a revoked session invalidates access at once.
    sessions = AuthSession.objects.filter(
        user=user,
        revoked_at__isnull=True,
        expires_at__gt=now,
    ).only("id")
    if not any(
        hmac.compare_digest(session_public_id(item.pk), str(payload["sid"]))
        for item in sessions
    ):
        return None
    return user, payload


@transaction.atomic
def refresh_session(refresh_token: str) -> tuple[User, dict] | None:
    if not refresh_token:
        return None
    session = (
        AuthSession.objects.select_for_update()
        .select_related("user")
        .filter(refresh_token_hash=_sha256(refresh_token))
        .first()
    )
    now = timezone.now()
    if (
        session is None
        or session.revoked_at is not None
        or session.expires_at <= now
        or not session.user.is_active
    ):
        return None

    new_refresh_token = secrets.token_urlsafe(48)
    session.refresh_token_hash = _sha256(new_refresh_token)
    session.last_active_at = now
    session.save(update_fields=("refresh_token_hash", "last_active_at"))
    return session.user, _token_response(session.user, session, new_refresh_token)


def revoke_session_by_handle(user: User, public_id: str) -> bool:
    sessions = AuthSession.objects.filter(user=user, revoked_at__isnull=True).only("id")
    for session in sessions:
        if hmac.compare_digest(session_public_id(session.pk), public_id):
            return bool(
                AuthSession.objects.filter(pk=session.pk, revoked_at__isnull=True).update(
                    revoked_at=timezone.now()
                )
            )
    return False


def revoke_all_sessions(user: User, *, except_public_id: str | None = None) -> int:
    sessions = AuthSession.objects.filter(user=user, revoked_at__isnull=True).only("id")
    keep_pk = None
    if except_public_id:
        keep_pk = next(
            (
                item.pk
                for item in sessions
                if hmac.compare_digest(session_public_id(item.pk), except_public_id)
            ),
            None,
        )
    rows = AuthSession.objects.filter(user=user, revoked_at__isnull=True)
    if keep_pk is not None:
        rows = rows.exclude(pk=keep_pk)
    return rows.update(revoked_at=timezone.now())


def list_user_sessions(user: User, current_public_id: str | None = None) -> list[dict]:
    sessions = AuthSession.objects.filter(user=user).order_by("-last_active_at")
    return [
        {
            "public_id": session_public_id(item.pk),
            "device_label": item.device_label,
            "user_agent": item.user_agent,
            "ip_address": item.ip_address,
            "created_at": item.created_at,
            "last_active_at": item.last_active_at,
            "expires_at": item.expires_at,
            "revoked_at": item.revoked_at,
            "is_current": bool(
                current_public_id
                and hmac.compare_digest(session_public_id(item.pk), current_public_id)
            ),
        }
        for item in sessions
    ]


@transaction.atomic
def create_account(validated_data: dict) -> User:
    values = dict(validated_data)
    values.pop("confirm_password", None)
    password = values.pop("password")
    monthly_budget_paise = values.pop("monthly_budget_paise", None)
    user = User.objects.create_user(password=password, **values)
    UserSettings.objects.create(user=user, monthly_budget_paise=monthly_budget_paise)
    return user


@transaction.atomic
def update_profile(user: User, validated_data: dict) -> User:
    for field, value in validated_data.items():
        setattr(user, field, value)
    user.save(update_fields=tuple(validated_data.keys()) + ("updated_at",))
    return user


@transaction.atomic
def update_settings(user: User, values: dict) -> UserSettings:
    values = dict(values)
    category_was_supplied = "default_category_public_id" in values
    category_id = values.pop("default_category_public_id", None)
    upi_was_supplied = "preferred_upi_app_code" in values
    upi_code = values.pop("preferred_upi_app_code", None)
    settings_obj, _ = UserSettings.objects.get_or_create(user=user)

    if category_was_supplied:
        if category_id is None:
            settings_obj.default_category = None
        else:
            category = Category.objects.filter(public_id=category_id).filter(
                Q(user=user) | Q(user__isnull=True)
            ).first()
            if category is None:
                raise ValueError("The selected category is unavailable.")
            settings_obj.default_category = category

    if upi_was_supplied:
        if not upi_code:
            settings_obj.preferred_upi_app = None
        else:
            upi_app = UpiApp.objects.filter(code=upi_code, is_active=True).first()
            if upi_app is None:
                raise ValueError("The selected UPI app is unavailable.")
            settings_obj.preferred_upi_app = upi_app

    for field, value in values.items():
        setattr(settings_obj, field, value)
    settings_obj.save()
    return settings_obj


@transaction.atomic
def patch_onboarding(user: User, values: dict) -> UserSettings:
    values = dict(values)
    category_ids = values.pop("category_public_ids", None)
    step = values.pop("onboarding_step", None)
    if "display_name" in values:
        user.display_name = values.pop("display_name") or None
        user.save(update_fields=("display_name", "updated_at"))

    settings_obj, _ = UserSettings.objects.get_or_create(user=user)
    if "monthly_budget_paise" in values:
        settings_obj.monthly_budget_paise = values.pop("monthly_budget_paise")
    if category_ids is not None:
        selected = list(
            Category.objects.filter(public_id__in=category_ids)
            .filter(Q(user=user) | Q(user__isnull=True))
            .values_list("public_id", "id")
        )
        category_by_public_id = {str(public_id): category_id for public_id, category_id in selected}
        requested_ids = [str(public_id) for public_id in category_ids]
        if len(requested_ids) != len(set(requested_ids)):
            raise ValueError("A category can only be selected once.")
        if len(category_by_public_id) != len(requested_ids):
            raise ValueError("One or more selected categories are unavailable.")
        categories = [category_by_public_id[public_id] for public_id in requested_ids]
        UserCategory.objects.filter(user=user).delete()
        UserCategory.objects.bulk_create(
            [UserCategory(user=user, category_id=category_id, sort_order=position)
             for position, category_id in enumerate(categories)]
        )
    if step is not None:
        settings_obj.onboarding_step = step
    settings_obj.save()
    return settings_obj


@transaction.atomic
def complete_onboarding(user: User) -> UserSettings:
    settings_obj, _ = UserSettings.objects.get_or_create(user=user)
    settings_obj.onboarding_step = 4
    settings_obj.onboarding_completed_at = timezone.now()
    settings_obj.save()
    return settings_obj


def onboarding_data(user: User) -> dict:
    settings_obj, _ = UserSettings.objects.get_or_create(user=user)
    selected_categories = (
        UserCategory.objects.filter(user=user)
        .select_related("category")
        .order_by("sort_order")
    )
    return {
        "display_name": user.display_name,
        "monthly_budget_paise": settings_obj.monthly_budget_paise,
        "category_public_ids": [str(item.category.public_id) for item in selected_categories],
        "onboarding_step": settings_obj.onboarding_step,
        "onboarding_completed_at": settings_obj.onboarding_completed_at,
    }


def record_audit(
    user: User | None,
    action: str,
    *,
    entity_type: str | None = None,
    entity_id: int | None = None,
    ip_address: str | None = None,
    metadata: dict | None = None,
) -> None:
    AuditLog.objects.create(
        user=user,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        metadata=metadata or None,
    )


@transaction.atomic
def request_password_reset(email: str) -> None:
    user = User.objects.filter(email__iexact=email, status=User.Status.ACTIVE).first()
    if user is None:
        return
    now = timezone.now()
    PasswordResetToken.objects.filter(user=user, used_at__isnull=True).update(used_at=now)
    raw_token = secrets.token_urlsafe(32)
    PasswordResetToken.objects.create(
        user=user,
        token_hash=_sha256(raw_token),
        expires_at=now + timedelta(minutes=settings.PASSWORD_RESET_TTL_MINUTES),
    )
    reset_url = f"{settings.FRONTEND_PASSWORD_RESET_URL}?token={raw_token}"
    send_mail(
        "Reset your Student Finance password",
        f"Use this one-time link to reset your password: {reset_url}\n"
        f"The link expires in {settings.PASSWORD_RESET_TTL_MINUTES} minutes.",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
    record_audit(user, "password_reset_requested", entity_type="user", entity_id=user.pk)


@transaction.atomic
def reset_password(raw_token: str, new_password: str) -> bool:
    token = (
        PasswordResetToken.objects.select_for_update()
        .select_related("user")
        .filter(token_hash=_sha256(raw_token), used_at__isnull=True)
        .first()
    )
    now = timezone.now()
    if token is None or token.expires_at <= now or not token.user.is_active:
        return False
    token.user.set_password(new_password)
    token.user.save(update_fields=("password", "updated_at"))
    token.used_at = now
    token.save(update_fields=("used_at",))
    revoke_all_sessions(token.user)
    record_audit(token.user, "password_reset", entity_type="user", entity_id=token.user.pk)
    return True


@transaction.atomic
def change_password(user: User, current_password: str, new_password: str, current_session_handle: str | None) -> bool:
    if not user.password or not user.check_password(current_password):
        return False
    user.set_password(new_password)
    user.save(update_fields=("password", "updated_at"))
    revoke_all_sessions(user, except_public_id=current_session_handle)
    record_audit(user, "password_change", entity_type="user", entity_id=user.pk)
    return True


def verify_google_id_token(raw_token: str) -> dict | None:
    client_id = getattr(settings, "GOOGLE_CLIENT_ID", "")
    if not client_id:
        return None
    try:
        from google.auth.transport.requests import Request
        from google.oauth2 import id_token

        claims = id_token.verify_oauth2_token(raw_token, Request(), client_id)
    except Exception:
        return None
    if not claims.get("sub") or not claims.get("email") or not claims.get("email_verified"):
        return None
    return claims


@transaction.atomic
def google_login(claims: dict) -> tuple[User, bool]:
    provider_user_id = str(claims["sub"])
    identity = OAuthIdentity.objects.select_related("user").filter(
        provider=OAuthIdentity.Provider.GOOGLE,
        provider_user_id=provider_user_id,
    ).first()
    if identity:
        if not identity.user.is_active:
            raise ValueError("This account is unavailable.")
        return identity.user, False

    email = claims["email"].strip().lower()
    user = User.objects.filter(email__iexact=email).first()
    now = timezone.now()
    created = user is None
    if user is None:
        user = User(
            email=email,
            full_name=(claims.get("name") or email.split("@", 1)[0])[:120],
            display_name=(claims.get("given_name") or "")[:60] or None,
            password=None,
            email_verified_at=now,
            status=User.Status.ACTIVE,
        )
        user.save(force_insert=True)
    else:
        if not user.is_active:
            raise ValueError("This account is unavailable.")
        if user.email_verified_at is None:
            user.email_verified_at = now
            user.save(update_fields=("email_verified_at", "updated_at"))

    OAuthIdentity.objects.create(
        user=user,
        provider=OAuthIdentity.Provider.GOOGLE,
        provider_user_id=provider_user_id,
    )
    UserSettings.objects.get_or_create(user=user)
    return user, created
