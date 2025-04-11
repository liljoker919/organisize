from django import forms
from .models import VacationPlan, Flight, Lodging, Activity


class VacationPlanForm(forms.ModelForm):
    class Meta:
        model = VacationPlan
        fields = [
            "title",
            "destination",
            "start_date",
            "end_date",
            "trip_type",
            "estimated_cost",
            "actual_cost",
            "whos_going",
            "notes",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }


class FlightForm(forms.ModelForm):
    class Meta:
        model = Flight
        fields = [
            "airline",
            "confirmation",
            "departure_airport",
            "arrival_airport",
            "departure_time",
            "arrival_time",
        ]
        widgets = {
            "departure_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "arrival_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class LodgingForm(forms.ModelForm):
    class Meta:
        model = Lodging
        fields = [
            "confirmation",
            "name",
            "check_in",
            "check_out",
        ]
        widgets = {
            "check_in": forms.DateInput(attrs={"type": "date"}),
            "check_out": forms.DateInput(attrs={"type": "date"}),
        }


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = [
            "name",
            "date",
            "start_time",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
        }
