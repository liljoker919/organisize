from django.shortcuts import render, get_object_or_404, redirect
from django.forms import inlineformset_factory
from .models import VacationPlan, Lodging, Activity, Group, Transportation
from .forms import (
    VacationPlanForm,
    TransportationForm,
    LodgingForm,
    ActivityForm,
    ShareVacationForm,
    GroupForm,
    CustomUserCreationForm,
)
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .models import Lodging, Activity, Transportation
from django.template.loader import render_to_string
from django.template.exceptions import TemplateDoesNotExist
from django.http import JsonResponse, Http404
from django.contrib import messages
from django.template import Template
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.views.generic.edit import CreateView
from django.db.models import Q
from django.core.mail import send_mail
from .email_utils import send_vacation_invitation_email, send_registration_confirmation_email
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.utils.crypto import get_random_string
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from datetime import datetime, date, timedelta
from collections import defaultdict


def home(request):
    return render(request, "planner/landing.html")


@method_decorator(login_required, name="dispatch")
class VacationListView(ListView):
    model = VacationPlan
    template_name = "planner/vacation_list.html"
    context_object_name = "vacations"

    def get_queryset(self):
        return VacationPlan.objects.filter(
            Q(owner=self.request.user) | Q(shared_with=self.request.user)
        ).distinct()


@login_required
def activities_list(request):
    """Standalone activities page showing all activities the user has access to"""
    # Get all activities from vacations the user owns or is shared with
    activities = (
        Activity.objects.filter(
            Q(vacation__owner=request.user) | Q(vacation__shared_with=request.user)
        )
        .distinct()
        .select_related("vacation", "suggested_by")
    )

    return render(request, "planner/activities_list.html", {"activities": activities})


@login_required
def create_vacation(request):
    if request.method == "POST":
        form = VacationPlanForm(request.POST)
        if form.is_valid():
            vacation = form.save(commit=False)
            vacation.owner = request.user
            vacation.save()

            # Process shared emails
            # emails = form.cleaned_data.get("share_with_emails", "").split(",")
            # emails = [email.strip() for email in emails if email.strip()]

            emails = form.cleaned_data.get("share_with_emails", [])
            for email in emails:
                user = User.objects.filter(email=email).first()
                if user:
                    # Existing user: Add to shared_with
                    vacation.shared_with.add(user)
                    # Send invitation email to existing user
                    send_vacation_invitation_email(
                        vacation=vacation,
                        inviter=request.user,
                        invitee_email=email,
                        request=request
                    )
                else:
                    # New user: Create a temporary user and send registration email
                    temp_password = get_random_string(8)
                    new_user = User.objects.create_user(
                        username=email.split("@")[0],
                        email=email,
                        password=temp_password,
                    )
                    vacation.shared_with.add(new_user)
                    send_vacation_invitation_email(
                        vacation=vacation,
                        inviter=request.user,
                        invitee_email=email,
                        temp_password=temp_password,
                        request=request
                    )

            form.save_m2m()  # Save shared_with relationships
            messages.success(request, "Vacation created successfully!")
            return redirect("vacation_list")
    else:
        form = VacationPlanForm()
    return render(request, "planner/create_vacation.html", {"form": form})


@login_required
def edit_vacation(request, pk):
    vacation = get_object_or_404(VacationPlan, pk=pk)
    if vacation.owner != request.user:
        messages.error(request, "You do not have permission to edit this vacation.")
        return redirect("vacation_detail", pk=vacation.pk)

    if request.method == "POST":
        form = VacationPlanForm(request.POST, instance=vacation)
        if form.is_valid():
            form.save()
            messages.success(request, "Vacation updated successfully.")
            return redirect("vacation_detail", pk=vacation.pk)
    else:
        form = VacationPlanForm(instance=vacation)

    return render(
        request, "planner/edit_vacation.html", {"form": form, "vacation": vacation}
    )


@login_required
@require_http_methods(["POST"])
def delete_vacation(request, pk):
    vacation = get_object_or_404(VacationPlan, pk=pk)
    if vacation.owner == request.user:
        vacation.delete()
        messages.success(request, "Vacation deleted successfully.")
    else:
        messages.error(request, "You do not have permission to delete this vacation.")
    return redirect("vacation_list")


