from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date
from django.core.exceptions import ValidationError
from django.urls import reverse
from planner.models import Group, VacationPlan, Lodging
from planner.forms import GroupForm, LodgingForm


class GroupModelTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )

    def test_group_creation_with_new_fields(self):
        """Test creating a group with creator and description"""
        group = Group.objects.create(
            name='Test Group',
            creator=self.user1,
            description='A test group for vacation planning'
        )
        
        self.assertEqual(group.name, 'Test Group')
        self.assertEqual(group.creator, self.user1)
        self.assertEqual(group.description, 'A test group for vacation planning')
        self.assertIsNone(group.invite_link_expiry)
        self.assertTrue(group.is_invite_active())

    def test_group_creation_without_optional_fields(self):
        """Test creating a group without description"""
        group = Group.objects.create(
            name='Test Group',
            creator=self.user1
        )
        
        self.assertEqual(group.name, 'Test Group')
        self.assertEqual(group.creator, self.user1)
        self.assertEqual(group.description, '')
        self.assertIsNone(group.invite_link_expiry)
        self.assertTrue(group.is_invite_active())

    def test_invite_link_expiry_future(self):
        """Test invite link is active when expiry is in the future"""
        future_time = timezone.now() + timedelta(hours=1)
        group = Group.objects.create(
            name='Test Group',
            creator=self.user1,
            invite_link_expiry=future_time
        )
        
        self.assertTrue(group.is_invite_active())

    def test_invite_link_expiry_past(self):
        """Test invite link is inactive when expiry is in the past"""
        past_time = timezone.now() - timedelta(hours=1)
        group = Group.objects.create(
            name='Test Group',
            creator=self.user1,
            invite_link_expiry=past_time
        )
        
        self.assertFalse(group.is_invite_active())

    def test_invite_link_no_expiry(self):
        """Test invite link is active when no expiry is set"""
        group = Group.objects.create(
            name='Test Group',
            creator=self.user1
        )
        
        self.assertTrue(group.is_invite_active())

    def test_creator_relationship(self):
        """Test the creator relationship works correctly"""
        group = Group.objects.create(
            name='Test Group',
            creator=self.user1
        )
        
        # Test reverse relationship
        created_groups = self.user1.created_groups.all()
        self.assertIn(group, created_groups)

    def test_members_relationship_unchanged(self):
        """Test that the existing members relationship still works"""
        group = Group.objects.create(
            name='Test Group',
            creator=self.user1
        )
        
        # Add members
        group.members.add(self.user1, self.user2)
        
        self.assertEqual(group.members.count(), 2)
        self.assertIn(group, self.user1.vacation_groups.all())
        self.assertIn(group, self.user2.vacation_groups.all())


class GroupFormTest(TestCase):
    def test_form_validation_future_expiry(self):
        """Test that form accepts future expiry dates"""
        future_time = timezone.now() + timedelta(hours=1)
        form_data = {
            'name': 'Test Group',
            'description': 'Test description',
            'invite_link_expiry': future_time.strftime('%Y-%m-%dT%H:%M')
        }
        form = GroupForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_validation_past_expiry(self):
        """Test that form rejects past expiry dates"""
        past_time = timezone.now() - timedelta(hours=1)
        form_data = {
            'name': 'Test Group',
            'description': 'Test description',
            'invite_link_expiry': past_time.strftime('%Y-%m-%dT%H:%M')
        }
        form = GroupForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('invite_link_expiry', form.errors)

    def test_form_validation_no_expiry(self):
        """Test that form works without expiry date"""
        form_data = {
            'name': 'Test Group',
            'description': 'Test description'
        }
        form = GroupForm(data=form_data)
        self.assertTrue(form.is_valid())



class LodgingModelTest(TestCase):
    def setUp(self):
        """Set up test data"""

class VacationItineraryTest(TestCase):
    def setUp(self):
        """Set up test data for itinerary tests"""


        self.vacation = VacationPlan.objects.create(
            owner=self.user,
            destination='Test Destination',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            trip_type='booked'
        )

    def test_lodging_with_type(self):
        """Test creating lodging with lodging_type field"""
        lodging = Lodging.objects.create(
            vacation=self.vacation,
            confirmation='TEST123',
            name='Test Hotel',
            lodging_type='hotel',
            check_in=date.today(),
            check_out=date.today() + timedelta(days=3)
        )
        
        self.assertEqual(lodging.lodging_type, 'hotel')
        self.assertEqual(lodging.get_lodging_type_display(), 'Hotel')

    def test_lodging_form_includes_type(self):
        """Test that LodgingForm includes lodging_type field"""
        form = LodgingForm()
        self.assertIn('lodging_type', form.fields)
        
        # Test form with lodging type
        form_data = {
            'confirmation': 'TEST123',
            'name': 'Test Resort',
            'lodging_type': 'resort',
            'check_in': date.today(),
            'check_out': date.today() + timedelta(days=3),
        }
        form = LodgingForm(data=form_data)
        self.assertTrue(form.is_valid())


