from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


class PublicTagsApiTests(TestCase):
    # Tests the publicly available tags API.

    def setUp(self):
        self.client = APIClient()

    def test_login_requires(self):
        # Test a login is required for retrieving tags.
        resp = self.client.get(TAGS_URL)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    # Test the authorized user tags API.

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'kimsTest@gmail.com',
            'password123'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        # Test retrieving the tags.
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Keto')
        Tag.objects.create(user=self.user, name='Paleo')

        resp = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, serializer.data)

    def test_tags_limited_to_user(self):
        # Test that tags returned are for authenticated user.
        user2 = get_user_model().objects.create_user(
            'otherUser@gmail.com',
            'testpass123'
        )
        Tag.objects.create(user=user2, name='Fruit')
        tag = Tag.objects.create(user=self.user, name='Comfort Food')

        resp = self.client.get(TAGS_URL)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['name'], tag.name)

    def test_create_tag_successful(self):
        # Test the tag was created successfully.
        payload = {'name': 'Test Tag'}

        self.client.post(TAGS_URL, payload)
        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()
        self.assertTrue(exists)

    def test_create_invalid_tag(self):
        # Test creating a tag with an invalid payload.
        payload = {'name': ' '}
        resp = self.client.post(TAGS_URL, payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_recipes(self):
        # Test retrieving tags that are assigned to recipes.
        tag1 = Tag.objects.create(user=self.user, name='curry')
        tag2 = Tag.objects.create(user=self.user, name='tahini')
        recipe = Recipe.objects.create(
            title='Curry Chicken',
            time_minutes=10,
            price=15.00,
            user=self.user
        )
        recipe.tags.add(tag1)
        resp = self.client.get(TAGS_URL, {'assigned_only': 1})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)

        self.assertIn(serializer1.data, resp.data)
        self.assertNotIn(serializer2.data, resp.data)

    def test_retrieved_tags_assigned_unique(self):
        # Test filtering by tags returns unique list.
        tag = Tag.objects.create(user=self.user, name='Breakfast')
        Tag.objects.create(user=self.user, name='Lunch')
        recipe1 = Recipe.objects.create(
            title='Pancakes',
            time_minutes=5,
            price=5.00,
            user=self.user
        )
        recipe1.tags.add(tag)
        recipe2 = Recipe.objects.create(
            title='Eggs Benedict',
            time_minutes=20,
            price=10.00,
            user=self.user
        )
        recipe2.tags.add(tag)

        resp = self.client.get(TAGS_URL, {'assigned_only': 1})
        self.assertEqual(len(resp.data), 1)
