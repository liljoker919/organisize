from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from planner import views as planner_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", planner_views.home, name="home"),  # 👈 root route
    path("signup/", planner_views.signup, name="signup"),  # 👈 signup route
    path("vacations/", include("planner.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/register/", planner_views.register, name="register"),
]
