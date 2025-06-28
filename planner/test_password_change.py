"""
Tests for password change functionality.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core import mail
from planner.models import EmailLog


class PasswordChangeTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpassword123'
        )
        
    def test_password_change_requires_login(self):
        """Test that password change page requires authentication."""
        response = self.client.get(reverse('password_change'))
        self.assertRedirects(response, '/accounts/login/?next=/accounts/password_change/')
        
    def test_password_change_form_displays(self):
        """Test that password change form displays for authenticated users."""
        self.client.login(username='testuser', password='oldpassword123')
        response = self.client.get(reverse('password_change'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Change Password')
        self.assertContains(response, 'Current Password')
        self.assertContains(response, 'New Password')
        
    def test_password_change_success(self):
        """Test successful password change with email notification."""
        self.client.login(username='testuser', password='oldpassword123')
        
        # Clear any existing emails
        mail.outbox = []
        
        response = self.client.post(reverse('password_change'), {
            'old_password': 'oldpassword123',
            'new_password1': 'newpassword456',
            'new_password2': 'newpassword456'
        })
        
        # Should redirect to success page
        self.assertRedirects(response, reverse('password_change_done'))
        
        # User should still be logged in (session preserved)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        
        # Password should be changed
        user = User.objects.get(username='testuser')
        self.assertTrue(user.check_password('newpassword456'))
        
        # Email should be sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['test@example.com'])
        self.assertIn('Password Changed Successfully', email.subject)
        
        # Email log should be created
        email_logs = EmailLog.objects.filter(
            email_type='password_change',
            recipient_email='test@example.com'
        )
        self.assertEqual(email_logs.count(), 1)
        
    def test_password_change_invalid_old_password(self):
        """Test password change with incorrect old password."""
        self.client.login(username='testuser', password='oldpassword123')
        
        response = self.client.post(reverse('password_change'), {
            'old_password': 'wrongpassword',
            'new_password1': 'newpassword456',
            'new_password2': 'newpassword456'
        })
        
        # Should show form with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your old password was entered incorrectly')
        
        # Password should not be changed
        user = User.objects.get(username='testuser')
        self.assertTrue(user.check_password('oldpassword123'))
        
    def test_password_change_mismatched_passwords(self):
        """Test password change with mismatched new passwords."""
        self.client.login(username='testuser', password='oldpassword123')
        
        response = self.client.post(reverse('password_change'), {
            'old_password': 'oldpassword123',
            'new_password1': 'newpassword456',
            'new_password2': 'differentpassword789'
        })
        
        # Should show form with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "two password fields")
        
        # Password should not be changed
        user = User.objects.get(username='testuser')
        self.assertTrue(user.check_password('oldpassword123'))
        
    def test_password_change_done_page(self):
        """Test password change done page displays correctly."""
        self.client.login(username='testuser', password='oldpassword123')
        response = self.client.get(reverse('password_change_done'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Password Changed Successfully')
        self.assertContains(response, 'confirmation email has been sent')
        
    def test_navigation_link_exists(self):
        """Test that the password change link exists in navigation."""
        self.client.login(username='testuser', password='oldpassword123')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Change Password')
        self.assertContains(response, reverse('password_change'))