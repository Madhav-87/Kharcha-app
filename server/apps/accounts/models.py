"""Identity, authentication metadata, settings, and onboarding models.

The tables are provisioned by the supplied MySQL schema, so these models are
intentionally unmanaged by Django migrations.
"""

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models

from common.db_fields import (
    DatabaseNowDateTime3Field,
    DateTime3Field,
    FixedCharField,
    PublicIdField,
    UnsignedBigAutoField,
    UnsignedBigIntegerField,
    UnsignedIntegerAutoField,
    UnsignedTinyIntegerField,
    UpdatedDateTime3Field,
    VarBinaryField,
)


class College(models.Model):
    id = UnsignedIntegerAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100, default="")
    state = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "colleges"
        constraints = [models.UniqueConstraint(fields=("name", "city"), name="uq_college")]

    def __str__(self):
        return f"{self.name}, {self.city}"


class UserManager(BaseUserManager):
    """Manager for the existing users table; passwords use Django hashers."""

    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("A user must have an email address.")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        if password is None:
            user.set_unusable_password()
        else:
            user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        PENDING_DELETION = "pending_deletion", "Pending deletion"
        DELETED = "deleted", "Deleted"

    id = UnsignedBigAutoField(primary_key=True)
    public_id = PublicIdField()
    full_name = models.CharField(max_length=120)
    display_name = models.CharField(max_length=60, null=True, blank=True)
    email = models.EmailField(max_length=255, unique=True)
    phone = FixedCharField(max_length=13, unique=True, null=True, blank=True)
    password = models.CharField(
        max_length=255, db_column="password_hash", null=True, blank=True
    )
    college = models.ForeignKey(
        College,
        on_delete=models.SET_NULL,
        db_column="college_id",
        null=True,
        blank=True,
        related_name="users",
    )
    college_name = models.CharField(max_length=160, null=True, blank=True)
    avatar_url = models.CharField(max_length=500, null=True, blank=True)
    email_verified_at = DateTime3Field(null=True, blank=True)
    phone_verified_at = DateTime3Field(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    last_login = DateTime3Field(db_column="last_login_at", null=True, blank=True)
    created_at = DatabaseNowDateTime3Field()
    updated_at = UpdatedDateTime3Field()

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        managed = False
        db_table = "users"

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE

    @property
    def is_staff(self):
        return False

    @property
    def is_superuser(self):
        return False

    @property
    def password_hash(self):
        return self.password

    @property
    def last_login_at(self):
        return self.last_login

    def has_perm(self, perm, obj=None):
        return False

    def has_module_perms(self, app_label):
        return False

    def __str__(self):
        return self.display_name or self.full_name


class OAuthIdentity(models.Model):
    class Provider(models.TextChoices):
        GOOGLE = "google", "Google"

    id = UnsignedBigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="oauth_identities")
    provider = models.CharField(max_length=6, choices=Provider.choices)
    provider_user_id = models.CharField(max_length=255)
    created_at = DatabaseNowDateTime3Field()

    class Meta:
        managed = False
        db_table = "oauth_identities"
        constraints = [
            models.UniqueConstraint(
                fields=("provider", "provider_user_id"), name="uq_oauth"
            )
        ]


class AuthSession(models.Model):
    id = UnsignedBigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="auth_sessions")
    refresh_token_hash = FixedCharField(max_length=64, unique=True)
    device_label = models.CharField(max_length=120, null=True, blank=True)
    user_agent = models.CharField(max_length=400, null=True, blank=True)
    ip_address = models.CharField(max_length=45, null=True, blank=True)
    created_at = DatabaseNowDateTime3Field()
    last_active_at = DatabaseNowDateTime3Field()
    expires_at = DateTime3Field()
    revoked_at = DateTime3Field(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "auth_sessions"
        indexes = [models.Index(fields=("user", "revoked_at", "expires_at"), name="idx_sessions_user")]


class PasswordResetToken(models.Model):
    id = UnsignedBigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_tokens")
    token_hash = FixedCharField(max_length=64, unique=True)
    expires_at = DateTime3Field()
    used_at = DateTime3Field(null=True, blank=True)
    created_at = DatabaseNowDateTime3Field()

    class Meta:
        managed = False
        db_table = "password_reset_tokens"


class TwoFactorMethod(models.Model):
    class Method(models.TextChoices):
        TOTP = "totp", "TOTP"
        SMS = "sms", "SMS"

    id = UnsignedBigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="two_factor_methods")
    method = models.CharField(max_length=4, choices=Method.choices)
    secret_enc = VarBinaryField(max_length=512, null=True, blank=True)
    enabled_at = DateTime3Field(null=True, blank=True)
    created_at = DatabaseNowDateTime3Field()

    class Meta:
        managed = False
        db_table = "two_factor_methods"
        constraints = [
            models.UniqueConstraint(fields=("user", "method"), name="uq_2fa")
        ]


class UserSettings(models.Model):
    user = models.OneToOneField(
        User, primary_key=True, on_delete=models.CASCADE, related_name="settings"
    )
    monthly_budget_paise = UnsignedBigIntegerField(null=True, blank=True)
    currency = FixedCharField(max_length=3, default="INR")
    default_category = models.ForeignKey(
        "categories.Category",
        on_delete=models.SET_NULL,
        db_column="default_category_id",
        null=True,
        blank=True,
        related_name="default_for_settings",
    )
    preferred_upi_app = models.ForeignKey(
        "payments.UpiApp",
        on_delete=models.SET_NULL,
        db_column="preferred_upi_app_id",
        null=True,
        blank=True,
        related_name="preferred_by_settings",
    )
    budget_alert_threshold = UnsignedTinyIntegerField(default=80)
    push_enabled = models.BooleanField(default=True)
    notify_budget_alerts = models.BooleanField(default=True)
    notify_payment_updates = models.BooleanField(default=True)
    notify_system = models.BooleanField(default=True)
    onboarding_step = UnsignedTinyIntegerField(default=1)
    onboarding_completed_at = DateTime3Field(null=True, blank=True)
    updated_at = UpdatedDateTime3Field()

    class Meta:
        managed = False
        db_table = "user_settings"
