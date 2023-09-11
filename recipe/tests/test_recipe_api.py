"""
Test for the recipe APIs
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPE_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """
    Return recipe detail URL
    """
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    """
    Helper function to create a recipe
    """
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': Decimal('5.25'),
        'description': 'Sample description',
        'link': 'https://www.sample.com/recipe',
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


def create_user(**params):
    """
    Helper function to create a user
    """
    return get_user_model().objects.create_user(**params)


class PublicRecipeApiTests(TestCase):
    """
    Test unauthenticated recipe API access
    """

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """
        Test that authentication is required
        """
        response = self.client.get(RECIPE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """
    Test authenticated recipe API access
    """

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="user@example.com", password='test123pass')
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """
        Test retrieving a list of recipes
        """
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        response = self.client.get(RECIPE_URL)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_recipes_list_limited_to_user(self):
        """
        Test retrieving recipes for user
        """
        user2 = create_user(email="other_user@example.com", password='test123pass')
        create_recipe(user=user2)
        create_recipe(user=self.user)

        response = self.client.get(RECIPE_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_get_recipe_detail(self):
        """
        Test retrieving a recipe detail
        """
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        response = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(response.data, serializer.data)

    def test_create_basic_recipe(self):
        """
        Test creating recipe
        """
        payload = {
            "title": "Cheesecake",
            "time_minutes": 18,
            "price": Decimal('8.25'),
            "link": "www.cheesecake.com",
            "description": "Cheesecake is a sweet dessert consisting of one or more layers",
        }
        response = self.client.post(RECIPE_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=response.data['id'])
        for key, value in payload.items():
            self.assertEqual(value, getattr(recipe, key))
        self.assertEqual(recipe.user, self.user)

    def test_partial_update_recipe(self):
        """
        Test updating a recipe with patch
        """
        original_link = "www.cheesecake.com"
        payload_to_create = {
            "title": "Cheesecake",
            "time_minutes": 18,
            "link": original_link,
        }
        recipe = create_recipe(user=self.user, **payload_to_create)

        payload = {"title": "Pasta"}
        url = detail_url(recipe.id)
        response = self.client.patch(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update_recipe(self):
        """
        Test full update of a recipe with put
        """
        payload_to_create = {
            "title": "Cheesecake",
            "time_minutes": 18,
            "link": "www.cheesecake.com",
        }
        recipe = create_recipe(user=self.user, **payload_to_create)

        payload = {
            "title": "Pasta",
            "time_minutes": 25,
            "price": Decimal('5.25'),
            "link": "www.pasta.com",
            "description": "Pasta is a type of food typically made from an unleavened dough",
        }
        url = detail_url(recipe.id)
        response = self.client.put(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for key, value in payload.items():
            self.assertEqual(value, getattr(recipe, key))
        self.assertEqual(recipe.user, self.user)

    def test_update_user_error(self):
        """
        Test changing the recipe user results in an error
        """
        new_user = create_user(email="user_new2@example.com", password='test12345pass')
        recipe = create_recipe(user=self.user)

        payload = {"user_id": new_user.id}
        url = detail_url(recipe.id)
        response = self.client.patch(url, payload)
        recipe.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.user, self.user)
        self.assertNotEqual(recipe.user, new_user)

    def test_delete_recipe(self):
        """
        Test deleting a recipe
        """
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_recipe_other_users_recipe_error(self):
        """
        Test that other users cannot delete a recipe
        """
        new_user = create_user(email="user_new2@example.com", password='test12345pass')
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """
        Test creating a recipe with new tags
        """
        payload = {
            "title": "Cheesecake",
            "time_minutes": 18,
            "price": Decimal('8.25'),
            "link": "www.cheesecake.com",
            "description": "Cheesecake is a sweet dessert consisting of one or more layers",
            "tags": [{"name": "sweet"}, {"name": "dessert"}]
        }
        response = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipe.count(), 1)
        tags = recipe[0].tags
        self.assertEqual(tags.count(), 2)
        for tag in payload['tags']:
            self.assertTrue(tags.filter(name=tag['name'], user=self.user).exists())

    def test_create_recipe_with_existing_tags(self):
        """
        Test creating a recipe with existing tags
        """
        tag1 = Tag.objects.create(user=self.user, name="sweet")
        payload = {
            "title": "Cheesecake",
            "time_minutes": 18,
            "price": Decimal('8.25'),
            "link": "www.cheesecake.com",
            "description": "Cheesecake is a sweet dessert consisting of one or more layers",
            "tags": [{"name": "sweet"}, {"name": "dessert"}]
        }
        response = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipe.count(), 1)
        tags = recipe[0].tags
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags.all())
        for tag in payload['tags']:
            self.assertTrue(tags.filter(name=tag['name'], user=self.user).exists())

    def test_create_tag_on_update(self):
        """
        Test creating a tag on update
        """
        recipe = create_recipe(user=self.user)
        payload = {'tags': [{'name': 'sweet'}]}
        url = detail_url(recipe.id)
        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='sweet')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """
        Test updating a recipe and assigning a tag
        """
        tag_sweet = Tag.objects.create(user=self.user, name="sweet")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_sweet)

        tag_launch = Tag.objects.create(user=self.user, name="launch")
        payload = {'tags': [{'name': 'launch'}]}
        url = detail_url(recipe.id)
        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(tag_sweet, recipe.tags.all())
        self.assertIn(tag_launch, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """
        Test clearing a recipe tags
        """
        tag_sweet = Tag.objects.create(user=self.user, name="sweet")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_sweet)

        payload = {'tags': []}
        url = detail_url(recipe.id)
        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
