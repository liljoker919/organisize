from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date, time
from django.core.exceptions import ValidationError
from django.urls import reverse, resolve
from planner.models import Group, VacationPlan, Lodging, Flight, Activity
from planner.forms import GroupForm, LodgingForm, VacationPlanForm, FlightForm, ActivityForm


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
        self.vacation = VacationPlan.objects.create(
            owner=self.user,
            destination='Test Destination',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            trip_type='planned'
        )

    def test_lodging_creation(self):
        """Test creating a lodging"""
        lodging = Lodging.objects.create(
            vacation=self.vacation,
            confirmation='TEST123',
            name='Test Hotel',
            lodging_type='hotel',
            check_in=date.today(),
            check_out=date.today() + timedelta(days=3)
        )
        
        self.assertEqual(lodging.vacation, self.vacation)
        self.assertEqual(lodging.confirmation, 'TEST123')
        self.assertEqual(lodging.name, 'Test Hotel')
        self.assertEqual(lodging.lodging_type, 'hotel')

    def test_lodging_validation(self):
        """Test lodging validation"""
        # Test with valid data
        lodging = Lodging(
            vacation=self.vacation,
            confirmation='TEST123',
            name='Test Hotel',
            lodging_type='hotel',
            check_in=date.today(),
            check_out=date.today() + timedelta(days=3)
        )
        lodging.full_clean()  # Should not raise ValidationError
        
        # Test that we can save it
        lodging.save()
        self.assertIsNotNone(lodging.pk)


class FlightModelTest(TestCase):
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
            trip_type='planned'
        )

    def test_flight_creation(self):
        """Test creating a flight"""
        departure_time = timezone.now() + timedelta(days=1)
        arrival_time = departure_time + timedelta(hours=3)
        
        flight = Flight.objects.create(
            vacation=self.vacation,
            airline='Test Airlines',
            confirmation='CONF123',
            departure_airport='LAX',
            arrival_airport='JFK',
            departure_time=departure_time,
            arrival_time=arrival_time,
            actual_cost=299.99
        )
        
        self.assertEqual(flight.vacation, self.vacation)
        self.assertEqual(flight.airline, 'Test Airlines')
        self.assertEqual(flight.confirmation, 'CONF123')
        self.assertEqual(flight.departure_airport, 'LAX')
        self.assertEqual(flight.arrival_airport, 'JFK')
        self.assertEqual(flight.actual_cost, 299.99)


class ActivityModelTest(TestCase):
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
            trip_type='planned'
        )

    def test_activity_creation(self):
        """Test creating an activity"""
        activity = Activity.objects.create(
            vacation=self.vacation,
            name='Test Activity',
            date=date.today() + timedelta(days=2),
            start_time='14:00',
            suggested_by=self.user,
            actual_cost=50.00,
            notes='Test notes'
        )
        
        self.assertEqual(activity.vacation, self.vacation)
        self.assertEqual(activity.name, 'Test Activity')
        self.assertEqual(activity.suggested_by, self.user)
        self.assertEqual(activity.votes, 0)  # Default value
        self.assertEqual(activity.notes, 'Test notes')

    def test_activity_voting(self):
        """Test activity voting functionality"""
        activity = Activity.objects.create(
            vacation=self.vacation,
            name='Test Activity',
            date=date.today() + timedelta(days=2),
            start_time='14:00',
            suggested_by=self.user
        )
        
        # Test initial state
        self.assertEqual(activity.votes, 0)
        self.assertEqual(activity.voted_users.count(), 0)
        
        # Test adding vote
        activity.votes = 1
        activity.voted_users.add(self.user)
        activity.save()
        
        self.assertEqual(activity.votes, 1)
        self.assertEqual(activity.voted_users.count(), 1)
        self.assertIn(self.user, activity.voted_users.all())


class VacationPlanModelTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_vacation_plan_creation(self):
        """Test creating a vacation plan"""
        vacation = VacationPlan.objects.create(
            owner=self.user,
            destination='Paris, France',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=37),
            trip_type='planned',
            estimated_cost=2500.00,
            notes='Romantic getaway',
            whos_going='John and Jane'
        )
        
        self.assertEqual(vacation.owner, self.user)
        self.assertEqual(vacation.destination, 'Paris, France')
        self.assertEqual(vacation.trip_type, 'planned')
        self.assertEqual(vacation.estimated_cost, 2500.00)
        self.assertEqual(vacation.notes, 'Romantic getaway')
        self.assertEqual(vacation.whos_going, 'John and Jane')

    def test_vacation_plan_validation(self):
        """Test vacation plan validation"""
        # Test valid vacation
        vacation = VacationPlan(
            owner=self.user,
            destination='Paris, France',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=37),
            trip_type='planned'
        )
        vacation.full_clean()  # Should not raise ValidationError
        
        # Test invalid vacation (end date before start date)
        invalid_vacation = VacationPlan(
            owner=self.user,
            destination='Invalid Trip',
            start_date=date.today() + timedelta(days=37),
            end_date=date.today() + timedelta(days=30),
            trip_type='planned'
        )
        
        with self.assertRaises(ValidationError):
            invalid_vacation.full_clean()

    def test_vacation_plan_str_method(self):
        """Test string representation of vacation plan"""
        vacation = VacationPlan.objects.create(
            owner=self.user,
            destination='Tokyo, Japan',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=37),
            trip_type='booked'
        )
        
        self.assertEqual(str(vacation), 'Tokyo, Japan')

    def test_vacation_plan_sharing(self):
        """Test vacation plan sharing functionality"""
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        vacation = VacationPlan.objects.create(
            owner=self.user,
            destination='Shared Trip',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=37),
            trip_type='planned'
        )
        
        # Initially no shared users
        self.assertEqual(vacation.shared_with.count(), 0)
        
        # Add shared user
        vacation.shared_with.add(user2)
        self.assertEqual(vacation.shared_with.count(), 1)
        self.assertIn(user2, vacation.shared_with.all())


class VacationPlanFormTest(TestCase):
    def test_vacation_plan_form_valid_data(self):
        """Test VacationPlanForm with valid data"""
        form_data = {
            'destination': 'Paris, France',
            'start_date': date.today() + timedelta(days=30),
            'end_date': date.today() + timedelta(days=37),
            'trip_type': 'planned',
            'estimated_cost': 2500.00,
            'notes': 'Romantic getaway',
            'whos_going': 'John and Jane',
            'share_with_emails': 'test@example.com'
        }
        
        form = VacationPlanForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_vacation_plan_form_invalid_data(self):
        """Test VacationPlanForm with invalid data"""
        form_data = {
            'destination': '',  # Required field empty
            'start_date': date.today() + timedelta(days=37),
            'end_date': date.today() + timedelta(days=30),  # End before start
            'trip_type': 'invalid_type'
        }
        
        form = VacationPlanForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('destination', form.errors)


class FlightFormTest(TestCase):
    def test_flight_form_valid_data(self):
        """Test FlightForm with valid data"""
        departure_time = timezone.now() + timedelta(days=1)
        arrival_time = departure_time + timedelta(hours=3)
        
        form_data = {
            'airline': 'Test Airlines',
            'confirmation': 'CONF123',
            'departure_airport': 'LAX',
            'arrival_airport': 'JFK',
            'departure_time': departure_time.strftime('%Y-%m-%dT%H:%M'),
            'arrival_time': arrival_time.strftime('%Y-%m-%dT%H:%M'),
            'actual_cost': 299.99
        }
        
        form = FlightForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_flight_form_required_fields(self):
        """Test FlightForm required fields"""
        form = FlightForm(data={})
        self.assertFalse(form.is_valid())
        
        # Check that required fields are present in errors
        required_fields = ['airline', 'confirmation', 'departure_airport', 'arrival_airport']
        for field in required_fields:
            self.assertIn(field, form.errors)


class ActivityFormTest(TestCase):
    def test_activity_form_valid_data(self):
        """Test ActivityForm with valid data"""
        form_data = {
            'name': 'Visit Eiffel Tower',
            'date': date.today() + timedelta(days=5),
            'start_time': '14:00',
            'actual_cost': 25.00,
            'notes': 'Bring camera'
        }
        
        form = ActivityForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_activity_form_required_fields(self):
        """Test ActivityForm required fields"""
        form = ActivityForm(data={})
        self.assertFalse(form.is_valid())
        
        # Check that required fields are in errors
        self.assertIn('name', form.errors)
        self.assertIn('date', form.errors)
        self.assertIn('start_time', form.errors)