@login_required
def vacation_detail(request, pk):
    vacation = get_object_or_404(
        VacationPlan.objects.filter(Q(pk=pk) & (Q(owner=request.user) | Q(shared_with=request.user))).distinct()
    )

    # Initialize forms for static modals
    activity_form = ActivityForm()
    transportation_form = TransportationForm()
    edit_vacation_form = VacationPlanForm(instance=vacation)

    # Initialize forms for dynamic modals (e.g., editing existing objects)
    activities = vacation.activities.all()
    activity_forms = {
        activity.id: ActivityForm(instance=activity) for activity in activities
    }
    
    transportations = vacation.transportations.all()
    transportation_forms = {transportation.id: TransportationForm(instance=transportation) for transportation in transportations}

    lodgings = vacation.lodgings.all()
    context = {
        "vacation": vacation,
        "group": vacation.group,  # Add group to context
        "activity_form": activity_form,
        "transportation_form": transportation_form,
        "edit_vacation_form": edit_vacation_form,
        "activity_forms": activity_forms,
        "transportation_forms": transportation_forms,
        "activities": activities,
        "transportations": transportations,
        "lodgings": lodgings,
        "shared_users": vacation.shared_with.all(),
    }
    return render(request, "planner/vacation_detail.html", context)


@login_required
def vacation_stays(request, pk):
    """Separate stays/lodging page with timeline view"""
    vacation = get_object_or_404(VacationPlan, pk=pk)
    lodgings = vacation.lodgings.all().order_by("check_in")

    # Initialize forms for modals
    lodging_form = LodgingForm()
    lodging_forms = {lodging.id: LodgingForm(instance=lodging) for lodging in lodgings}

    context = {
        "vacation": vacation,
        "lodgings": lodgings,
        "lodging_form": lodging_form,
        "lodging_forms": lodging_forms,
    }
    return render(request, "planner/vacation_stays.html", context)


@login_required
def vacation_itinerary(request, pk):
    """Generate a day-by-day itinerary for a vacation"""
    vacation = get_object_or_404(
        VacationPlan.objects.filter(Q(pk=pk) & (Q(owner=request.user) | Q(shared_with=request.user))).distinct()
    )

    # Get all vacation events
    transportations = vacation.transportations.all()
    lodgings = vacation.lodgings.all()
    activities = vacation.activities.all()

    # Generate date range for the vacation
    start_date = vacation.start_date
    end_date = vacation.end_date

    # Create a dictionary to organize events by date
    itinerary_by_date = defaultdict(list)

    # Add transportation events
    for transportation in transportations:
        # Departure event
        departure_date = transportation.departure_time.date()
        if start_date <= departure_date <= end_date:
            itinerary_by_date[departure_date].append(
                {
                    "type": f"{transportation.transportation_type}_departure",
                    "time": transportation.departure_time.time(),
                    "title": f"{transportation.get_transportation_type_display()} Departure - {transportation.provider}",
                    "details": f"{transportation.departure_location} → {transportation.arrival_location}",
                    "confirmation": transportation.confirmation,
                    "cost": transportation.actual_cost,
                    "notes": None,
                }
            )

        # Arrival event
        arrival_date = transportation.arrival_time.date()
        if start_date <= arrival_date <= end_date:
            itinerary_by_date[arrival_date].append(
                {
                    "type": f"{transportation.transportation_type}_arrival",
                    "time": transportation.arrival_time.time(),
                    "title": f"{transportation.get_transportation_type_display()} Arrival - {transportation.provider}",
                    "details": f"{transportation.departure_location} → {transportation.arrival_location}",
                    "confirmation": transportation.confirmation,
                    "cost": transportation.actual_cost,
                    "notes": None,
                }
            )

    # Add lodging events
    for lodging in lodgings:
        # Check-in event
        if start_date <= lodging.check_in <= end_date:
            itinerary_by_date[lodging.check_in].append(
                {
                    "type": "lodging_checkin",
                    "time": None,  # No specific time for lodging
                    "title": f"Check-in - {lodging.name}",
                    "details": f"Confirmation: {lodging.confirmation}",
                    "confirmation": lodging.confirmation,
                    "cost": lodging.actual_cost,
                    "notes": None,
                }
            )

        # Check-out event
        if start_date <= lodging.check_out <= end_date:
            itinerary_by_date[lodging.check_out].append(
                {
                    "type": "lodging_checkout",
                    "time": None,  # No specific time for lodging
                    "title": f"Check-out - {lodging.name}",
                    "details": f"Confirmation: {lodging.confirmation}",
                    "confirmation": lodging.confirmation,
                    "cost": lodging.actual_cost,
                    "notes": None,
                }
            )

    # Add activity events
    for activity in activities:
        if start_date <= activity.date <= end_date:
            itinerary_by_date[activity.date].append(
                {
                    "type": "activity",
                    "time": activity.start_time,
                    "title": activity.name,
                    "details": f"Suggested by: {activity.suggested_by.username}",
                    "confirmation": None,
                    "cost": activity.actual_cost,
                    "notes": activity.notes,
                }
            )

    # Sort events within each day by time (events without time go last)
    for date_events in itinerary_by_date.values():
        date_events.sort(key=lambda x: x["time"] if x["time"] else datetime.max.time())

    # Create sorted list of dates and their events
    sorted_itinerary = []
    current_date = start_date
    while current_date <= end_date:
        events = itinerary_by_date.get(current_date, [])
        sorted_itinerary.append({"date": current_date, "events": events})
        current_date += timedelta(days=1)

    context = {
        "vacation": vacation,
        "itinerary": sorted_itinerary,
        "total_days": (end_date - start_date).days + 1,
    }

    return render(request, "planner/vacation_itinerary.html", context)


