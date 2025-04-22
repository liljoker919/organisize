from django import forms
from .models import VacationPlan, Flight, Lodging, Activity
from django.contrib.auth.models import User


class VacationPlanForm(forms.ModelForm):
    shared_with = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-control"}),
    )

    class Meta:
        model = VacationPlan
        fields = [
            "destination",
            "start_date",
            "end_date",
            "estimated_cost",
            "whos_going",
            "notes",
            "trip_type",
            "shared_with",
        ]
        widgets = {
            "start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "end_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "destination": forms.TextInput(attrs={"class": "form-control"}),
            "estimated_cost": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "whos_going": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "trip_type": forms.Select(attrs={"class": "form-control"}),
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
            "actual_cost",
        ]
        widgets = {
            "airline": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Airline"}
            ),
            "confirmation": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Confirmation #"}
            ),
            "departure_airport": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Departure airport"}
            ),
            "arrival_airport": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Arrival airport"}
            ),
            "departure_time": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "class": "form-control",
                    "placeholder": "Departure time",
                }
            ),
            "arrival_time": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "class": "form-control",
                    "placeholder": "Arrival time",
                }
            ),
            "actual_cost": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Actual cost",
                    "step": "0.01",
                }
            ),
        }


class LodgingForm(forms.ModelForm):
    class Meta:
        model = Lodging
        fields = ["confirmation", "name", "check_in", "check_out", "actual_cost"]
        widgets = {
            "confirmation": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Confirmation #"}
            ),
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Lodging name"}
            ),
            "check_in": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                    "placeholder": "Check-in date",
                }
            ),
            "check_out": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                    "placeholder": "Check-out date",
                }
            ),
            "actual_cost": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Actual cost",
                    "step": "0.01",
                }
            ),
        }


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ["name", "date", "start_time", "actual_cost"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Activity name"}
            ),
            "date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                    "placeholder": "Activity date",
                }
            ),
            "start_time": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "form-control",
                    "placeholder": "Start time",
                }
            ),
            "actual_cost": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Actual cost",
                    "step": "0.01",
                }
            ),
        }
