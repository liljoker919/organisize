from django.urls import path
from . import views
from .views import VacationListView, vacation_detail, create_vacation

urlpatterns = [
    path("", VacationListView.as_view(), name="vacation_list"),
    path("create/", views.create_vacation, name="create_vacation"),
    path("<int:pk>/", views.vacation_detail, name="vacation_detail"),
    path("<int:pk>/add-flight/", views.add_flight, name="add_flight"),
    path("<int:pk>/add-lodging/", views.add_lodging, name="add_lodging"),
    path("<int:pk>/add-activity/", views.add_activity, name="add_activity"),
    path("<int:pk>/convert/", views.convert_to_booked, name="convert_to_booked"),
]
