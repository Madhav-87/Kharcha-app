from django.urls import path

from apps.accounts.views import (
    ChangePasswordView,
    CompleteOnboardingView,
    ForgotPasswordView,
    GoogleLoginView,
    LoginView,
    LogoutView,
    MeView,
    OnboardingView,
    ProfileView,
    RefreshView,
    RegisterView,
    ResetPasswordView,
    SessionDetailView,
    SessionsView,
    SettingsView,
)

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/google/", GoogleLoginView.as_view(), name="auth-google"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("auth/forgot-password/", ForgotPasswordView.as_view(), name="auth-forgot-password"),
    path("auth/reset-password/", ResetPasswordView.as_view(), name="auth-reset-password"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("auth/sessions/", SessionsView.as_view(), name="auth-sessions"),
    path("auth/sessions/all/", SessionsView.as_view(), name="auth-sessions-all"),
    path("auth/sessions/<str:public_id>/", SessionDetailView.as_view(), name="auth-session-detail"),
    path("users/me/", ProfileView.as_view(), name="user-profile"),
    path("settings/", SettingsView.as_view(), name="user-settings"),
    path("onboarding/", OnboardingView.as_view(), name="onboarding"),
    path("onboarding/complete/", CompleteOnboardingView.as_view(), name="onboarding-complete"),
]
