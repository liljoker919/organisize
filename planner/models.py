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


class Transportation(models.Model):
    TRANSPORTATION_TYPE_CHOICES = [
        ('flight', 'Flight'),
        ('train', 'Train'),
        ('bus', 'Bus'),
        ('ferry', 'Ferry'),
        ('car', 'Car'),
        ('other', 'Other'),
    ]
    
    vacation = models.ForeignKey(
        VacationPlan, on_delete=models.CASCADE, related_name="transportations"
    )
    transportation_type = models.CharField(
        max_length=20, choices=TRANSPORTATION_TYPE_CHOICES, default='flight'
    )
    provider = models.CharField(max_length=100)  # airline, bus company, train operator, etc.
    confirmation = models.CharField(max_length=100)
    departure_location = models.CharField(max_length=100)  # airport, station, terminal, etc.
    arrival_location = models.CharField(max_length=100)    # airport, station, terminal, etc.
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    actual_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    
    def __str__(self):
        return f"{self.get_transportation_type_display()}: {self.departure_location} → {self.arrival_location}"


class Lodging(models.Model):
    LODGING_TYPE_CHOICES = [
        ('hotel', 'Hotel'),
        ('motel', 'Motel'),
        ('resort', 'Resort'),
        ('hostel', 'Hostel'),
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('cabin', 'Cabin'),
        ('villa', 'Villa'),
        ('campground', 'Campground'),
        ('other', 'Other'),
    ]
    
    vacation = models.ForeignKey(
        VacationPlan, on_delete=models.CASCADE, related_name="lodgings"
    )
    confirmation = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    lodging_type = models.CharField(
        max_length=20, choices=LODGING_TYPE_CHOICES, default='hotel'
    )
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
    suggested_by = models.ForeignKey(User,on_delete=models.CASCADE,related_name='suggested_activities')
    votes = models.IntegerField(default=0)
    voted_users = models.ManyToManyField(User, related_name='voted_activities', blank=True)
    notes = models.TextField(blank=True, help_text="Personal notes for this activity")

    def __str__(self):
        return self.name

    # will display activities with highest votes first.
    class Meta:
        ordering = ["-votes"]

class Group(models.Model):
    """
    Group model to enable group collaboration and voting on activities.
    Includes fields for name, invite link, members, creator, description, and invite link expiry.
    """

    name = models.CharField(max_length=200)
    invite_link = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    invite_link_expiry = models.DateTimeField(null=True, blank=True)
    members = models.ManyToManyField(User, related_name="vacation_groups")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_groups")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_invite_active(self):
        """Check if the invite link is active based on expiry date."""
        from django.utils import timezone
        if self.invite_link_expiry:
            return self.invite_link_expiry > timezone.now()
        return True

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-created_at"]