@require_http_methods(["POST"])
def add_transportation(request, pk):
    vacation = get_object_or_404(VacationPlan, pk=pk)
    form = TransportationForm(request.POST)

    if form.is_valid():
        transportation = form.save(commit=False)
        transportation.vacation = vacation
        transportation.save()
        return redirect("vacation_detail", pk=pk)

    # If invalid, re-render the whole page with the modal visible and errors
    lodging_form = LodgingForm()
    activity_form = ActivityForm()

    transportations = Transportation.objects.filter(vacation=vacation)
    lodgings = Lodging.objects.filter(vacation=vacation)
    activities = Activity.objects.filter(vacation=vacation)

    return render(
        request,
        "planner/vacation_detail.html",
        {
            "vacation": vacation,
            "transportation_form": form,
            "lodging_form": lodging_form,
            "activity_form": activity_form,
            "transportations": transportations,
            "lodgings": lodgings,
            "activities": activities,
            "show_transportation_modal": True,
        },
    )


@login_required
def edit_transportation(request, pk):
    transportation = get_object_or_404(Transportation, pk=pk)
    vacation = transportation.vacation
    if (
        vacation.owner != request.user
        and request.user not in vacation.shared_with.all()
    ):
        return redirect("vacation_detail", pk=vacation.pk)

    if request.method == "POST":
        form = TransportationForm(request.POST, instance=transportation)
        if form.is_valid():
            form.save()
            return redirect("vacation_detail", pk=vacation.pk)
    else:
        form = TransportationForm(instance=transportation)

    return render(request, "planner/edit_transportation.html", {"form": form, "transportation": transportation})


@login_required
@require_http_methods(["POST"])
def delete_transportation(request, pk):
    transportation = get_object_or_404(Transportation, pk=pk)
    vacation_pk = transportation.vacation.pk
    if (
        transportation.vacation.owner == request.user
        or request.user in transportation.vacation.shared_with.all()
    ):
        transportation.delete()
        messages.success(request, "Transportation deleted successfully.")
    else:
        messages.error(request, "You do not have permission to delete this transportation.")
    return redirect("vacation_detail", pk=vacation_pk)


@require_http_methods(["POST"])
def add_lodging(request, pk):
    vacation = get_object_or_404(VacationPlan, pk=pk)
    form = LodgingForm(request.POST)

    if form.is_valid():
        lodging = form.save(commit=False)
        lodging.vacation = vacation
        lodging.save()
        return redirect("vacation_detail", pk=pk)

    transportation_form = TransportationForm()
    activity_form = ActivityForm()

    transportations = Transportation.objects.filter(vacation=vacation)
    lodgings = Lodging.objects.filter(vacation=vacation)
    activities = Activity.objects.filter(vacation=vacation)

    return render(
        request,
        "planner/vacation_detail.html",
        {
            "vacation": vacation,
            "transportation_form": transportation_form,
            "lodging_form": form,
            "activity_form": activity_form,
            "transportations": transportations,
            "lodgings": lodgings,
            "activities": activities,
            "show_lodging_modal": True,
        },
    )


