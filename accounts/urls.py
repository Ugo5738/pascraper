from accounts import forms, views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

router = routers.DefaultRouter()

router.register(r"users", views.UserViewSet, basename="user")

admin_urls = [
    path("", include(router.urls)),
    path("current-user/", views.CurrentUserDetailView.as_view(), name="current-user"),
    path("change-password", views.ChangePasswordView.as_view(), name="change_password"),
    path(
        "change-password/", views.ChangePasswordView.as_view(), name="change-password"
    ),
    path("delete-account/", views.DeleteAccountView.as_view(), name="delete-account"),
    path(
        "password-reset/",
        include("django_rest_passwordreset.urls", namespace="password_reset"),
    ),
]

jwt_urls = [
    path("token/", views.CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
]

account_urls = [
    path("signup/", views.RegisterAPIView.as_view(), name="signup"),
    path(
        "verify-email/<str:token>/",
        views.VerifyEmailView.as_view(),
        name="verify_email",
    ),
    path(
        "resend-verification/",
        views.ResendVerificationEmailView.as_view(),
        name="resend_verification",
    ),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="account/login.html", authentication_form=forms.UserLoginForm
        ),
        name="login",
    ),
    # path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("logout/", views.LogoutView.as_view(), name="auth_logout"),
]

social_urls = []

google_auth_urls = [
    # path('google_auth-2/', views.google_auth, name='google_auth'),
    # path('oauth2callback/', views.google_callback, name='gmail_callback'),
]


password_urls = [
    # path("change-password/", views.ChangePassword.as_view(), name="change_password"),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            form_class=forms.CustomPasswordResetForm,
            template_name="account/password/password_reset.html",
            subject_template_name="account/password/password_reset_subject.txt",
            email_template_name="account/password/password_reset_email.html",
            from_email=settings.EMAIL_HOST_USER,
            # success_url='/login/'
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="account/password/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="account/password/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="account/password/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]

urlpatterns = (
    admin_urls
    + jwt_urls
    + account_urls
    + password_urls
    + social_urls
    + google_auth_urls
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += staticfiles_urlpatterns()
