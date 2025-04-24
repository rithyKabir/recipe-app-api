"""
Test for models.
"""

from django.test import TestCase
"""
get_user_model is a default function that returns the User model that is 
active in the current project. It is best practice to use this function cause 
it'll be easier to handle the test case even if the user model is changed for
some reason.
"""
from django.contrib.auth import get_user_model

class ModelTests(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test creating a user with an email is successful."""
        email = 'test@example.com' #safe to use example.com for testing
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        """
        We are using user.check_password instead of user.password == password
        because the password will be saved as a hash in the database. this 
        check_password method will hash the password and compare it to the
        given value. it is a default method of the user model.
        """
        self.assertTrue(user.check_password(password))