"""
Tests for the user API
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    """
    Helper function to create a user
    """
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """
    Test the users API (public)
    """

    def setUp(self):
        """
        Setup
        """
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """
        Test creating user with valid payload is successful
        """
        payload = {
            "email": 'user@example.com',
            "password": 'test_user12345',
            "name": 'Test User',
        }
        response = self.client.post(path=CREATE_USER_URL, data=payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', response.data)

    def test_user_exists(self):
        """
        Test creating a user that already exists fails
        """
        payload = {
            "email": 'user@example.com',
            "password": 'test123',
            "name": 'Test User',
        }
        create_user(**payload)
        response = self.client.post(path=CREATE_USER_URL, data=payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """
        Test that the password must be more than 5 characters
        """
        payload = {
            "email": 'user@example.com',
            "password": 'tp',
            "name": 'Test User',
        }
        response = self.client.post(path=CREATE_USER_URL, data=payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email'],
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """
        Test that a token is created for the user
        """
        user_details = {
            "email": 'user@example.com',
            "password": 'user_password',
            "name": 'Test User',
        }
        create_user(**user_details)
        payload = {
            "email": user_details['email'],
            "password": user_details['password'],
        }
        response = self.client.post(path=TOKEN_URL, data=payload)

        self.assertIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """
        Test that token is not created if invalid credentials are given
        """
        user_details = {
            "email": 'user@example.com',
            "password": 'user_password',
            "name": 'Test User',
        }
        create_user(**user_details)
        payload = {'email': user_details['email'], 'password': 'wrong'}
        response = self.client.post(path=TOKEN_URL, data=payload)

        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """
        Test that token is not created if password is blank
        """
        payload = {"email": 'user@example.com', "password": ''}
        response = self.client.post(path=TOKEN_URL, data=payload)

        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """
        Test that authentication is required for users
        """
        response = self.client.get(path=ME_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """
    Test API requests that require authentication
    """

    def setUp(self):
        """
        Setup
        """
        self.user = create_user(
            email='user@example.com',
            password='test_user12345',
            name='Test User',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """
        Test retrieving profile for logged in used
        """
        response = self.client.get(path=ME_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'name': self.user.name,
            'email': self.user.email,
        })

    def test_post_me_not_allowed(self):
        """
        Test that POST is not allowed on me url
        """
        response = self.client.post(path=ME_URL, data={})

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_update_user_profile(self):
        """
        Test updating the user profile for authenticated user
        """
        payload = {'name': 'New Name', 'password': 'new_password123'}
        response = self.client.patch(path=ME_URL, data=payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
