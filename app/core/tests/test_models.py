"""
Test for models.
"""
from django.contrib.auth import get_user_model
from core import models
from unittest.mock import patch
from decimal import Decimal
from django.test import TestCase
"""
get_user_model is a default function that returns the User model that is
active in the current project. It is best practice to use this function cause
it'll be easier to handle the test case even if the user model is changed for
some reason.
"""


def create_user(email='user@example.com', password='testpass123',):
    """Create and return a new user."""
    return get_user_model().objects.create_user(email=email, password=password)


class ModelTests(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test creating a user with an email is successful."""
        email = 'test@example.com'  # safe to use example.com for testing
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

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users."""
        sample_emails = [
             ['test1@EXAMPLE.com', 'test1@example.com'],
             ['Test2@Example.com', 'Test2@example.com'],
             ['TEST3@EXAMPLE.com', 'TEST3@example.com'],
             ['test4@example.COM', 'test4@example.com'],
         ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'sample123')
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test that creating a user without an email raises a ValueError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test123')

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = get_user_model().objects.create_superuser(
             'test@example.com',
             'test123',
         )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """Test creating a recipe is successful."""
        user = get_user_model().objects.create_user(
            'test@example.com',
            'testpass123',
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title='Sample Recipe',
            time_minutes=5,
            price=Decimal('5.50'),
            description='Sample description',
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        """Test creating a tag is successful."""
        user = create_user()
        tag = models.Tag.objects.create(
            user=user,
            name='Vegan'
        )

        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):
        """Test creating an ingredient is successful."""
        user = create_user()
        ingredient = models.Ingredient.objects.create(
            user=user,
            name='Cucumber'
        )

        self.assertEqual(str(ingredient), ingredient.name)

    @patch('core.models.uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        """Test that image is saved in the correct location."""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'myimage.jpg')
        exp_path = f'uploads/recipe/{uuid}.jpg'

        self.assertEqual(file_path, exp_path)