class VacationStaysViewTest(TestCase):
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
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            trip_type='booked'
        )
        self.lodging1 = Lodging.objects.create(
            vacation=self.vacation,
            confirmation='HOTEL123',
            name='Test Hotel',
            lodging_type='hotel',
            check_in=date.today(),
            check_out=date.today() + timedelta(days=3)
        )
        self.lodging2 = Lodging.objects.create(
            vacation=self.vacation,
            confirmation='RESORT456',
            name='Test Resort',
            lodging_type='resort',
            check_in=date.today() + timedelta(days=4),
            check_out=date.today() + timedelta(days=7)
        )

    def test_vacation_stays_view_access(self):
        """Test that vacation stays view is accessible"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('vacation_stays', args=[self.vacation.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Stays - Test Destination')

    def test_vacation_stays_timeline_order(self):
        """Test that lodgings are ordered by check-in date in timeline"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('vacation_stays', args=[self.vacation.pk]))
        
        # Check that lodgings are in the context and ordered correctly
        lodgings = response.context['lodgings']
        self.assertEqual(len(lodgings), 2)
        self.assertEqual(lodgings[0], self.lodging1)  # Earlier check-in first
        self.assertEqual(lodgings[1], self.lodging2)

    def test_vacation_stays_shows_lodging_types(self):
        """Test that different lodging types are displayed"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('vacation_stays', args=[self.vacation.pk]))
        
        self.assertContains(response, 'Test Hotel')
        self.assertContains(response, 'Test Resort')
        self.assertContains(response, 'Hotel')  # Display name
        self.assertContains(response, 'Resort')  # Display name

        
        # Create a vacation
        self.vacation = VacationPlan.objects.create(
            owner=self.user,
            destination='Test Destination',
            start_date=date(2024, 6, 15),
            end_date=date(2024, 6, 18),
            trip_type='booked',
            estimated_cost=1000.00
        )
        
        # Create flight
        self.flight = Flight.objects.create(
            vacation=self.vacation,
            airline='Test Airlines',
            confirmation='ABC123',
            departure_airport='NYC',
            arrival_airport='LAX',
            departure_time=timezone.datetime(2024, 6, 15, 10, 30),
            arrival_time=timezone.datetime(2024, 6, 15, 14, 30),
            actual_cost=500.00
        )
        
        # Create lodging
        self.lodging = Lodging.objects.create(
            vacation=self.vacation,
            name='Test Hotel',
            confirmation='DEF456',
            check_in=date(2024, 6, 15),
            check_out=date(2024, 6, 18),
            actual_cost=300.00
        )
        
        # Create activity
        self.activity = Activity.objects.create(
            vacation=self.vacation,
            name='Test Activity',
            date=date(2024, 6, 16),
            start_time=time(14, 0),
            suggested_by=self.user,
            actual_cost=50.00,
            notes='Fun activity to do'
        )

    def test_itinerary_view_requires_login(self):
        """Test that itinerary view requires authentication"""
        url = reverse('vacation_itinerary', kwargs={'pk': self.vacation.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_itinerary_view_with_valid_vacation(self):
        """Test itinerary view with authenticated user and valid vacation"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('vacation_itinerary', kwargs={'pk': self.vacation.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Destination')
        self.assertContains(response, 'Test Airlines')
        self.assertContains(response, 'Test Hotel')
        self.assertContains(response, 'Test Activity')

    def test_itinerary_view_unauthorized_user(self):
        """Test that unauthorized users cannot access vacation itinerary"""
        unauthorized_user = User.objects.create_user(
            username='unauthorized',
            email='unauth@example.com',
            password='testpass123'
        )
        self.client.login(username='unauthorized', password='testpass123')
        url = reverse('vacation_itinerary', kwargs={'pk': self.vacation.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)

    def test_itinerary_context_data(self):
        """Test that itinerary view provides correct context data"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('vacation_itinerary', kwargs={'pk': self.vacation.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('vacation', response.context)
        self.assertIn('itinerary', response.context)
        self.assertIn('total_days', response.context)
        
        # Check that we have 4 days (June 15-18)
        self.assertEqual(response.context['total_days'], 4)
        
        # Check that itinerary is sorted by date
        itinerary = response.context['itinerary']
        self.assertEqual(len(itinerary), 4)
        self.assertEqual(itinerary[0]['date'], date(2024, 6, 15))
        self.assertEqual(itinerary[3]['date'], date(2024, 6, 18))

    def test_itinerary_events_organization(self):
        """Test that events are properly organized by date and time"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('vacation_itinerary', kwargs={'pk': self.vacation.pk})
        response = self.client.get(url)
        
        itinerary = response.context['itinerary']
        
        # June 15 should have flight departure, arrival, and check-in
        june_15_events = itinerary[0]['events']
        self.assertEqual(len(june_15_events), 3)
        
        # Events should be sorted by time
        event_types = [event['type'] for event in june_15_events]
        self.assertIn('flight_departure', event_types)
        self.assertIn('flight_arrival', event_types)
        self.assertIn('lodging_checkin', event_types)
        
        # June 16 should have the activity
        june_16_events = itinerary[1]['events']
        self.assertEqual(len(june_16_events), 1)
        self.assertEqual(june_16_events[0]['type'], 'activity')
        self.assertEqual(june_16_events[0]['title'], 'Test Activity')
        
        # June 18 should have check-out
        june_18_events = itinerary[3]['events']
        self.assertEqual(len(june_18_events), 1)
        self.assertEqual(june_18_events[0]['type'], 'lodging_checkout')

    def test_itinerary_empty_vacation(self):
        """Test itinerary view with vacation that has no events"""
        empty_vacation = VacationPlan.objects.create(
            owner=self.user,
            destination='Empty Vacation',
            start_date=date(2024, 7, 1),
            end_date=date(2024, 7, 3),
            trip_type='planned'
        )
        
        self.client.login(username='testuser', password='testpass123')
        url = reverse('vacation_itinerary', kwargs={'pk': empty_vacation.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Empty Vacation')
        
        # All days should have empty events
        itinerary = response.context['itinerary']
        for day in itinerary:
            self.assertEqual(len(day['events']), 0)

    def test_vacation_detail_has_itinerary_link(self):
        """Test that vacation detail page has link to itinerary"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('vacation_detail', kwargs={'pk': self.vacation.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        itinerary_url = reverse('vacation_itinerary', kwargs={'pk': self.vacation.pk})
        self.assertContains(response, itinerary_url)