class LodgingFormTest(TestCase):
    def test_lodging_form_valid_data(self):
        """Test LodgingForm with valid data"""
        form_data = {
            'confirmation': 'HOTEL123',
            'name': 'Grand Hotel',
            'lodging_type': 'hotel',
            'check_in': date.today() + timedelta(days=5),
            'check_out': date.today() + timedelta(days=8),
            'actual_cost': 150.00
        }
        
        form = LodgingForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_lodging_form_required_fields(self):
        """Test LodgingForm required fields"""
        form = LodgingForm(data={})
        self.assertFalse(form.is_valid())
        
        # Check that required fields are in errors
        required_fields = ['confirmation', 'name', 'check_in', 'check_out']
        for field in required_fields:
            self.assertIn(field, form.errors)


class URLRoutingTest(TestCase):
    """Test URL routing and resolution"""
    
    def test_vacation_list_url(self):
        """Test vacation list URL resolution"""
        url = reverse('vacation_list')
        self.assertEqual(url, '/vacations/')
        
    def test_create_vacation_url(self):
        """Test create vacation URL resolution"""
        url = reverse('create_vacation')
        self.assertEqual(url, '/vacations/create/')
        
    def test_vacation_detail_url(self):
        """Test vacation detail URL resolution"""
        url = reverse('vacation_detail', kwargs={'pk': 1})
        self.assertEqual(url, '/vacations/1/')
        
    def test_vacation_itinerary_url(self):
        """Test vacation itinerary URL resolution"""
        url = reverse('vacation_itinerary', kwargs={'pk': 1})
        self.assertEqual(url, '/vacations/1/itinerary/')
        
    def test_add_flight_url(self):
        """Test add flight URL resolution"""
        url = reverse('add_flight', kwargs={'pk': 1})
        self.assertEqual(url, '/vacations/1/add-flight/')
        
    def test_add_lodging_url(self):
        """Test add lodging URL resolution"""
        url = reverse('add_lodging', kwargs={'pk': 1})
        self.assertEqual(url, '/vacations/1/add-lodging/')
        
    def test_add_activity_url(self):
        """Test add activity URL resolution"""
        url = reverse('add_activity', kwargs={'pk': 1})
        self.assertEqual(url, '/vacations/1/add-activity/')
        
    def test_group_list_url(self):
        """Test group list URL resolution"""
        url = reverse('group_list')
        self.assertEqual(url, '/vacations/groups/')


