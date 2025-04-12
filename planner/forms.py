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
        exclude = ["vacation"]
        widgets = {
            "airline": forms.TextInput(attrs={"class": "form-control"}),
            "confirmation": forms.TextInput(attrs={"class": "form-control"}),
            "departure_airport": forms.TextInput(attrs={"class": "form-control"}),
            "arrival_airport": forms.TextInput(attrs={"class": "form-control"}),
            "departure_time": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "arrival_time": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
        }


class LodgingForm(forms.ModelForm):
    class Meta:
        model = Lodging
        exclude = ["vacation"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "confirmation": forms.TextInput(attrs={"class": "form-control"}),
            "check_in": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "check_out": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
        }


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        exclude = ["vacation"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "start_time": forms.TimeInput(
                attrs={"class": "form-control", "type": "time"}
            ),
        }
