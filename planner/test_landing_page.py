# Test landing page functionality
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class LandingPageTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_landing_page_accessible_without_authentication(self):
        """Test that the landing page is accessible without login"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Organisize')

    def test_landing_page_has_required_sections(self):
        """Test that landing page contains all required sections"""
        response = self.client.get('/')
        
        # Hero section
        self.assertContains(response, 'Plan, organize, and manage your dream vacations')
        
        # How It Works section
        self.assertContains(response, 'How It Works')
        self.assertContains(response, '1. Plan')
        self.assertContains(response, '2. Invite')
        self.assertContains(response, '3. Itinerary')
        
        # Features section
        self.assertContains(response, 'Everything You Need')
        self.assertContains(response, 'Smart Itineraries')
        self.assertContains(response, 'Easy Sharing')
        self.assertContains(response, 'Lodging Management')
        self.assertContains(response, 'Activity Planning')
        self.assertContains(response, 'Transportation')
        self.assertContains(response, 'Cost Tracking')
        
        # Screenshots/Demo section
        self.assertContains(response, 'See It In Action')
        
        # CTA footer
        self.assertContains(response, 'Ready to Plan Your Next Vacation?')

    def test_landing_page_cta_buttons(self):
        """Test that CTA buttons link to correct pages"""
        response = self.client.get('/')
        
        # Check for register links
        self.assertContains(response, reverse('register'))
        
        # Check for login links  
        self.assertContains(response, reverse('login'))

    def test_register_page_accessible(self):
        """Test that register page is accessible"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Register')

    def test_responsive_design_classes(self):
        """Test that Bootstrap responsive classes are present"""
        response = self.client.get('/')
        content = response.content.decode()
        
        # Check for responsive grid classes
        self.assertIn('col-lg', content)
        self.assertIn('col-md', content)
        
        # Check for Bootstrap components
        self.assertIn('btn btn-', content)
        self.assertIn('card', content)


class RegisterFunctionalityTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_form_renders(self):
        """Test that register form renders correctly"""
        response = self.client.get(reverse('register'))
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="password1"')
        self.assertContains(response, 'name="password2"')

    def test_successful_register_redirects_to_login(self):
        """Test that successful registration redirects to login page"""
        response = self.client.post(reverse('register'), {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123'
        })
        self.assertRedirects(response, reverse('login'))
        
        # Verify user was created
        self.assertTrue(User.objects.filter(username='testuser').exists())