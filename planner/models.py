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


class UserEmailPreference(models.Model):
    """
    User email preferences for different types of communications.
    Supports unsubscribe functionality and email preference management.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name="email_preferences"
    )
    
    # Email subscription preferences
    receive_vacation_invitations = models.BooleanField(default=True)
    receive_activity_notifications = models.BooleanField(default=True)
    receive_password_reset_emails = models.BooleanField(default=True)
    receive_account_notifications = models.BooleanField(default=True)
    receive_marketing_emails = models.BooleanField(default=False)
    
    # Unsubscribe tracking
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    unsubscribe_token = models.UUIDField(default=uuid.uuid4, unique=True)
    
    # Email status tracking
    is_email_valid = models.BooleanField(default=True)
    bounce_count = models.IntegerField(default=0)
    complaint_received = models.BooleanField(default=False)
    last_email_sent = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def is_unsubscribed(self):
        """Check if user has unsubscribed from all emails."""
        return self.unsubscribed_at is not None
    
    @property
    def can_receive_emails(self):
        """Check if user can receive emails (not unsubscribed, complained, or invalid)."""
        return (
            not self.is_unsubscribed 
            and not self.complaint_received 
            and self.is_email_valid
        )
    
    def unsubscribe_all(self):
        """Unsubscribe user from all email communications."""
        from django.utils import timezone
        self.unsubscribed_at = timezone.now()
        self.receive_vacation_invitations = False
        self.receive_activity_notifications = False
        self.receive_account_notifications = False
        self.receive_marketing_emails = False
        # Keep password reset emails enabled for security
        self.save()
    
    def mark_bounce(self, is_hard_bounce=False):
        """Mark email as bounced and increment bounce count."""
        self.bounce_count += 1
        if is_hard_bounce or self.bounce_count >= 3:
            self.is_email_valid = False
        self.save()
    
    def mark_complaint(self):
        """Mark email as complained - immediately stop all communications."""
        self.complaint_received = True
        self.is_email_valid = False
        self.save()
    
    def __str__(self):
        return f"Email preferences for {self.user.username}"
    
    class Meta:
        ordering = ["-created_at"]


class EmailLog(models.Model):
    """
    Comprehensive email sending log for monitoring and compliance.
    """
    EMAIL_TYPES = [
        ('registration', 'Registration Confirmation'),
        ('password_reset', 'Password Reset'),
        ('vacation_invitation', 'Vacation Invitation'),
        ('activity_notification', 'Activity Notification'),
        ('unsubscribe_confirmation', 'Unsubscribe Confirmation'),
        ('marketing', 'Marketing Email'),
        ('system', 'System Notification'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('bounced', 'Bounced'),
        ('complained', 'Complained'),
        ('failed', 'Failed'),
    ]
    
    # Email identification
    email_type = models.CharField(max_length=50, choices=EMAIL_TYPES)
    recipient_email = models.EmailField()
    recipient_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="email_logs"
    )
    
    # Email content
    subject = models.CharField(max_length=255)
    message_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    bounced_at = models.DateTimeField(null=True, blank=True)
    complained_at = models.DateTimeField(null=True, blank=True)
    
    # AWS SES specific fields
    ses_message_id = models.CharField(max_length=255, null=True, blank=True)
    bounce_type = models.CharField(max_length=50, null=True, blank=True)  # 'Permanent', 'Transient'
    bounce_subtype = models.CharField(max_length=50, null=True, blank=True)
    complaint_feedback_type = models.CharField(max_length=50, null=True, blank=True)
    
    # Additional tracking
    error_message = models.TextField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def mark_sent(self, ses_message_id=None):
        """Mark email as sent."""
        from django.utils import timezone
        self.status = 'sent'
        self.sent_at = timezone.now()
        if ses_message_id:
            self.ses_message_id = ses_message_id
        self.save()
    
    def mark_delivered(self):
        """Mark email as delivered."""
        from django.utils import timezone
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save()
    
    def mark_bounced(self, bounce_type=None, bounce_subtype=None):
        """Mark email as bounced."""
        from django.utils import timezone
        self.status = 'bounced'
        self.bounced_at = timezone.now()
        self.bounce_type = bounce_type
        self.bounce_subtype = bounce_subtype
        self.save()
    
    def mark_complained(self, feedback_type=None):
        """Mark email as complained."""
        from django.utils import timezone
        self.status = 'complained'
        self.complained_at = timezone.now()
        self.complaint_feedback_type = feedback_type
        self.save()
    
    def mark_failed(self, error_message=None):
        """Mark email as failed."""
        self.status = 'failed'
        self.error_message = error_message
        self.save()
    
    def __str__(self):
        return f"{self.email_type} to {self.recipient_email} - {self.status}"
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["email_type"]),
            models.Index(fields=["recipient_email"]),
            models.Index(fields=["ses_message_id"]),
            models.Index(fields=["created_at"]),
        ]
