from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from planner import views as planner_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", planner_views.home, name="home"),  # 👈 root route
    path("vacations/", include("planner.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
]
