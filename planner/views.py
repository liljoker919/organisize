from django.shortcuts import render, get_object_or_404, redirect
from django.forms import inlineformset_factory
from .models import VacationPlan, Flight, Lodging, Activity
from .forms import VacationPlanForm, FlightForm, LodgingForm, ActivityForm
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_http_methods
from .models import Flight, Lodging, Activity
from django.template.loader import render_to_string
from django.http import JsonResponse


def home(request):
    return render(request, "planner/home.html")


def vacation_list(request):
    vacations = VacationPlan.objects.all()
    return render(request, "planner/vacation_list.html", {"vacations": vacations})


def create_vacation(request):
    if request.method == "POST":
        form = VacationPlanForm(request.POST)
        if form.is_valid():
            vacation = form.save()
            return redirect("vacation_detail", pk=vacation.pk)
    else:
        form = VacationPlanForm()
    return render(request, "planner/create_vacation.html", {"form": form})


def vacation_detail(request, pk):
    vacation = get_object_or_404(VacationPlan, pk=pk)

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
