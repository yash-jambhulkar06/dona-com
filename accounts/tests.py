from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User


class SimpleAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:login')
        self.logout_url = reverse('accounts:logout')

    def test_registration_success(self):
        data = {
            'full_name': 'Aarav Sharma',
            'email': 'aarav@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
        }
        response = self.client.post(self.register_url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # User created
        user = User.objects.filter(email='aarav@example.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.first_name, 'Aarav')
        self.assertEqual(user.last_name, 'Sharma')
        self.assertEqual(user.full_name, 'Aarav Sharma')
        self.assertTrue(user.check_password('password123'))
        
        # User is authenticated in session
        self.assertEqual(int(self.client.session['_auth_user_id'] == str(user.id)), 1)

    def test_registration_password_mismatch(self):
        data = {
            'full_name': 'Rohit Kumar',
            'email': 'rohit@example.com',
            'password': 'password123',
            'confirm_password': 'differentpassword',
        }
        response = self.client.post(self.register_url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'confirm_password', 'Passwords do not match.')
        self.assertFalse(User.objects.filter(email='rohit@example.com').exists())

    def test_registration_duplicate_email(self):
        User.objects.create_user(email='existing@example.com', password='password123', first_name='Existing')
        data = {
            'full_name': 'Another Person',
            'email': 'existing@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
        }
        response = self.client.post(self.register_url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'email', 'An account with this email address already exists. Please sign in.')

    def test_login_success(self):
        User.objects.create_user(email='testuser@example.com', password='mysecretpassword', first_name='Test')
        data = {
            'email': 'testuser@example.com',
            'password': 'mysecretpassword',
        }
        response = self.client.post(self.login_url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(email='testuser@example.com')
        self.assertEqual(self.client.session['_auth_user_id'], str(user.id))

    def test_login_invalid_password(self):
        User.objects.create_user(email='testuser2@example.com', password='mysecretpassword')
        data = {
            'email': 'testuser2@example.com',
            'password': 'wrongpassword',
        }
        response = self.client.post(self.login_url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)

    def test_logout(self):
        user = User.objects.create_user(email='logout@example.com', password='password123')
        self.client.login(username='logout@example.com', password='password123')
        response = self.client.get(self.logout_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
