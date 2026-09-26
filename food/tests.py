import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import User
from food.models import FreeFoodEvent


class EventAccessAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='community@example.com',
            password='Password123!',
            first_name='Aarav',
            last_name='Patel'
        )

        today = timezone.localtime().date()
        self.event = FreeFoodEvent.objects.create(
            title='Temple Maha Prasad Feast',
            event_type='Mahaprasad',
            venue_name='Shri Ram Mandir',
            address='Station Road, Nagpur',
            latitude=21.1458,
            longitude=79.0882,
            event_date=today + datetime.timedelta(days=1),
            start_time=datetime.time(12, 0),
            end_time=datetime.time(15, 0),
            food_details='Hot nutritious satvik prasad for all.',
            status=FreeFoodEvent.STATUS_APPROVED,
            submitted_by=self.user
        )

    def test_unauthenticated_user_can_browse_home_page(self):
        """Public homepage renders approved listings without a login gate."""
        response = self.client.get(reverse('food:home'))
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.context['recommended_results']), 0)
        self.assertContains(response, 'Temple Maha Prasad Feast')
        self.assertNotContains(response, 'Member-Exclusive Access')

    def test_authenticated_user_sees_events_on_home_page(self):
        """Authenticated user sees recommended events and filter bar on home page."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('food:home'))
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.context['recommended_results']), 0)
        self.assertContains(response, 'Temple Maha Prasad Feast')
        self.assertNotContains(response, 'Member-Exclusive Access')

    def test_unauthenticated_user_can_access_event_list(self):
        """Public visitors can browse the approved event directory."""
        response = self.client.get(reverse('food:event_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Temple Maha Prasad Feast')

    def test_authenticated_user_can_access_event_list(self):
        """Authenticated user can browse all events."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('food:event_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Temple Maha Prasad Feast')

    def test_unauthenticated_user_can_access_nearby(self):
        """Public visitors can use nearby discovery without location permission."""
        response = self.client.get(reverse('food:nearby_events'))
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_can_access_nearby(self):
        """Authenticated user can access nearby events."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('food:nearby_events'))
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_user_can_access_approved_event_detail(self):
        """Public visitors can open approved event details."""
        url = reverse('food:event_detail', kwargs={'event_id': self.event.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Temple Maha Prasad Feast')

    def test_unauthenticated_user_cannot_access_pending_event_detail(self):
        self.event.status = FreeFoodEvent.STATUS_PENDING
        self.event.save(update_fields=['status'])
        response = self.client.get(reverse('food:event_detail', kwargs={'event_id': self.event.id}))
        self.assertEqual(response.status_code, 404)

    def test_authenticated_user_can_access_event_detail(self):
        """Authenticated user can access event detail view."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('food:event_detail', kwargs={'event_id': self.event.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Temple Maha Prasad Feast')

    def test_unauthenticated_user_can_access_map_view(self):
        """Public visitors can see approved event locations on the map."""
        response = self.client.get(reverse('locations:map_view'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Temple Maha Prasad Feast')

    def test_authenticated_user_can_access_map_view(self):
        """Authenticated user can view map pins."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('locations:map_view'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Temple Maha Prasad Feast')
