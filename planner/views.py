from django.shortcuts import render, get_object_or_404, redirect
from django.forms import inlineformset_factory
from .models import VacationPlan, Flight, Lodging, Activity
from .forms import VacationPlanForm, FlightForm, LodgingForm, ActivityForm
from django.views.decorators.http import require_POST
from .models import Flight, Lodging, Activity


def home(request):
    return render(request, "home.html")


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

    # Query related objects
    flights = Flight.objects.filter(vacation=vacation)
    lodgings = Lodging.objects.filter(vacation=vacation)
    activities = Activity.objects.filter(vacation=vacation)

    # Fresh forms for modals
    flight_form = FlightForm()
    lodging_form = LodgingForm()
    activity_form = ActivityForm()

    return render(
        request,
        "planner/vacation_detail.html",
        {
            "vacation": vacation,
            "flight_form": flight_form,
            "lodging_form": lodging_form,
            "activity_form": activity_form,
            "flights": flights,
            "lodgings": lodgings,
            "activities": activities,
        },
    )


@require_POST
def add_flight(request, pk):
    vacation = get_object_or_404(VacationPlan, pk=pk)
    form = FlightForm(request.POST)
    if form.is_valid():
        flight = form.save(commit=False)
        flight.vacation = vacation
        flight.save()
    return redirect("vacation_detail", pk=pk)


@require_POST
def add_lodging(request, pk):
    vacation = get_object_or_404(VacationPlan, pk=pk)
    form = LodgingForm(request.POST)
    if form.is_valid():
        lodging = form.save(commit=False)
        lodging.vacation = vacation
        lodging.save()
    if not form.is_valid():
        print("Lodging form errors:", form.errors)

    return redirect("vacation_detail", pk=pk)


@require_POST
def add_activity(request, pk):
    vacation = get_object_or_404(VacationPlan, pk=pk)
    form = ActivityForm(request.POST)
    if form.is_valid():
        activity = form.save(commit=False)
        activity.vacation = vacation
        activity.save()
    return redirect("vacation_detail", pk=pk)
