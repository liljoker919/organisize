from django.urls import path
from . import views
from .views import VacationListView, create_vacation
from . import email_views

urlpatterns = [
    path("", VacationListView.as_view(), name="vacation_list"),
    path("activities/", views.activities_list, name="activities_list"),
    path("create/", views.create_vacation, name="create_vacation"),
    path("<int:pk>/", views.vacation_detail, name="vacation_detail"),
    path("<int:pk>/itinerary/", views.vacation_itinerary, name="vacation_itinerary"),

    path("<int:pk>/stays/", views.vacation_stays, name="vacation_stays"),

    path("<int:pk>/edit/", views.edit_vacation, name="edit_vacation"),
    path("<int:pk>/delete/", views.delete_vacation, name="delete_vacation"),
    path("<int:pk>/convert/", views.convert_to_booked, name="convert_to_booked"),
    # Transportation
    path("<int:pk>/add-transportation/", views.add_transportation, name="add_transportation"),
    path("transportation/<int:pk>/edit/", views.edit_transportation, name="edit_transportation"),
    path("transportation/<int:pk>/delete/", views.delete_transportation, name="delete_transportation"),
    # Lodging
    path("<int:pk>/add-lodging/", views.add_lodging, name="add_lodging"),
    path("lodging/<int:pk>/edit/", views.edit_lodging, name="edit_lodging"),
    path("lodging/<int:pk>/delete/", views.delete_lodging, name="delete_lodging"),
    # Activities
    path("<int:pk>/add-activity/", views.add_activity, name="add_activity"),
    path("activity/<int:pk>/edit/", views.edit_activity, name="edit_activity"),
    path("activity/<int:pk>/delete/", views.delete_activity, name="delete_activity"),
    path('activity/<int:pk>/vote/', views.vote_activity, name='vote_activity'),
    # User management
    path("<int:pk>/share/", views.share_vacation, name="share_vacation"),
    path("vacations/<int:pk>/invite/", views.invite_users, name="invite_users"),
    path("vacations/<int:pk>/manage/", views.manage_users, name="manage_users"),
    # Groups
    path("groups/", views.group_list, name="group_list"),
    path("groups/create/", views.create_group, name="create_group"),
    path("groups/<int:pk>/", views.group_detail, name="group_detail"),
    
    # Email management
    path("email-preferences/", email_views.email_preferences_view, name="email_preferences"),
    
    # User profile
    path("profile/", views.profile_view, name="profile"),
]
