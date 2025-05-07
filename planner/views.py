from django.shortcuts import render, get_object_or_404, redirect
from django.forms import inlineformset_factory
from .models import VacationPlan, Flight, Lodging, Activity
from .forms import VacationPlanForm, FlightForm, LodgingForm, ActivityForm
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .models import Flight, Lodging, Activity
from django.template.loader import render_to_string
from django.template.exceptions import TemplateDoesNotExist
from django.http import JsonResponse
from django.contrib import messages
from django.template import Template
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.views.generic.edit import CreateView
from django.db.models import Q


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
def create_vacation(request):
    if request.method == "POST":
        form = VacationPlanForm(request.POST)
        if form.is_valid():
            vacation = form.save(commit=False)
            vacation.owner = request.user
            vacation.save()
            form.save_m2m()  # Save shared_with relationships
            return redirect("vacation_list")
    else:
        form = VacationPlanForm()
    return render(request, "planner/create_vacation.html", {"form": form})


@login_required
def edit_vacation(request, pk):
    vacation = get_object_or_404(VacationPlan, pk=pk)
    if vacation.owner != request.user:
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

    flights = Flight.objects.filter(vacation=vacation)
    lodgings = Lodging.objects.filter(vacation=vacation)
    activities = Activity.objects.filter(vacation=vacation)

    context = {
        "vacation": vacation,
        "flights": flights,
        "lodgings": lodgings,
        "activities": activities,
        "flight_form": FlightForm(),  # Form for adding a new flight
        "lodging_form": LodgingForm(),  # Form for adding a new lodging
        "activity_form": ActivityForm(),  # Form for adding a new activity
        "form": VacationPlanForm(instance=vacation),  # Form for editing the vacation
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


@require_http_methods(["POST"])
def add_activity(request, pk):
    vacation = get_object_or_404(VacationPlan, pk=pk)
    form = ActivityForm(request.POST)

    if form.is_valid():
        activity = form.save(commit=False)
        activity.vacation = vacation
        activity.save()
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
    vacation = get_object_or_404(VacationPlan, pk=pk)

    if vacation.trip_type == "planned":
        vacation.trip_type = "booked"
        vacation.save()
        messages.success(request, "Trip converted to Booked!")
    return redirect("vacation_detail", pk=pk)
