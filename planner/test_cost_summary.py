from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from datetime import date, datetime, time
from planner.models import VacationPlan, Transportation, Lodging, Activity


class CostSummaryTest(TestCase):
    """Test cost summary functionality in vacation detail view"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.vacation = VacationPlan.objects.create(
            owner=self.user,
            destination='Test Destination',
            start_date=date(2024, 6, 15),
            end_date=date(2024, 6, 18),
            trip_type='booked',
            estimated_cost=Decimal('1500.00')
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_cost_summary_with_all_costs(self):
        """Test cost summary when all items have costs"""
        # Create transportation with cost
        Transportation.objects.create(
            vacation=self.vacation,
            transportation_type='flight',
            provider='Test Airlines',
            confirmation='ABC123',
            departure_location='Test Airport A',
            arrival_location='Test Airport B',
            departure_time=datetime(2024, 6, 15, 10, 0),
            arrival_time=datetime(2024, 6, 15, 14, 0),
            actual_cost=Decimal('450.00')
        )
        
        # Create lodging with cost
        Lodging.objects.create(
            vacation=self.vacation,
            confirmation='HOTEL123',
            name='Test Hotel',
            lodging_type='hotel',
            check_in=date(2024, 6, 15),
            check_out=date(2024, 6, 18),
            actual_cost=Decimal('800.00')
        )
        
        # Create activity with cost
        Activity.objects.create(
            vacation=self.vacation,
            name='Test Activity',
            date=date(2024, 6, 16),
            start_time=time(14, 0),
            actual_cost=Decimal('120.00'),
            suggested_by=self.user
        )
        
        # Get vacation detail page
        response = self.client.get(reverse('vacation_detail', kwargs={'pk': self.vacation.pk}))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check context variables
        context = response.context
        self.assertEqual(context['transportation_total'], Decimal('450.00'))
        self.assertEqual(context['lodging_total'], Decimal('800.00'))
        self.assertEqual(context['activity_total'], Decimal('120.00'))
        self.assertEqual(context['grand_total'], Decimal('1370.00'))
        self.assertEqual(context['budget_difference'], Decimal('130.00'))
        self.assertFalse(context['is_over_budget'])
        
        # Check that Trip Summary appears in rendered content
        self.assertContains(response, 'Trip Summary')
        self.assertContains(response, '$450.00')  # Transportation total
        self.assertContains(response, '$800.00')  # Lodging total  
        self.assertContains(response, '$120.00')  # Activity total
        self.assertContains(response, '$1370.00')  # Grand total (without comma)
        self.assertContains(response, 'under budget')
    
    def test_cost_summary_over_budget(self):
        """Test cost summary when over budget"""
        # Create expensive transportation
        Transportation.objects.create(
            vacation=self.vacation,
            transportation_type='flight',
            provider='Expensive Airlines',
            confirmation='EXP123',
            departure_location='Test Airport A',
            arrival_location='Test Airport B',
            departure_time=datetime(2024, 6, 15, 10, 0),
            arrival_time=datetime(2024, 6, 15, 14, 0),
            actual_cost=Decimal('2000.00')  # Over budget
        )
        
        # Get vacation detail page
        response = self.client.get(reverse('vacation_detail', kwargs={'pk': self.vacation.pk}))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check context variables
        context = response.context
        self.assertEqual(context['transportation_total'], Decimal('2000.00'))
        self.assertEqual(context['grand_total'], Decimal('2000.00'))
        self.assertEqual(context['budget_difference'], Decimal('500.00'))
        self.assertTrue(context['is_over_budget'])
        
        # Check that over budget message appears
        self.assertContains(response, 'over budget')
    
    def test_cost_summary_no_costs(self):
        """Test cost summary when no items have costs"""
        # Create items without costs
        Transportation.objects.create(
            vacation=self.vacation,
            transportation_type='flight',
            provider='Free Airlines',
            confirmation='FREE123',
            departure_location='Test Airport A',
            arrival_location='Test Airport B',
            departure_time=datetime(2024, 6, 15, 10, 0),
            arrival_time=datetime(2024, 6, 15, 14, 0),
            actual_cost=None
        )
        
        # Get vacation detail page
        response = self.client.get(reverse('vacation_detail', kwargs={'pk': self.vacation.pk}))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        
        # Check context variables
        context = response.context
        self.assertEqual(context['transportation_total'], Decimal('0'))
        self.assertEqual(context['grand_total'], Decimal('0'))
        
        # Trip Summary should not appear when grand total is 0
        self.assertNotContains(response, 'Trip Summary')
    
    def test_individual_cost_display(self):
        """Test that individual costs are displayed properly"""
        # Create transportation with cost
        transportation = Transportation.objects.create(
            vacation=self.vacation,
            transportation_type='flight',
            provider='Test Airlines',
            confirmation='ABC123',
            departure_location='Test Airport A',
            arrival_location='Test Airport B',
            departure_time=datetime(2024, 6, 15, 10, 0),
            arrival_time=datetime(2024, 6, 15, 14, 0),
            actual_cost=Decimal('450.00')
        )
        
        # Create activity with cost
        activity = Activity.objects.create(
            vacation=self.vacation,
            name='Test Activity',
            date=date(2024, 6, 16),
            start_time=time(14, 0),
            actual_cost=Decimal('120.00'),
            suggested_by=self.user
        )
        
        # Get vacation detail page
        response = self.client.get(reverse('vacation_detail', kwargs={'pk': self.vacation.pk}))
        
        # Check that individual costs are displayed
        self.assertContains(response, '<strong>Cost:</strong> $450.00')  # Transportation cost
        self.assertContains(response, '<strong>Cost:</strong> $120.00')  # Activity cost
        self.assertContains(response, 'Total Transportation Cost')
        self.assertContains(response, 'Total Activities Cost')