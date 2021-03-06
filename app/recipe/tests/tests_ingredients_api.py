from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientsApiTests(TestCase):
    # Tests the publicly available Ingredients API.

    def setUp(self):
        self.client = APIClient()

    def test_login_requires(self):
        # Test a login is required for retrieving tags.
        resp = self.client.get(INGREDIENTS_URL)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    # Test the authorized user ingredients API.

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'kimsTest@gmail.com',
            'password123'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        # Test retrieving the ingredients.
        Ingredient.objects.create(user=self.user, name='Salt')
        Ingredient.objects.create(user=self.user, name='Pepper')
        Ingredient.objects.create(user=self.user, name='Paprika')

        resp = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        # Test that ingredient returned are for authenticated user.
        user2 = get_user_model().objects.create_user(
            'otherUser@gmail.com',
            'testpass123'
        )
        Ingredient.objects.create(user=user2, name='Fruit')
        ingredient = Ingredient.objects.create(user=self.user, name='Mustard')

        resp = self.client.get(INGREDIENTS_URL)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['name'], ingredient.name)

    def test_create_ingredient_successful(self):
        # Test the ingredient was created successfully.
        payload = {'name': 'Paprika'}

        self.client.post(INGREDIENTS_URL, payload)
        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()
        self.assertTrue(exists)

    def test_create_invalid_ingredient(self):
        # Test creating an ingredient with an invalid payload.
        payload = {'name': ' '}
        resp = self.client.post(INGREDIENTS_URL, payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredients_assigned_to_recipes(self):
        # Test filtering only ingredients assigned to recipes.
        ingredient1 = Ingredient.objects.create(
            user=self.user,
            name='Apples'
        )
        ingredient2 = Ingredient.objects.create(
            user=self.user,
            name='Peaches'
        )
        recipe1 = Recipe.objects.create(
            title='Apple Pancakes',
            time_minutes=5,
            price=5.00,
            user=self.user
        )
        recipe1.ingredients.add(ingredient1)
        resp = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)
        self.assertIn(serializer1.data, resp.data)
        self.assertNotIn(serializer2.data, resp.data)

    def test_retrieve_ingredients_assigned_unique(self):
        # Test filtering unique ingredient list.
        ingredient1 = Ingredient.objects.create(
            user=self.user,
            name='Apples'
        )
        recipe1 = Recipe.objects.create(
            title='Apple Pancakes',
            time_minutes=5,
            price=5.00,
            user=self.user
        )
        recipe1.ingredients.add(ingredient1)
        recipe2 = Recipe.objects.create(
            title='Apple Crumble',
            time_minutes=10,
            price=8.00,
            user=self.user
        )
        recipe2.ingredients.add(ingredient1)
        resp = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})
        self.assertEqual(len(resp.data), 1)
