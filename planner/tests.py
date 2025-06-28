from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date, time, datetime
from django.core.exceptions import ValidationError
from django.urls import reverse
from planner.models import Group, VacationPlan, Lodging, Transportation, Activity
from planner.forms import GroupForm, LodgingForm, TransportationForm, VacationPlanForm, ActivityForm, CustomUserCreationForm




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

    def test_vacation_detail_view_has_section_icons(self):
        """Test that vacation detail view contains icons for all sections"""
        # Create a booked vacation since icons are only shown for booked trips
        booked_vacation = VacationPlan.objects.create(
            owner=self.user,
            destination='Test Booked Destination',
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=7),
            trip_type='booked'
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('vacation_detail', kwargs={'pk': booked_vacation.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Check that section icons are present
        self.assertContains(response, 'bi bi-airplane')  # Transportation icon
        self.assertContains(response, 'bi bi-star')  # Activities icon
        self.assertContains(response, 'bi bi-house-door')  # Stays icon

    def test_vacation_detail_view_unauthorized(self):
        """Test vacation detail view for unauthorized user"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        self.client.login(username='otheruser', password='otherpass123')
        response = self.client.get(reverse('vacation_detail', kwargs={'pk': self.vacation.pk}))
        self.assertEqual(response.status_code, 403)

    def test_invite_users_by_email(self):
        """Test inviting users via email addresses"""
        # Create a user with an email that we'll invite
        existing_user = User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='testpass123'
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        # Test inviting existing user by email
        response = self.client.post(
            reverse('invite_users', kwargs={'pk': self.vacation.pk}),
            {'invite_emails': 'existing@example.com'}
        )
        
        self.assertRedirects(response, reverse('vacation_detail', kwargs={'pk': self.vacation.pk}))
        
        # Check that the existing user was added to the vacation
        self.assertIn(existing_user, self.vacation.shared_with.all())
        
        # Test inviting non-existing email (should be noted for future)
        response = self.client.post(
            reverse('invite_users', kwargs={'pk': self.vacation.pk}),
            {'invite_emails': 'nonexisting@example.com'}
        )
        
        self.assertRedirects(response, reverse('vacation_detail', kwargs={'pk': self.vacation.pk}))
        
        # Test multiple emails
        new_user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='testpass123'
        )
        
        response = self.client.post(
            reverse('invite_users', kwargs={'pk': self.vacation.pk}),
            {'invite_emails': 'newuser@example.com, another@example.com'}
        )
        
        self.assertRedirects(response, reverse('vacation_detail', kwargs={'pk': self.vacation.pk}))
        self.assertIn(new_user, self.vacation.shared_with.all())
        
        # Test invalid email
        response = self.client.post(
            reverse('invite_users', kwargs={'pk': self.vacation.pk}),
            {'invite_emails': 'invalid-email'}
        )
        
        self.assertRedirects(response, reverse('vacation_detail', kwargs={'pk': self.vacation.pk}))
        
        # Test empty email
        response = self.client.post(
            reverse('invite_users', kwargs={'pk': self.vacation.pk}),
            {'invite_emails': ''}
        )
        
        self.assertRedirects(response, reverse('vacation_detail', kwargs={'pk': self.vacation.pk}))

    def test_create_vacation_view_get(self):
        """Test create vacation view GET request"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('create_vacation'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create a New Vacation')

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

    def test_add_lodging_view_get(self):
        """Test add lodging view GET request returns Method Not Allowed"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('add_lodging', kwargs={'pk': self.vacation.pk}))
        self.assertEqual(response.status_code, 405)  # Method Not Allowed



class VacationItineraryTestWithEvents(TestCase):
    def setUp(self):
        """Set up test data for itinerary tests with events"""

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
        """Test add activity view GET request returns Method Not Allowed"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('add_activity', kwargs={'pk': self.vacation.pk}))
        self.assertEqual(response.status_code, 405)  # Method Not Allowed

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
        
        # Create transportation
        self.transportation = Transportation.objects.create(
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
        
        self.assertEqual(response.status_code, 403)

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
        
        # June 15 should have transportation departure, arrival, and check-in
        june_15_events = itinerary[0]['events']
        self.assertEqual(len(june_15_events), 3)
        
        # Events should be sorted by time
        event_types = [event['type'] for event in june_15_events]
        self.assertIn('flight_departure', event_types)  # transportation type is 'flight'
        self.assertIn('flight_arrival', event_types)    # transportation type is 'flight'
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
            departure_time=timezone.make_aware(datetime(2024, 6, 15, 10, 30)),
            arrival_time=timezone.make_aware(datetime(2024, 6, 15, 14, 30)),
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
            departure_time=timezone.make_aware(datetime(2024, 6, 16, 8, 0)),
            arrival_time=timezone.make_aware(datetime(2024, 6, 16, 16, 0)),
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
            departure_time=timezone.make_aware(datetime(2024, 6, 16, 12, 0)),
            arrival_time=timezone.make_aware(datetime(2024, 6, 16, 18, 0)),
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
            'departure_time': timezone.make_aware(datetime(2024, 6, 17, 10, 0)).strftime('%Y-%m-%dT%H:%M'),
            'arrival_time': timezone.make_aware(datetime(2024, 6, 17, 12, 0)).strftime('%Y-%m-%dT%H:%M'),
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
            departure_time=timezone.make_aware(datetime(2024, 6, 15, 15, 0)),
            arrival_time=timezone.make_aware(datetime(2024, 6, 15, 16, 0)),
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
            departure_time=timezone.make_aware(datetime(2024, 6, 15, 12, 0)),
            arrival_time=timezone.make_aware(datetime(2024, 6, 15, 16, 0)),
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
        
        # Create a transportation entry
        transportation = Transportation.objects.create(
            vacation=vacation,
            transportation_type='flight',
            provider='Test Airlines',
            confirmation='TR123',
            departure_location='NYC',
            arrival_location='LAX',
            departure_time=timezone.make_aware(datetime(2024, 6, 15, 10, 0)),
            arrival_time=timezone.make_aware(datetime(2024, 6, 15, 14, 0)),
            actual_cost=500.00
        )
        
        # Check that transportation data works correctly
        self.assertEqual(transportation.transportation_type, 'flight')
        self.assertEqual(transportation.provider, 'Test Airlines')
        self.assertEqual(transportation.departure_location, 'NYC')
        self.assertEqual(str(transportation), 'Flight: NYC → LAX')


class RegistrationFormTest(TestCase):
    """Test CustomUserCreationForm functionality"""
    
    def test_registration_form_valid_data(self):
        """Test registration form with valid data"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_registration_form_email_required(self):
        """Test that email field is required"""
        form_data = {
            'username': 'testuser',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_registration_form_duplicate_email(self):
        """Test that duplicate email addresses are rejected"""
        # Create existing user
        User.objects.create_user(
            username='existing_user',
            email='test@example.com',
            password='password123'
        )
        
        # Try to register with same email
        form_data = {
            'username': 'newuser',
            'email': 'test@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_registration_form_password_mismatch(self):
        """Test that password mismatch is caught"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'DifferentPass456!'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_registration_form_saves_email(self):
        """Test that form saves user with email"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('ComplexPass123!'))


class RegistrationViewTest(TestCase):
    """Test registration view functionality"""
    
    def setUp(self):
        self.client = Client()

    def test_registration_view_get(self):
        """Test GET request to registration view"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Register')
        self.assertContains(response, 'form')

    def test_registration_view_post_valid(self):
        """Test POST request with valid registration data"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        }
        
        response = self.client.post(reverse('register'), data=form_data)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))
        
        # User should be created
        self.assertTrue(User.objects.filter(username='newuser').exists())
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@example.com')

    def test_registration_view_post_invalid(self):
        """Test POST request with invalid registration data"""
        form_data = {
            'username': 'newuser',
            'email': 'invalid-email',
            'password1': 'ComplexPass123!',
            'password2': 'DifferentPass456!'
        }
        
        response = self.client.post(reverse('register'), data=form_data)
        
        # Should stay on registration page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Register')
        
        # User should not be created
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_registration_url_resolution(self):
        """Test that registration URL resolves correctly"""
        url = reverse('register')
        self.assertEqual(url, '/accounts/register/')

    def test_registration_template_links(self):
        """Test that registration page has proper links"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        
        # Should have link to login
        self.assertContains(response, reverse('login'))
        self.assertContains(response, 'Sign in here')

    def test_login_template_has_register_link(self):
        """Test that login page has link to registration"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        
        # Should have link to register
        self.assertContains(response, reverse('register'))
        self.assertContains(response, 'Register here')

    def test_navbar_has_register_link_when_not_authenticated(self):
        """Test that navbar shows register link for unauthenticated users"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        
        # Should have register link in navbar
        self.assertContains(response, reverse('register'))
        self.assertContains(response, 'Register')

    def test_registration_success_message(self):
        """Test that success message is shown after registration"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        }
        
        response = self.client.post(reverse('register'), data=form_data, follow=True)
        
        # Should show success message
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('Account created for newuser', str(messages[0]))
        self.assertIn('You can now log in', str(messages[0]))

    def test_authenticated_user_redirected_from_register_get(self):
        """Test that authenticated users are redirected from register page (GET)"""
        # Create and login a user
        user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        
        # Try to access register page
        response = self.client.get(reverse('register'))
        
        # Should be redirected to vacation list
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('vacation_list'))

    def test_authenticated_user_redirected_from_register_post(self):
        """Test that authenticated users are redirected from register page (POST)"""
        # Create and login a user
        user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        
        # Try to submit registration form
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        }
        response = self.client.post(reverse('register'), data=form_data)
        
        # Should be redirected to vacation list
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('vacation_list'))
        
        # User should NOT be created
        self.assertFalse(User.objects.filter(username='newuser').exists())


class AccessDeniedTestCase(TestCase):
    """Test cases for 403 Access Denied functionality"""

    def setUp(self):
        """Create test users and vacation for access control testing"""
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='ownerpass123'
        )
        self.unauthorized_user = User.objects.create_user(
            username='unauthorized',
            email='unauthorized@example.com',
            password='unauthorizedpass123'
        )
        self.shared_user = User.objects.create_user(
            username='shared',
            email='shared@example.com',
            password='sharedpass123'
        )
        
        # Create a vacation owned by owner
        self.vacation = VacationPlan.objects.create(
            title='Private Test Vacation',
            destination='Secret Island',
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=17),
            owner=self.owner,
            estimated_cost=1000.00
        )
        
        # Share vacation with shared_user
        self.vacation.shared_with.add(self.shared_user)

    def test_vacation_detail_unauthorized_access_returns_403(self):
        """Test that unauthorized users get 403 for vacation detail view"""
        self.client.login(username='unauthorized', password='unauthorizedpass123')
        response = self.client.get(reverse('vacation_detail', kwargs={'pk': self.vacation.pk}))
        self.assertEqual(response.status_code, 403)

    def test_vacation_detail_owner_access_returns_200(self):
        """Test that vacation owner can access vacation detail view"""
        self.client.login(username='owner', password='ownerpass123')
        response = self.client.get(reverse('vacation_detail', kwargs={'pk': self.vacation.pk}))
        self.assertEqual(response.status_code, 200)

    def test_vacation_detail_shared_user_access_returns_200(self):
        """Test that shared users can access vacation detail view"""
        self.client.login(username='shared', password='sharedpass123')
        response = self.client.get(reverse('vacation_detail', kwargs={'pk': self.vacation.pk}))
        self.assertEqual(response.status_code, 200)

    def test_vacation_itinerary_unauthorized_access_returns_403(self):
        """Test that unauthorized users get 403 for vacation itinerary view"""
        self.client.login(username='unauthorized', password='unauthorizedpass123')
        response = self.client.get(reverse('vacation_itinerary', kwargs={'pk': self.vacation.pk}))
        self.assertEqual(response.status_code, 403)

    def test_vacation_itinerary_owner_access_returns_200(self):
        """Test that vacation owner can access vacation itinerary view"""
        self.client.login(username='owner', password='ownerpass123')
        response = self.client.get(reverse('vacation_itinerary', kwargs={'pk': self.vacation.pk}))
        self.assertEqual(response.status_code, 200)

    def test_vacation_stays_unauthorized_access_returns_403(self):
        """Test that unauthorized users get 403 for vacation stays view"""
        self.client.login(username='unauthorized', password='unauthorizedpass123')
        response = self.client.get(reverse('vacation_stays', kwargs={'pk': self.vacation.pk}))
        self.assertEqual(response.status_code, 403)

    def test_vacation_nonexistent_returns_404(self):
        """Test that accessing non-existent vacation returns 404, not 403"""
        self.client.login(username='unauthorized', password='unauthorizedpass123')
        response = self.client.get(reverse('vacation_detail', kwargs={'pk': 999999}))
        self.assertEqual(response.status_code, 404)

    def test_403_template_contains_access_denied_message(self):
        """Test that 403 page contains appropriate access denied message"""
        self.client.login(username='unauthorized', password='unauthorizedpass123')
        response = self.client.get(reverse('vacation_detail', kwargs={'pk': self.vacation.pk}))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Access Denied', status_code=403)
        self.assertContains(response, 'permission', status_code=403)
        self.assertContains(response, 'My Vacations', status_code=403)


