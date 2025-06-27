"""
Tests for email functionality in the Organisize application.
"""

from django.test import TestCase, override_settings
from django.core import mail
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch
from datetime import date, timedelta

from planner.models import VacationPlan
from planner.email_utils import (
    send_html_email,
    send_registration_confirmation_email,
    send_vacation_invitation_email
)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class EmailUtilsTest(TestCase):
    """Test email utility functions"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.vacation = VacationPlan.objects.create(
            owner=self.user,
            destination='Paris, France',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=37),
            trip_type='planned',
            notes='Romantic getaway'
        )

    def test_send_html_email_basic(self):
        """Test basic HTML email sending"""
        context = {'username': 'testuser', 'site_url': 'https://example.com'}
        
        result = send_html_email(
            subject='Test Email',
            template_name='registration_confirmation',
            context=context,
            recipient_list=['test@example.com']
        )
        
        # Updated: new function returns dict
        self.assertTrue(result['success'])
        self.assertEqual(result['sent_count'], 1)
        self.assertEqual(len(result['failed']), 0)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Test Email')
        self.assertEqual(email.to, ['test@example.com'])
        self.assertIn('testuser', email.body)  # Plain text fallback
        self.assertEqual(len(email.alternatives), 1)  # HTML alternative

    def test_send_registration_confirmation_email(self):
        """Test registration confirmation email"""
        result = send_registration_confirmation_email(self.user)
        
        # Updated: new function returns dict
        self.assertTrue(result['success'])
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Welcome to Organisize - Registration Successful!')
        self.assertEqual(email.to, [self.user.email])
        self.assertIn('testuser', email.body)

    def test_send_vacation_invitation_email_new_user(self):
        """Test vacation invitation email for new user"""
        result = send_vacation_invitation_email(
            vacation=self.vacation,
            inviter=self.user,
            invitee_email='newuser@example.com',
            temp_password='temp123'
        )
        
        # Updated: new function returns dict
        self.assertTrue(result['success'])
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertIn('Paris, France', email.subject)
        self.assertEqual(email.to, ['newuser@example.com'])
        self.assertIn('temp123', email.body)  # Contains temp password

    def test_send_vacation_invitation_email_existing_user(self):
        """Test vacation invitation email for existing user"""
        result = send_vacation_invitation_email(
            vacation=self.vacation,
            inviter=self.user,
            invitee_email='existing@example.com'
        )
        
        # Updated: new function returns dict
        self.assertTrue(result['success'])
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertIn('Paris, France', email.subject)
        self.assertEqual(email.to, ['existing@example.com'])
        self.assertNotIn('password', email.body.lower())  # No temp password

    @patch('planner.email_utils.logger')
    def test_send_html_email_failure_handling(self, mock_logger):
        """Test email sending failure handling"""
        # Test with invalid template
        result = send_html_email(
            subject='Test',
            template_name='nonexistent_template',
            context={},
            recipient_list=['test@example.com']
        )
        
        # Updated: new function returns dict with success=False
        self.assertFalse(result['success'])
        self.assertEqual(result['sent_count'], 0)
        self.assertEqual(len(result['failed']), 1)
        mock_logger.error.assert_called_once()


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class EmailIntegrationTest(TestCase):
    """Test email integration with views"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_registration_sends_confirmation_email(self):
        """Test that user registration sends confirmation email"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        }
        
        response = self.client.post(reverse('register'), data=form_data)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        
        # Should send confirmation email
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['newuser@example.com'])
        self.assertIn('Welcome to Organisize', email.subject)

    def test_vacation_creation_with_invites_sends_emails(self):
        """Test that creating vacation with invites sends emails"""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'destination': 'Test Destination',
            'start_date': (date.today() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'end_date': (date.today() + timedelta(days=37)).strftime('%Y-%m-%d'),
            'trip_type': 'planned',
            'estimated_cost': '1500.00',
            'share_with_emails': 'invite1@example.com,invite2@example.com'
        }
        
        response = self.client.post(reverse('create_vacation'), data=form_data)
        self.assertEqual(response.status_code, 302)
        
        # Should send 2 invitation emails
        self.assertEqual(len(mail.outbox), 2)
        
        emails = [email.to[0] for email in mail.outbox]
        self.assertIn('invite1@example.com', emails)
        self.assertIn('invite2@example.com', emails)
        
        # Check email content
        for email in mail.outbox:
            self.assertIn('Test Destination', email.subject)

    def test_share_vacation_sends_emails(self):
        """Test that sharing vacation sends invitation emails"""
        vacation = VacationPlan.objects.create(
            owner=self.user,
            destination='Share Test',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=37),
            trip_type='planned'
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'emails': 'share1@example.com,share2@example.com'
        }
        
        response = self.client.post(
            reverse('share_vacation', kwargs={'pk': vacation.pk}),
            data=form_data
        )
        self.assertEqual(response.status_code, 302)
        
        # Should send 2 invitation emails
        self.assertEqual(len(mail.outbox), 2)
        
        emails = [email.to[0] for email in mail.outbox]
        self.assertIn('share1@example.com', emails)
        self.assertIn('share2@example.com', emails)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class EmailTemplateTest(TestCase):
    """Test email template rendering"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_registration_confirmation_template_renders(self):
        """Test that registration confirmation template renders correctly"""
        context = {
            'username': 'testuser',
            'user_email': 'test@example.com',
            'site_url': 'https://example.com'
        }
        
        result = send_html_email(
            subject='Test',
            template_name='registration_confirmation',
            context=context,
            recipient_list=['test@example.com']
        )
        
        # Updated: new function returns dict
        self.assertTrue(result['success'])
        email = mail.outbox[0]
        
        # Check that HTML alternative contains expected content
        html_content = email.alternatives[0][0]
        self.assertIn('testuser', html_content)
        self.assertIn('Start Planning Your Vacation', html_content)
        self.assertIn('example.com', html_content)

    def test_vacation_invitation_template_renders(self):
        """Test that vacation invitation template renders correctly"""
        vacation = VacationPlan.objects.create(
            owner=self.user,
            destination='Test Destination',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=37),
            trip_type='planned',
            notes='Test notes'
        )
        
        result = send_vacation_invitation_email(
            vacation=vacation,
            inviter=self.user,
            invitee_email='invitee@example.com',
            temp_password='temp123'
        )
        
        # Updated: new function returns dict
        self.assertTrue(result['success'])
        email = mail.outbox[0]
        
        # Check that HTML alternative contains expected content
        html_content = email.alternatives[0][0]
        self.assertIn('Test Destination', html_content)
        self.assertIn('testuser', html_content)
        self.assertIn('temp123', html_content)
        self.assertIn('Test notes', html_content)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend',
    DEFAULT_FROM_EMAIL='test@organisize.com'
)
class EmailSettingsTest(TestCase):
    """Test email configuration settings"""

    def test_email_settings_are_configurable(self):
        """Test that email settings can be configured via environment variables"""
        from django.conf import settings
        
        # Test that settings are loaded correctly
        self.assertEqual(settings.DEFAULT_FROM_EMAIL, 'test@organisize.com')
        self.assertEqual(settings.EMAIL_BACKEND, 'django.core.mail.backends.console.EmailBackend')

    def test_email_uses_default_from_email(self):
        """Test that emails use configured DEFAULT_FROM_EMAIL"""
        result = send_html_email(
            subject='Test',
            template_name='registration_confirmation',
            context={'username': 'test', 'site_url': 'https://example.com'},
            recipient_list=['test@example.com']
        )
        
        # Updated: new function returns dict
        self.assertTrue(result['success'])