class ViewTest(TestCase):
    """Test view functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        
        self.vacation = VacationPlan.objects.create(
            owner=self.user,
            destination='Test Destination',
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=7),
            trip_type='planned'
        )

    def test_vacation_list_view_unauthenticated(self):
        """Test vacation list view redirects unauthenticated users"""
        response = self.client.get(reverse('vacation_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_vacation_list_view_authenticated(self):
        """Test vacation list view for authenticated users"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('vacation_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Destination')

    def test_vacation_detail_view(self):
        """Test vacation detail view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('vacation_detail', kwargs={'pk': self.vacation.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Destination')

    def test_vacation_detail_view_unauthorized(self):
        """Test vacation detail view for unauthorized user"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        self.client.login(username='otheruser', password='otherpass123')
        response = self.client.get(reverse('vacation_detail', kwargs={'pk': self.vacation.pk}))
        self.assertEqual(response.status_code, 404)

    def test_create_vacation_view_get(self):
        """Test create vacation view GET request"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('create_vacation'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Vacation')

    def test_create_vacation_view_post(self):
        """Test create vacation view POST request"""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'destination': 'New York',
            'start_date': (date.today() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'end_date': (date.today() + timedelta(days=37)).strftime('%Y-%m-%d'),
            'trip_type': 'planned',
            'estimated_cost': '1500.00',
            'notes': 'Business trip',
            'whos_going': 'John Doe'
        }
        
        response = self.client.post(reverse('create_vacation'), data=form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        
        # Verify vacation was created
        vacation = VacationPlan.objects.filter(destination='New York').first()
        self.assertIsNotNone(vacation)
        self.assertEqual(vacation.owner, self.user)

    def test_vacation_itinerary_view(self):
        """Test vacation itinerary view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('vacation_itinerary', kwargs={'pk': self.vacation.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Itinerary')

    def test_add_flight_view_get(self):
        """Test add flight view GET request"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('add_flight', kwargs={'pk': self.vacation.pk}))
        self.assertEqual(response.status_code, 200)

    def test_add_flight_view_post(self):
        """Test add flight view POST request"""
        self.client.login(username='testuser', password='testpass123')
        
        departure_time = timezone.now() + timedelta(days=2)
        arrival_time = departure_time + timedelta(hours=3)
        
        form_data = {
            'airline': 'Test Airlines',
            'confirmation': 'CONF123',
            'departure_airport': 'LAX',
            'arrival_airport': 'JFK',
            'departure_time': departure_time.strftime('%Y-%m-%dT%H:%M'),
            'arrival_time': arrival_time.strftime('%Y-%m-%dT%H:%M'),
            'actual_cost': '299.99'
        }
        
        response = self.client.post(reverse('add_flight', kwargs={'pk': self.vacation.pk}), data=form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        
        # Verify flight was created
        flight = Flight.objects.filter(vacation=self.vacation).first()
        self.assertIsNotNone(flight)
        self.assertEqual(flight.airline, 'Test Airlines')

    def test_add_lodging_view_get(self):
        """Test add lodging view GET request"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('add_lodging', kwargs={'pk': self.vacation.pk}))
        self.assertEqual(response.status_code, 200)

    def test_add_lodging_view_post(self):
        """Test add lodging view POST request"""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'confirmation': 'HOTEL123',
            'name': 'Grand Hotel',
            'lodging_type': 'hotel',
            'check_in': (date.today() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'check_out': (date.today() + timedelta(days=5)).strftime('%Y-%m-%d'),
            'actual_cost': '150.00'
        }
        
        response = self.client.post(reverse('add_lodging', kwargs={'pk': self.vacation.pk}), data=form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        
        # Verify lodging was created
        lodging = Lodging.objects.filter(vacation=self.vacation).first()
        self.assertIsNotNone(lodging)
        self.assertEqual(lodging.name, 'Grand Hotel')

    def test_add_activity_view_get(self):
        """Test add activity view GET request"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('add_activity', kwargs={'pk': self.vacation.pk}))
        self.assertEqual(response.status_code, 200)

    def test_add_activity_view_post(self):
        """Test add activity view POST request"""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'name': 'Visit Museum',
            'date': (date.today() + timedelta(days=3)).strftime('%Y-%m-%d'),
            'start_time': '14:00',
            'actual_cost': '25.00',
            'notes': 'Educational visit'
        }
        
        response = self.client.post(reverse('add_activity', kwargs={'pk': self.vacation.pk}), data=form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        
        # Verify activity was created
        activity = Activity.objects.filter(vacation=self.vacation).first()
        self.assertIsNotNone(activity)
        self.assertEqual(activity.name, 'Visit Museum')
        self.assertEqual(activity.suggested_by, self.user)

    def test_group_list_view(self):
        """Test group list view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('group_list'))
        self.assertEqual(response.status_code, 200)

    def test_create_group_view_get(self):
        """Test create group view GET request"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('create_group'))
        self.assertEqual(response.status_code, 200)



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
        
        # Create vacation with specific dates for itinerary tests (June 15-18, 4 days)
        self.vacation = VacationPlan.objects.create(
            owner=self.user,
            destination='Test Destination',
            start_date=date(2024, 6, 15),
            end_date=date(2024, 6, 18),
            trip_type='booked',
            estimated_cost=1000.00
        )
        
        # Create flight for itinerary tests
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
        
        # Create lodging for itinerary tests
        self.lodging = Lodging.objects.create(
            vacation=self.vacation,
            name='Test Hotel',
            confirmation='DEF456',
            lodging_type='hotel',
            check_in=date(2024, 6, 15),
            check_out=date(2024, 6, 18),
            actual_cost=300.00
        )
        
        # Create activity for itinerary tests
        self.activity = Activity.objects.create(
            vacation=self.vacation,
            name='Test Activity',
            date=date(2024, 6, 16),
            start_time=time(14, 0),
            suggested_by=self.user,
            actual_cost=50.00,
            notes='Fun activity to do'
        )
        
        # Create additional lodging for vacation stays tests
        self.lodging1 = self.lodging  # Use the main lodging as lodging1
        self.lodging2 = Lodging.objects.create(
            vacation=self.vacation,
            confirmation='RESORT456',
            name='Test Resort',
            lodging_type='resort',
            check_in=date(2024, 6, 19),  # After the vacation ends, but for stays timeline test
            check_out=date(2024, 6, 22),
            actual_cost=400.00
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