# edit_lodging view
@login_required
def edit_lodging(request, pk):
    lodging = get_object_or_404(Lodging, pk=pk)
    vacation = lodging.vacation
    if (
        vacation.owner != request.user
        and request.user not in vacation.shared_with.all()
    ):
        return redirect("vacation_detail", pk=vacation.pk)

    if request.method == "POST":
        form = LodgingForm(request.POST, instance=lodging)
        if form.is_valid():
            form.save()
            return redirect("vacation_detail", pk=vacation.pk)
    else:
        form = LodgingForm(instance=lodging)

    return render(
        request, "planner/edit_lodging.html", {"form": form, "lodging": lodging}
    )


# delete_lodging view
@login_required
def delete_lodging(request, pk):
    lodging = get_object_or_404(Lodging, pk=pk)
    vacation_pk = lodging.vacation.pk
    if lodging.vacation.owner == request.user:
        lodging.delete()
        messages.success(request, "Lodging deleted successfully.")
    return redirect("vacation_detail", pk=vacation_pk)


# Add activity view
@require_http_methods(["POST"])
def add_activity(request, pk):
    vacation = get_object_or_404(VacationPlan, pk=pk)
    form = ActivityForm(request.POST)

    if form.is_valid():
        activity = form.save(commit=False)
        activity.vacation = vacation
        activity.suggested_by = request.user
        activity.save()
        messages.success(request, "New Activity has been created!")
        return redirect("vacation_detail", pk=pk)

    transportation_form = TransportationForm()
    lodging_form = LodgingForm()

    transportations = Transportation.objects.filter(vacation=vacation)
    lodgings = Lodging.objects.filter(vacation=vacation)
    activities = Activity.objects.filter(vacation=vacation)

    return render(
        request,
        "planner/vacation_detail.html",
        {
            "vacation": vacation,
            "transportation_form": transportation_form,
            "lodging_form": lodging_form,
            "activity_form": form,
            "transportations": transportations,
            "lodgings": lodgings,
            "activities": activities,
            "show_activity_modal": True,
        },
    )


# edit_activity view
@login_required
def edit_activity(request, pk):
    activity = get_object_or_404(Activity, pk=pk)
    vacation = activity.vacation
    if (
        vacation.owner != request.user
        and request.user not in vacation.shared_with.all()
    ):
        return redirect("vacation_detail", pk=vacation.pk)

    if request.method == "POST":
        form = ActivityForm(request.POST, instance=activity)
        if form.is_valid():
            form.save()
            return redirect("vacation_detail", pk=vacation.pk)
    else:
        form = ActivityForm(instance=activity)

    return render(
        request, "planner/edit_activity.html", {"form": form, "activity": activity}
    )


# vote activity view
@login_required
@require_POST  # This ensure that view only handles POST requests.
def vote_activity(request, pk):
    activity = get_object_or_404(Activity, pk=pk)

    if request.user not in activity.voted_users.all():
        activity.votes += 1
        activity.voted_users.add(request.user)
        activity.save()
        messages.success(request, "Your vote has been counted!")

    return redirect("vacation_detail", pk=activity.vacation.pk)


# delete_activity view
@login_required
def delete_activity(request, pk):
    activity = get_object_or_404(Activity, pk=pk)
    vacation_pk = activity.vacation.pk
    if activity.vacation.owner == request.user:
        activity.delete()
        messages.success(request, "Activity deleted successfully.")
    return redirect("vacation_detail", pk=vacation_pk)


def convert_to_booked(request, pk):
    vacation = get_object_or_404(VacationPlan, pk=pk, owner=request.user)

    if vacation.trip_type == "planned":
        vacation.trip_type = "booked"
        vacation.save()
        messages.success(request, "Trip converted to Booked!")
    return redirect("vacation_detail", pk=pk)


@login_required
def share_vacation(request, pk):
    vacation = get_object_or_404(VacationPlan, pk=pk, owner=request.user)

    if request.method == "POST":
        form = ShareVacationForm(request.POST)
        if form.is_valid():
            emails = form.cleaned_data["emails"].split(",")
            emails = [email.strip() for email in emails]
            for email in emails:
                user = User.objects.filter(email=email).first()
                if user:
                    # Existing user: Add to shared_with
                    vacation.shared_with.add(user)
                    # Send invitation email to existing user
                    send_vacation_invitation_email(
                        vacation=vacation,
                        inviter=request.user,
                        invitee_email=email,
                        request=request
                    )
                else:
                    # New user: Create a temporary user and send registration email
                    temp_password = get_random_string(8)
                    new_user = User.objects.create_user(
                        username=email.split("@")[0],
                        email=email,
                        password=temp_password,
                    )
                    vacation.shared_with.add(new_user)
                    send_vacation_invitation_email(
                        vacation=vacation,
                        inviter=request.user,
                        invitee_email=email,
                        temp_password=temp_password,
                        request=request
                    )
            messages.success(request, "Vacation shared successfully!")
            return redirect("vacation_detail", pk=pk)
    else:
        form = ShareVacationForm()

    return render(
        request, "planner/share_vacation.html", {"form": form, "vacation": vacation}
    )


