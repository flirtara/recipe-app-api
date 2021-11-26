from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    # Helper function to create users
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    # Tests the users API (public)

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        # Test creating user with valid payload is successful.
        payload = {
            'email': 'test@gmail.com',
            'password': 'testpass',
            'name': 'Test name'
        }
        resp = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**resp.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', resp.data)

    def test_user_exists(self):
        # Test creating a user that already exist fails.
        payload = {
            'email': 'test@gmail.com',
            'password': "testpass",
            'name': 'Test name'
        }
        create_user(**payload)
        resp = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_password_too_short(self):
        # Test that the password is more than 8 characters
        payload = {
            'email': 'test@gmail.com',
            'password': 'test1',
            'name': 'Test name',
        }
        resp = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        # Test creating a token for a user
        payload = {
            'email': 'test_token@gmail.com',
            'password': 'test123',
        }
        create_user(**payload)
        resp = self.client.post(TOKEN_URL, payload)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('token', resp.data)

    def test_create_token_invalid_credentials(self):
        # Test that token is not created with invalid credentials.
        payload = {
            'email': 'test_token@gmail.com',
            'password': 'test123',
        }
        create_user(**payload)
        payload = {
            'email': 'test_token@gmail.com',
            'password': 'test999',
        }
        resp = self.client.post(TOKEN_URL, payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', resp.data)

    def test_create_token_no_user(self):
        # Test that token isn't created if user doesn't exist.
        payload = {
            'email': 'test_token@gmail.com',
            'password': 'test123',
        }
        resp = self.client.post(TOKEN_URL, payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', resp.data)

    def test_create_token_missing_field(self):
        # Test that email and password are required.
        payload = {
            'email': 'test_token',
            'password': '',
        }
        resp = self.client.post(TOKEN_URL, payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', resp.data)

    def test_retrieve_user_unauthorized(self):
        # Test that authentication is required for users.
        resp = self.client.get(ME_URL)

        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    # Tests API requests that require authentication

    def setUp(self):
        self.user = create_user(
            email='test@gmail.com',
            password="testpass123",
            name='Private Test User'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        # Test retrieving profile for logged in user.
        resp = self.client.get(ME_URL)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, {
            'name': self.user.name,
            'email': self.user.email
        })

    def test_post_me_not_allowed(self):
        # Test that post is not allowed on the ME Url.
        resp = self.client.post(ME_URL, {})

        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        # Test updating the user profile for authenticated user.
        payload = {
            'name': 'new name',
            'password': "newpassword1234",
        }
        resp = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
