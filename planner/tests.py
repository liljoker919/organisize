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