@login_required
@require_http_methods(["POST"])
def invite_users(request, pk):
    vacation = get_object_or_404(VacationPlan, pk=pk, owner=request.user)
    
    # Get email addresses from the form
    emails_input = request.POST.get("invite_emails", "")
    email_list = [email.strip() for email in emails_input.split(",") if email.strip()]
    
    if not email_list:
        messages.error(request, "Please provide at least one email address.")
        return redirect("vacation_detail", pk=pk)
    
    # Validate email addresses
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    
    valid_emails = []
    for email in email_list:
        try:
            validate_email(email)
            valid_emails.append(email)
        except ValidationError:
            messages.error(request, f"Invalid email address: {email}")
            return redirect("vacation_detail", pk=pk)
    
    # Find existing users and add them to the vacation
    existing_users = User.objects.filter(email__in=valid_emails)
    already_shared_emails = set(vacation.shared_with.values_list('email', flat=True))
    
    new_users_added = 0
    for user in existing_users:
        if user.email not in already_shared_emails and user != vacation.owner:
            vacation.shared_with.add(user)
            new_users_added += 1
    
    # For emails that don't correspond to existing users, we could:
    # 1. Store them in a separate invitation model (future enhancement)
    # 2. Create inactive user accounts and send invitation emails (future enhancement)
    # For now, we'll just inform the user about existing users that were added
    
    existing_user_emails = set(existing_users.values_list('email', flat=True))
    non_existing_emails = set(valid_emails) - existing_user_emails
    
    success_message_parts = []
    if new_users_added > 0:
        success_message_parts.append(f"{new_users_added} existing user(s) added to vacation")
    
    if non_existing_emails:
        # For now, just inform the user that these emails were noted
        # In a full implementation, we'd send invitation emails
        success_message_parts.append(f"Noted {len(non_existing_emails)} email(s) for users not yet registered")
    
    if success_message_parts:
        messages.success(request, "; ".join(success_message_parts))
    else:
        messages.info(request, "No new users were added (users may already be invited or invalid)")
    
    return redirect("vacation_detail", pk=pk)


@login_required
@require_http_methods(["POST"])
def manage_users(request, pk):
    vacation = get_object_or_404(VacationPlan, pk=pk, owner=request.user)
    user_ids = request.POST.getlist("remove_users")
    users = User.objects.filter(id__in=user_ids)
    vacation.shared_with.remove(*users)
    messages.success(request, "Users removed successfully!")
    return redirect("vacation_detail", pk=pk)


def clean_share_with_emails(self):
    emails = self.cleaned_data.get("share_with_emails", "")
    email_list = [email.strip() for email in emails.split(",") if email.strip()]
    for email in email_list:
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError(f"Invalid email address: {email}")
    return email_list


# Group Views
@login_required
def group_list(request):
    """List all groups the user is a member of or created"""
    groups = Group.objects.filter(
        Q(members=request.user) | Q(creator=request.user)
    ).distinct()
    return render(request, "planner/group_list.html", {"groups": groups})


@login_required
def group_detail(request, pk):
    """View group details"""
    group = get_object_or_404(Group, pk=pk)
    # Check if user is a member or creator
    if not (request.user in group.members.all() or request.user == group.creator):
        raise Http404("Group not found")

    return render(request, "planner/group_detail.html", {"group": group})


@login_required
def create_group(request):
    """Create a new group"""
    if request.method == "POST":
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.creator = request.user
            group.save()
            # Add creator as a member
            group.members.add(request.user)
            messages.success(request, "Group created successfully!")
            return redirect("group_detail", pk=group.pk)
    else:
        form = GroupForm()
    return render(request, "planner/create_group.html", {"form": form})


def register(request):
    """User registration view"""
    # Redirect authenticated users to vacation list
    if request.user.is_authenticated:
        return redirect('vacation_list')
    
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            
            # Send registration confirmation email
            send_registration_confirmation_email(user, request)
            
            messages.success(request, f"Account created for {username}! You can now log in.")
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})
