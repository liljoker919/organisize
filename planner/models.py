# models.py
from django.db import models


class VacationPlan(models.Model):
    TRIP_TYPE_CHOICES = [
        ("planned", "Planned"),
        ("booked", "Booked"),
    ]

    title = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    trip_type = models.CharField(
        max_length=10, choices=TRIP_TYPE_CHOICES, default="planned"
    )
    estimated_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    actual_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    whos_going = models.TextField(blank=True)
    notes = models.TextField(default="", blank=True)

    def __str__(self):
        return self.title


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


class Lodging(models.Model):
    vacation = models.ForeignKey(
        VacationPlan, on_delete=models.CASCADE, related_name="lodgings"
    )
    confirmation = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    check_in = models.DateField()
    check_out = models.DateField()


class Activity(models.Model):
    vacation = models.ForeignKey(
        VacationPlan, on_delete=models.CASCADE, related_name="activities"
    )
    name = models.CharField(max_length=200)
    date = models.DateField()
    start_time = models.TimeField()
