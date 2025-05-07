from django.urls import path
from . import views
from .views import VacationListView, vacation_detail, create_vacation

urlpatterns = [
    path("", VacationListView.as_view(), name="vacation_list"),
    path("create/", views.create_vacation, name="create_vacation"),
    path("<int:pk>/", vacation_detail, name="vacation_detail"),
    path("<int:pk>/edit/", views.edit_vacation, name="edit_vacation"),
    path("<int:pk>/delete/", views.delete_vacation, name="delete_vacation"),
    path("<int:pk>/convert/", views.convert_to_booked, name="convert_to_booked"),
    # Flights
    path("<int:pk>/add-flight/", views.add_flight, name="add_flight"),
    path("flight/<int:pk>/edit/", views.edit_flight, name="edit_flight"),
    path("flight/<int:pk>/delete/", views.delete_flight, name="delete_flight"),
    # Lodging
    path("<int:pk>/add-lodging/", views.add_lodging, name="add_lodging"),
    path("lodging/<int:pk>/edit/", views.edit_lodging, name="edit_lodging"),
    path("lodging/<int:pk>/delete/", views.delete_lodging, name="delete_lodging"),
    # Activities
    path("<int:pk>/add-activity/", views.add_activity, name="add_activity"),
    path("activity/<int:pk>/edit/", views.edit_activity, name="edit_activity"),
    path("activity/<int:pk>/delete/", views.delete_activity, name="delete_activity"),
]
