"""
Test tags api.
"""
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


def detail_url(tag_id):
    """Create and return a tag detail url."""
    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(email='user@example.com', password='testpass123'):
    """Create and return a new user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagsApiTests(TestCase):
    """Test the publically available tags API."""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required to access the tags API."""
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test the private tags API."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving tags."""
        Tag.objects.create(user=self.user, name='Dessert')
        Tag.objects.create(user=self.user, name='Breakfast')

        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test that tags returned are for the authenticated user."""
        user2 = create_user(email="user2@example.com")
        Tag.objects.create(user=user2, name='Lunch')
        tag = Tag.objects.create(user=self.user, name='Dinner')
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        """Test updating a tag"""
        tag = Tag.objects.create(user=self.user, name='After Dinner')

        payload = {'name': 'Dessert'}
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])
    """
    Testcase class runs in isolation. Hence before running each test method
    the database is reset and other tags created in other test method doesnt
    exists.
    """
    def test_delete_tag(self):
        """Test deleting a tag"""
        tag = Tag.objects.create(user=self.user, name='Dinner')
        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())

    def test_filter_tags_assigned_to_recipes(self):
        """Test listing tags assigned to recipes."""
        tag1 = Tag.objects.create(user=self.user, name='Vegan')
        tag2 = Tag.objects.create(user=self.user, name='Dessert')
        recipe = Recipe.objects.create(
            title='Chocolate Cake',
            time_minutes=30,
            price=Decimal('5.00'),
            user=self.user,
        )
        recipe.tags.add(tag2)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        serializer1 = TagSerializer(tag2)
        serializer2 = TagSerializer(tag1)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_filter_tags_assigned_unique(self):
        """Test filtering tags assigned returns unique items."""
        tag = Tag.objects.create(user=self.user, name='Breakfast')
        Tag.objects.create(user=self.user, name='Lunch')
        recipe1 = Recipe.objects.create(
            title='Pancakes',
            time_minutes=10,
            price=Decimal('2.00'),
            user=self.user,
        )
        recipe1.tags.add(tag)
        recipe2 = Recipe.objects.create(
            title='Omelette',
            time_minutes=15,
            price=Decimal('3.00'),
            user=self.user,
        )
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)
