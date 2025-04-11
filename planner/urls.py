from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("vacations/", views.vacation_list, name="vacation_list"),
    path("vacations/new/", views.create_vacation, name="create_vacation"),
    path("vacations/<int:pk>/", views.vacation_detail, name="vacation_detail"),
    path("vacations/<int:pk>/add-flight/", views.add_flight, name="add_flight"),
    path("vacations/<int:pk>/add_lodging/", views.add_lodging, name="add_lodging"),
    path("vacations/<int:pk>/add-activity/", views.add_activity, name="add_activity"),
]
