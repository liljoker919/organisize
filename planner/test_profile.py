"""
Test for profile and email preferences accessibility
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class ProfileAndEmailPreferencesTest(TestCase):
    """Test profile page and email preferences accessibility"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_profile_page_accessible_when_logged_in(self):
        """Test that profile page is accessible for logged-in users"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User Profile')
        self.assertContains(response, 'testuser')
        self.assertContains(response, 'test@example.com')
    
    def test_profile_page_redirects_when_not_logged_in(self):
        """Test that profile page redirects to login when not authenticated"""
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_email_preferences_page_accessible_when_logged_in(self):
        """Test that email preferences page is accessible for logged-in users"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('email_preferences'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email Preferences')
    
    def test_email_preferences_page_redirects_when_not_logged_in(self):
        """Test that email preferences page redirects to login when not authenticated"""
        response = self.client.get(reverse('email_preferences'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_profile_page_contains_email_preferences_link(self):
        """Test that profile page contains a link to email preferences"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        # Check that the email preferences link is present
        self.assertContains(response, reverse('email_preferences'))
        self.assertContains(response, 'Email Preferences')
        self.assertContains(response, 'Manage your email notification settings')