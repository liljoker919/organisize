from django import forms
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import VacationPlan, Flight, Lodging, Activity, Group
from django.contrib.auth.models import User


class VacationPlanForm(forms.ModelForm):
    share_with_emails = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        help_text="Enter email addresses separated by commas.",
        label="Share with (Emails)",
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
        ]
        widgets = {
            "start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "end_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "destination": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter destination"}
            ),
            "estimated_cost": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "Enter estimated cost",
                }
            ),
            "whos_going": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Enter names of attendees",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Enter additional notes",
                }
            ),
            "trip_type": forms.Select(attrs={"class": "form-control"}),
        }

    def clean_share_with_emails(self):
        emails = self.cleaned_data.get("share_with_emails", "")
        email_list = [email.strip() for email in emails.split(",") if email.strip()]
        for email in email_list:
            try:
                validate_email(email)
            except ValidationError:
                raise ValidationError(f"Invalid email address: {email}")
        return email_list


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
        fields = ["confirmation", "name", "lodging_type", "check_in", "check_out", "actual_cost"]
        widgets = {
            "confirmation": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Confirmation #"}
            ),
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Lodging name"}
            ),
            "lodging_type": forms.Select(
                attrs={"class": "form-control"}
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
        fields = ["name", "date", "start_time", "actual_cost", "notes"]
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
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Personal notes for this activity",
                }
            ),
        }


class ShareVacationForm(forms.Form):
    emails = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        help_text="Enter email addresses separated by commas.",
    )


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ["name", "description", "invite_link_expiry"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter group name"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Enter group description (optional)",
                }
            ),
            "invite_link_expiry": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "class": "form-control",
                    "placeholder": "Invite link expiry (optional)",
                }
            ),
        }

    def clean_invite_link_expiry(self):
        """Validate that invite_link_expiry is in the future"""
        from django.utils import timezone
        expiry = self.cleaned_data.get('invite_link_expiry')
        if expiry and expiry <= timezone.now():
            raise ValidationError("Invite link expiry must be in the future.")
        return expiry
