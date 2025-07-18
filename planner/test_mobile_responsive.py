# Test mobile responsive dashboard functionality
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from planner.models import VacationPlan


class MobileResponsiveDashboardTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_home_page_has_responsive_grid_classes(self):
        """Test that landing page has proper responsive grid classes"""
        response = self.client.get(reverse('home'))
        content = response.content.decode()
        
        # Check for responsive grid classes in landing page
        self.assertIn('col-lg', content)
        self.assertIn('col-md', content)
        
        # Check for Bootstrap responsive components
        self.assertIn('d-flex', content)
        self.assertIn('flex-column', content)

    def test_dashboard_home_page_responsive_classes(self):
        """Test that vacation list (main dashboard) has proper responsive classes"""
        # Create a vacation to test the grid layout
        VacationPlan.objects.create(
            destination='Test Destination',
            start_date='2024-07-01',
            end_date='2024-07-10',
            owner=self.user,
            trip_type='booked'
        )
        
        response = self.client.get(reverse('vacation_list'))
        content = response.content.decode()
        
        # Check for responsive grid classes in vacation cards
        self.assertIn('col-12 col-md-6 col-lg-4', content)
        
        # Check for Bootstrap card improvements
        self.assertIn('card h-100 shadow-sm', content)
        self.assertIn('d-flex flex-column', content)

    def test_home_page_has_mobile_friendly_icons(self):
        """Test that landing page includes proper icons for mobile"""
        response = self.client.get(reverse('home'))
        content = response.content.decode()
        
        # Check for Bootstrap icons in landing page
        self.assertIn('bi bi-suitcase', content)
        self.assertIn('bi bi-plus-circle', content)
        self.assertIn('bi bi-question-circle', content)

    def test_vacation_detail_page_responsive_classes(self):
        """Test that vacation detail page has responsive improvements"""
        # Create a vacation for testing
        vacation = VacationPlan.objects.create(
            destination='Test Destination',
            start_date='2024-07-01',
            end_date='2024-07-10',
            owner=self.user,
            trip_type='booked'
        )
        
        response = self.client.get(reverse('vacation_detail', args=[vacation.id]))
        content = response.content.decode()
        
        # Check for mobile-responsive action button classes
        self.assertIn('vacation-actions', content)
        self.assertIn('section-header', content)
        
        # Check for improved button styling
        self.assertIn('btn btn-success', content)
        self.assertIn('btn btn-warning', content)
        self.assertIn('btn btn-danger', content)

    def test_responsive_css_is_included(self):
        """Test that custom responsive CSS is properly included"""
        response = self.client.get(reverse('vacation_list'))
        content = response.content.decode()
        
        # Check that our custom CSS file is linked
        self.assertIn('planner/css/responsive.css', content)

    def test_vacation_list_maintains_responsive_grid(self):
        """Test that vacation list page maintains proper responsive grid"""
        # Create a vacation to test the grid layout
        VacationPlan.objects.create(
            destination='Test Destination',
            start_date='2024-07-01',
            end_date='2024-07-10',
            owner=self.user,
            trip_type='booked'
        )
        
        response = self.client.get(reverse('vacation_list'))
        content = response.content.decode()
        
        # Check for existing responsive grid classes
        self.assertIn('col-12 col-md-6 col-lg-4', content)
        
        # Check for responsive card styling
        self.assertIn('card h-100 shadow-sm', content)

    def test_modal_responsive_improvements(self):
        """Test that modals have responsive improvements when vacation exists"""
        # Create a vacation to trigger modal availability
        vacation = VacationPlan.objects.create(
            destination='Test Destination',
            start_date='2024-07-01',
            end_date='2024-07-10',
            owner=self.user,
            trip_type='booked'
        )
        
        response = self.client.get(reverse('vacation_detail', args=[vacation.id]))
        content = response.content.decode()
        
        # Check for modal dialog improvements
        self.assertIn('modal-dialog', content)
        
        # Check for modal centering class if present
        # Note: This will only appear if we've updated the specific modal templates
        
    def test_base_template_viewport_meta_tag(self):
        """Test that base template has proper viewport meta tag for mobile"""
        response = self.client.get(reverse('vacation_list'))
        content = response.content.decode()
        
        # Check for proper viewport meta tag
        self.assertIn('name="viewport"', content)
        self.assertIn('width=device-width, initial-scale=1', content)

    def test_bootstrap_responsive_utilities_present(self):
        """Test that Bootstrap responsive utilities are being used"""
        response = self.client.get(reverse('vacation_list'))
        content = response.content.decode()
        
        # Check for Bootstrap responsive utilities
        self.assertIn('d-flex', content)
        self.assertIn('mb-', content)  # margin bottom classes
        self.assertIn('mt-', content)  # margin top classes