"""
Tests for enhanced email functionality including preferences, logging, and workflows.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch, MagicMock
import uuid

from planner.models import UserEmailPreference, EmailLog, VacationPlan
from planner.email_utils import (
    get_or_create_email_preferences, 
    can_send_email, 
    send_html_email,
    send_registration_confirmation_email
)


class UserEmailPreferenceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_email_preference_creation(self):
        """Test creating email preferences for a user."""
        preferences = get_or_create_email_preferences(self.user)
        
        self.assertEqual(preferences.user, self.user)
        self.assertTrue(preferences.receive_vacation_invitations)
        self.assertTrue(preferences.receive_activity_notifications)
        self.assertTrue(preferences.receive_password_reset_emails)
        self.assertTrue(preferences.receive_account_notifications)
        self.assertFalse(preferences.receive_marketing_emails)
        self.assertFalse(preferences.is_unsubscribed)
        self.assertTrue(preferences.can_receive_emails)

    def test_unsubscribe_all(self):
        """Test unsubscribing from all emails."""
        preferences = get_or_create_email_preferences(self.user)
        preferences.unsubscribe_all()
        
        self.assertTrue(preferences.is_unsubscribed)
        self.assertFalse(preferences.can_receive_emails)
        self.assertFalse(preferences.receive_vacation_invitations)
        self.assertFalse(preferences.receive_activity_notifications)
        self.assertFalse(preferences.receive_account_notifications)
        self.assertFalse(preferences.receive_marketing_emails)
        # Password reset should still be enabled
        self.assertTrue(preferences.receive_password_reset_emails)

    def test_mark_bounce(self):
        """Test marking email as bounced."""
        preferences = get_or_create_email_preferences(self.user)
        
        # Soft bounce
        preferences.mark_bounce(is_hard_bounce=False)
        self.assertEqual(preferences.bounce_count, 1)
        self.assertTrue(preferences.is_email_valid)
        
        # Hard bounce
        preferences.mark_bounce(is_hard_bounce=True)
        self.assertEqual(preferences.bounce_count, 2)
        self.assertFalse(preferences.is_email_valid)

    def test_mark_complaint(self):
        """Test marking email as complained."""
        preferences = get_or_create_email_preferences(self.user)
        preferences.mark_complaint()
        
        self.assertTrue(preferences.complaint_received)
        self.assertFalse(preferences.is_email_valid)
        self.assertFalse(preferences.can_receive_emails)


class EmailUtilsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_can_send_email_valid_user(self):
        """Test email permission checking for valid user."""
        can_send, reason = can_send_email(self.user, 'vacation_invitation')
        self.assertTrue(can_send)
        self.assertEqual(reason, "OK")

    def test_can_send_email_unsubscribed_user(self):
        """Test email permission checking for unsubscribed user."""
        preferences = get_or_create_email_preferences(self.user)
        preferences.unsubscribe_all()
        
        can_send, reason = can_send_email(self.user, 'vacation_invitation')
        self.assertFalse(can_send)
        self.assertIn("unsubscribed", reason.lower())

    def test_can_send_email_disabled_type(self):
        """Test email permission checking for disabled email type."""
        preferences = get_or_create_email_preferences(self.user)
        preferences.receive_vacation_invitations = False
        preferences.save()
        
        can_send, reason = can_send_email(self.user, 'vacation_invitation')
        self.assertFalse(can_send)
        self.assertIn("disabled", reason.lower())


class EmailLogTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_email_log_creation(self):
        """Test creating an email log entry."""
        log = EmailLog.objects.create(
            email_type='registration',
            recipient_email=self.user.email,
            recipient_user=self.user,
            subject='Welcome to Organisize'
        )
        
        self.assertEqual(log.status, 'pending')
        self.assertEqual(log.email_type, 'registration')
        self.assertEqual(log.recipient_user, self.user)

    def test_email_log_status_updates(self):
        """Test updating email log status."""
        log = EmailLog.objects.create(
            email_type='registration',
            recipient_email=self.user.email,
            subject='Test'
        )
        
        # Mark as sent
        log.mark_sent('ses-message-id-123')
        self.assertEqual(log.status, 'sent')
        self.assertEqual(log.ses_message_id, 'ses-message-id-123')
        self.assertIsNotNone(log.sent_at)
        
        # Mark as delivered
        log.mark_delivered()
        self.assertEqual(log.status, 'delivered')
        self.assertIsNotNone(log.delivered_at)
        
        # Mark as bounced
        log.mark_bounced('Permanent', 'General')
        self.assertEqual(log.status, 'bounced')
        self.assertEqual(log.bounce_type, 'Permanent')
        self.assertEqual(log.bounce_subtype, 'General')


class UnsubscribeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.preferences = get_or_create_email_preferences(self.user)

    def test_unsubscribe_view_get(self):
        """Test GET request to unsubscribe view."""
        response = self.client.get(
            reverse('unsubscribe', kwargs={'token': self.preferences.unsubscribe_token})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)
        self.assertContains(response, 'Email Preferences')

    def test_unsubscribe_view_post_unsubscribe_all(self):
        """Test POST request to unsubscribe from all emails."""
        response = self.client.post(
            reverse('unsubscribe', kwargs={'token': self.preferences.unsubscribe_token}),
            {'action': 'unsubscribe_all'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.preferences.refresh_from_db()
        self.assertTrue(self.preferences.is_unsubscribed)

    def test_unsubscribe_view_invalid_token(self):
        """Test unsubscribe view with invalid token."""
        invalid_token = uuid.uuid4()
        response = self.client.get(
            reverse('unsubscribe', kwargs={'token': invalid_token})
        )
        
        self.assertEqual(response.status_code, 404)
        # The template should contain this text
        self.assertContains(response, 'Invalid Unsubscribe Link', status_code=404)

    def test_email_preferences_view_authenticated(self):
        """Test email preferences view for authenticated user."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('email_preferences'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email Preferences')

    def test_email_preferences_view_unauthenticated(self):
        """Test email preferences view redirects unauthenticated users."""
        response = self.client.get(reverse('email_preferences'))
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))