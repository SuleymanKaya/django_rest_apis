"""
Tests for the user API
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse('user:create')


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
