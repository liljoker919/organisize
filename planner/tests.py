from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from planner.models import VacationPlan, Activity
from datetime import date, time


class ActivityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.vacation = VacationPlan.objects.create(
            owner=self.user,
            destination='Test Destination',
            start_date=date(2025, 7, 1),
            end_date=date(2025, 7, 7),
            trip_type='planned'
        )
        
    def test_activities_list_view_requires_login(self):
        """Test that activities list view requires authentication"""
        response = self.client.get(reverse('activities_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
    def test_activities_list_view_authenticated(self):
        """Test that activities list view works for authenticated users"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('activities_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'All Activities')
        
    def test_activity_model_with_notes(self):
        """Test that Activity model can store notes"""
        activity = Activity.objects.create(
            vacation=self.vacation,
            name='Test Activity',
            date=date(2025, 7, 2),
            start_time=time(10, 0),
            suggested_by=self.user,
            notes='These are test notes for the activity'
        )
        self.assertEqual(activity.notes, 'These are test notes for the activity')
        
    def test_activities_list_displays_user_activities(self):
        """Test that activities list shows activities from user's vacations"""
        activity = Activity.objects.create(
            vacation=self.vacation,
            name='Test Activity',
            date=date(2025, 7, 2),
            start_time=time(10, 0),
            suggested_by=self.user,
            notes='Test notes'
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('activities_list'))
        self.assertContains(response, 'Test Activity')
        self.assertContains(response, 'Test notes')

# Create your tests here.
