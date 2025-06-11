from django.shortcuts import render, get_object_or_404, redirect
from django.forms import inlineformset_factory
from .models import VacationPlan, Flight, Lodging, Activity
from .forms import (
    VacationPlanForm,
    FlightForm,
    LodgingForm,
    ActivityForm,
    ShareVacationForm,
)
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .models import Flight, Lodging, Activity
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
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST


def home(request):
    return render(request, "planner/home.html")


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
    activities = Activity.objects.filter(
        Q(vacation__owner=request.user) | Q(vacation__shared_with=request.user)
    ).distinct().select_related('vacation', 'suggested_by')
    
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
                else:
                    # New user: Create a temporary user and send registration email
                    temp_password = get_random_string(8)
                    new_user = User.objects.create_user(
                        username=email.split("@")[0],
                        email=email,
                        password=temp_password,
                    )
                    vacation.shared_with.add(new_user)
                    send_mail(
                        subject="You're invited to join a vacation on Organisize!",
                        message=f"You've been invited to join a vacation. "
                        f"Please register using this email and the temporary password: {temp_password}",
                        from_email="noreply@organisize.com",
                        recipient_list=[email],
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
        VacationPlan, Q(pk=pk) & (Q(owner=request.user) | Q(shared_with=request.user))
    )

    
    # Initialize forms for static modals
    lodging_form = LodgingForm()
    activity_form = ActivityForm()
    flight_form = FlightForm()
    edit_vacation_form = VacationPlanForm(instance=vacation)

    # Initialize forms for dynamic modals (e.g., editing existing objects)
    lodgings = vacation.lodgings.all()
    lodging_forms = {lodging.id: LodgingForm(instance=lodging) for lodging in lodgings}

    activities = vacation.activities.all()
    activity_forms = {
        activity.id: ActivityForm(instance=activity) for activity in activities
    }

    flights = vacation.flights.all()
    flight_forms = {flight.id: FlightForm(instance=flight) for flight in flights}

    context = {
        "vacation": vacation,
        "lodging_form": lodging_form,
        "activity_form": activity_form,
        "flight_form": flight_form,
        "edit_vacation_form": edit_vacation_form,
        "lodging_forms": lodging_forms,
        "activity_forms": activity_forms,
        "flight_forms": flight_forms,
        "activities" : activities
    }
    return render(request, "planner/vacation_detail.html", context)


@require_http_methods(["POST"])
def add_flight(request, pk):
    vacation = get_object_or_404(VacationPlan, pk=pk)
    form = FlightForm(request.POST)

    if form.is_valid():
        flight = form.save(commit=False)
        flight.vacation = vacation
        flight.save()
        return redirect("vacation_detail", pk=pk)

    # If invalid, re-render the whole page with the modal visible and errors
    lodging_form = LodgingForm()
    activity_form = ActivityForm()

    flights = Flight.objects.filter(vacation=vacation)
    lodgings = Lodging.objects.filter(vacation=vacation)
    activities = Activity.objects.filter(vacation=vacation)

    return render(
        request,
        "planner/vacation_detail.html",
        {
            "vacation": vacation,
            "flight_form": form,
            "lodging_form": lodging_form,
            "activity_form": activity_form,
            "flights": flights,
            "lodgings": lodgings,
            "activities": activities,
            "show_flight_modal": True,
        },
    )


@login_required
def edit_flight(request, pk):
    flight = get_object_or_404(Flight, pk=pk)
    vacation = flight.vacation
    if (
        vacation.owner != request.user
        and request.user not in vacation.shared_with.all()
    ):
        return redirect("vacation_detail", pk=vacation.pk)

    if request.method == "POST":
        form = FlightForm(request.POST, instance=flight)
        if form.is_valid():
            form.save()
            return redirect("vacation_detail", pk=vacation.pk)
    else:
        form = FlightForm(instance=flight)

    return render(request, "planner/edit_flight.html", {"form": form, "flight": flight})


@login_required
@require_http_methods(["POST"])
def delete_flight(request, pk):
    flight = get_object_or_404(Flight, pk=pk)
    vacation_pk = flight.vacation.pk
    if (
        flight.vacation.owner == request.user
        or request.user in flight.vacation.shared_with.all()
    ):
        flight.delete()
        messages.success(request, "Flight deleted successfully.")
    else:
        messages.error(request, "You do not have permission to delete this flight.")
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

    flight_form = FlightForm()
    activity_form = ActivityForm()

    flights = Flight.objects.filter(vacation=vacation)
    lodgings = Lodging.objects.filter(vacation=vacation)
    activities = Activity.objects.filter(vacation=vacation)

    return render(
        request,
        "planner/vacation_detail.html",
        {
            "vacation": vacation,
            "flight_form": flight_form,
            "lodging_form": form,
            "activity_form": activity_form,
            "flights": flights,
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

    flight_form = FlightForm()
    lodging_form = LodgingForm()

    flights = Flight.objects.filter(vacation=vacation)
    lodgings = Lodging.objects.filter(vacation=vacation)
    activities = Activity.objects.filter(vacation=vacation)

    return render(
        request,
        "planner/vacation_detail.html",
        {
            "vacation": vacation,
            "flight_form": flight_form,
            "lodging_form": lodging_form,
            "activity_form": form,
            "flights": flights,
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
@require_POST # This ensure that view only handles POST requests.
def vote_activity(request,pk):
    activity = get_object_or_404(Activity, pk=pk)

    if request.user not in activity.voted_users.all():
        activity.votes += 1
        activity.voted_users.add(request.user)
        activity.save()
        messages.success(request, "Your vote has been counted!")
        
    return redirect('vacation_detail', pk=activity.vacation.pk)


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
                else:
                    # New user: Create a temporary user and send registration email
                    temp_password = get_random_string(8)
                    new_user = User.objects.create_user(
                        username=email.split("@")[0],
                        email=email,
                        password=temp_password,
                    )
                    vacation.shared_with.add(new_user)
                    send_mail(
                        subject="You're invited to join a vacation on Organisize!",
                        message=f"You've been invited to join a vacation. "
                        f"Please register using this email and the temporary password: {temp_password}",
                        from_email="noreply@organisize.com",
                        recipient_list=[email],
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
    user_ids = request.POST.getlist("shared_with")
    users = User.objects.filter(id__in=user_ids)
    vacation.shared_with.add(*users)
    messages.success(request, "Users invited successfully!")
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
