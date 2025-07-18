from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from planner import views as planner_views
from planner import auth_views as custom_auth_views
from planner import email_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", planner_views.home, name="home"),  # 👈 root route
    path("vacations/", include("planner.urls")),
    
    # Enhanced authentication URLs
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/password_change/", custom_auth_views.CustomPasswordChangeView.as_view(), name="password_change"),
    path("accounts/password_change/done/", auth_views.PasswordChangeDoneView.as_view(), name="password_change_done"),
    
    # Enhanced password reset with logging
    path("accounts/password_reset/", custom_auth_views.CustomPasswordResetView.as_view(), name="password_reset"),
    path("accounts/password_reset/done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("accounts/reset/<uidb64>/<token>/", custom_auth_views.CustomPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("accounts/reset/complete/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
    
    path("accounts/register/", planner_views.register, name="register"),
    
    # Email management
    path("unsubscribe/<uuid:token>/", email_views.unsubscribe_view, name="unsubscribe"),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
