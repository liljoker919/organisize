from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date, time
from django.core.exceptions import ValidationError
from django.urls import reverse
from planner.models import Group, VacationPlan, Lodging, Flight, Transportation
from planner.forms import GroupForm, LodgingForm, TransportationForm


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
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )


class VacationItineraryTest(TestCase):
    def setUp(self):
        """Set up test data for itinerary tests"""
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


class VacationItineraryTestWithEvents(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
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


class TransportationModelTest(TestCase):
    def setUp(self):
        """Set up test data for transportation tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a vacation
        self.vacation = VacationPlan.objects.create(
            owner=self.user,
            destination='Test Destination',
            start_date=date(2024, 6, 15),
            end_date=date(2024, 6, 18),
            trip_type='booked',
            estimated_cost=1000.00
        )

    def test_transportation_creation_flight(self):
        """Test creating a flight transportation"""
        transportation = Transportation.objects.create(
            vacation=self.vacation,
            transportation_type='flight',
            provider='Test Airlines',
            confirmation='ABC123',
            departure_location='NYC',
            arrival_location='LAX',
            departure_time=timezone.datetime(2024, 6, 15, 10, 30),
            arrival_time=timezone.datetime(2024, 6, 15, 14, 30),
            actual_cost=500.00
        )
        
        self.assertEqual(transportation.transportation_type, 'flight')
        self.assertEqual(transportation.provider, 'Test Airlines')
        self.assertEqual(transportation.get_transportation_type_display(), 'Flight')
        self.assertEqual(str(transportation), 'Flight: NYC → LAX')

    def test_transportation_creation_train(self):
        """Test creating a train transportation"""
        transportation = Transportation.objects.create(
            vacation=self.vacation,
            transportation_type='train',
            provider='Amtrak',
            confirmation='TRAIN456',
            departure_location='Union Station',
            arrival_location='Penn Station',
            departure_time=timezone.datetime(2024, 6, 16, 8, 0),
            arrival_time=timezone.datetime(2024, 6, 16, 16, 0),
            actual_cost=150.00
        )
        
        self.assertEqual(transportation.transportation_type, 'train')
        self.assertEqual(transportation.provider, 'Amtrak')
        self.assertEqual(transportation.get_transportation_type_display(), 'Train')
        self.assertEqual(str(transportation), 'Train: Union Station → Penn Station')

    def test_transportation_creation_bus(self):
        """Test creating a bus transportation"""
        transportation = Transportation.objects.create(
            vacation=self.vacation,
            transportation_type='bus',
            provider='Greyhound',
            confirmation='BUS789',
            departure_location='Downtown Terminal',
            arrival_location='City Center Terminal',
            departure_time=timezone.datetime(2024, 6, 16, 12, 0),
            arrival_time=timezone.datetime(2024, 6, 16, 18, 0),
            actual_cost=75.00
        )
        
        self.assertEqual(transportation.transportation_type, 'bus')
        self.assertEqual(transportation.provider, 'Greyhound')
        self.assertEqual(transportation.get_transportation_type_display(), 'Bus')
        self.assertEqual(str(transportation), 'Bus: Downtown Terminal → City Center Terminal')

    def test_transportation_form_validation(self):
        """Test that TransportationForm validates correctly"""
        form_data = {
            'transportation_type': 'ferry',
            'provider': 'Ferry Lines',
            'confirmation': 'FERRY123',
            'departure_location': 'Port A',
            'arrival_location': 'Port B',
            'departure_time': timezone.datetime(2024, 6, 17, 10, 0).strftime('%Y-%m-%dT%H:%M'),
            'arrival_time': timezone.datetime(2024, 6, 17, 12, 0).strftime('%Y-%m-%dT%H:%M'),
            'actual_cost': '100.00'
        }
        form = TransportationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_transportation_vacation_relationship(self):
        """Test the relationship between Transportation and VacationPlan"""
        transportation = Transportation.objects.create(
            vacation=self.vacation,
            transportation_type='car',
            provider='Hertz',
            confirmation='CAR999',
            departure_location='Airport Rental',
            arrival_location='Hotel',
            departure_time=timezone.datetime(2024, 6, 15, 15, 0),
            arrival_time=timezone.datetime(2024, 6, 15, 16, 0),
            actual_cost=200.00
        )
        
        # Test forward relationship
        self.assertEqual(transportation.vacation, self.vacation)
        
        # Test reverse relationship
        transportations = self.vacation.transportations.all()
        self.assertIn(transportation, transportations)
        self.assertEqual(transportations.count(), 1)


class TransportationViewTest(TestCase):
    def setUp(self):
        """Set up test data for transportation view tests"""
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

    def test_add_transportation_view(self):
        """Test adding transportation via POST"""
        self.client.login(username='testuser', password='testpass123')
        
        transportation_data = {
            'transportation_type': 'train',
            'provider': 'Test Train Co',
            'confirmation': 'TRN123',
            'departure_location': 'Station A',
            'arrival_location': 'Station B',
            'departure_time': '2024-06-15T10:00',
            'arrival_time': '2024-06-15T14:00',
            'actual_cost': '150.00'
        }
        
        response = self.client.post(
            reverse('add_transportation', args=[self.vacation.pk]),
            data=transportation_data
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertTrue(Transportation.objects.filter(vacation=self.vacation).exists())
        
        transportation = Transportation.objects.get(vacation=self.vacation)
        self.assertEqual(transportation.transportation_type, 'train')
        self.assertEqual(transportation.provider, 'Test Train Co')

    def test_vacation_detail_shows_transportation(self):
        """Test that vacation detail page shows transportation entries"""
        # Create transportation
        Transportation.objects.create(
            vacation=self.vacation,
            transportation_type='bus',
            provider='Test Bus Lines',
            confirmation='BUS456',
            departure_location='Terminal A',
            arrival_location='Terminal B',
            departure_time=timezone.datetime(2024, 6, 15, 12, 0),
            arrival_time=timezone.datetime(2024, 6, 15, 16, 0),
            actual_cost=75.00
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('vacation_detail', args=[self.vacation.pk]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Transportation')
        self.assertContains(response, 'Test Bus Lines')
        self.assertContains(response, 'Terminal A → Terminal B')
        self.assertContains(response, 'Bus')
        self.assertContains(response, 'BUS456')


class DataMigrationTest(TestCase):
    def test_transportation_migration_compatibility(self):
        """Test that data migration works correctly"""
        # Create a vacation
        user = User.objects.create_user(username='testuser', password='test')
        vacation = VacationPlan.objects.create(
            owner=user,
            destination='Test',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=3),
            trip_type='booked'
        )
        
        # Create a flight (legacy)
        flight = Flight.objects.create(
            vacation=vacation,
            airline='Test Airlines',
            confirmation='FL123',
            departure_airport='NYC',
            arrival_airport='LAX',
            departure_time=timezone.datetime(2024, 6, 15, 10, 0),
            arrival_time=timezone.datetime(2024, 6, 15, 14, 0),
            actual_cost=500.00
        )
        
        # Check that we can access the flight data
        self.assertEqual(flight.airline, 'Test Airlines')
        self.assertEqual(flight.departure_airport, 'NYC')
        
        # Create a transportation entry
        transportation = Transportation.objects.create(
            vacation=vacation,
            transportation_type='flight',
            provider='Test Airlines',
            confirmation='TR123',
            departure_location='NYC',
            arrival_location='LAX',
            departure_time=timezone.datetime(2024, 6, 15, 10, 0),
            arrival_time=timezone.datetime(2024, 6, 15, 14, 0),
            actual_cost=500.00
        )
        
        # Check that transportation data works correctly
        self.assertEqual(transportation.transportation_type, 'flight')
        self.assertEqual(transportation.provider, 'Test Airlines')
        self.assertEqual(transportation.departure_location, 'NYC')
        self.assertEqual(str(transportation), 'Flight: NYC → LAX')

