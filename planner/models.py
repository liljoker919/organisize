# models.py
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class VacationPlan(models.Model):
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="owned_vacations"
    )
    shared_with = models.ManyToManyField(
        User, related_name="shared_vacations", blank=True
    )
    destination = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    trip_type = models.CharField(
        max_length=50, choices=[("planned", "Planned"), ("booked", "Booked")]
    )
    estimated_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    notes = models.TextField(blank=True)
    whos_going = models.TextField(blank=True)
    group = models.ForeignKey(  # New field
        "Group",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vacations",
    )

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError("End date cannot be earlier than start date.")

    def __str__(self):
        return self.destination

    class Meta:
        indexes = [
            models.Index(fields=["start_date"]),
            models.Index(fields=["end_date"]),
            models.Index(fields=["trip_type"]),
        ]


class Flight(models.Model):
    vacation = models.ForeignKey(
        VacationPlan, on_delete=models.CASCADE, related_name="flights"
    )
    airline = models.CharField(max_length=100)
    confirmation = models.CharField(max_length=100)
    departure_airport = models.CharField(max_length=100)
    arrival_airport = models.CharField(max_length=100)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    actual_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )


class Lodging(models.Model):
    vacation = models.ForeignKey(
        VacationPlan, on_delete=models.CASCADE, related_name="lodgings"
    )
    confirmation = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    check_in = models.DateField()
    check_out = models.DateField()
    actual_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )


class Activity(models.Model):
    vacation = models.ForeignKey(
        VacationPlan, on_delete=models.CASCADE, related_name="activities"
    )
    name = models.CharField(max_length=200)
    date = models.DateField()
    start_time = models.TimeField()
    actual_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )


class Group(models.Model):
    """
    Group model to enable group collaboration and voting on activities.
    The model should include fields for the group name, invite link, and members
    """

    name = models.CharField(max_length=200)
    invite_link = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    members = models.ManyToManyField(User, related_name="vacation_groups")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-created_at"]
