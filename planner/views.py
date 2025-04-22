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
def vacation_detail(request, pk):
    vacation = get_object_or_404(
        VacationPlan, Q(pk=pk) & (Q(owner=request.user) | Q(shared_with=request.user))
    )

    flights = Flight.objects.filter(vacation=vacation)
    lodgings = Lodging.objects.filter(vacation=vacation)
    activities = Activity.objects.filter(vacation=vacation)

    flight_form = FlightForm()
    lodging_form = LodgingForm()
    activity_form = ActivityForm()

    context = {
        "vacation": vacation,
        "flight_form": flight_form,
        "lodging_form": lodging_form,
        "activity_form": activity_form,
        "flights": flights,
        "lodgings": lodgings,
        "activities": activities,
    }
    try:
        return render(request, "planner/vacation_detail.html", context)
    except TemplateDoesNotExist:
        return render(request, "404.html", status=404)
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


def convert_to_booked(request, pk):
    vacation = get_object_or_404(VacationPlan, pk=pk)

    if vacation.trip_type == "planned":
        vacation.trip_type = "booked"
        vacation.save()
        messages.success(request, "Trip converted to Booked!")
    return redirect("vacation_detail", pk=pk)
