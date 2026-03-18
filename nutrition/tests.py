from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import FoodItem, Recipe, RecipeIngredient, MealLog

User = get_user_model()


class NutritionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@test.com', username='testuser', password='pass1234!'
        )
        res = self.client.post('/api/auth/login/', {'email': 'test@test.com', 'password': 'pass1234!'})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {res.data["access"]}')

        self.food = FoodItem.objects.create(
            name='Chicken Breast', off_id='chicken-001',
            calories=165, protein=31, carbs=0, fat=3.6, fiber=0, sugars=0
        )
        self.food2 = FoodItem.objects.create(
            name='Brown Rice', off_id='rice-001',
            calories=216, protein=5, carbs=45, fat=1.8, fiber=3.5, sugars=0.7
        )

    def test_food_search_local(self):
        res = self.client.get('/api/nutrition/foods/?search=chicken')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], 'Chicken Breast')

    def test_food_search_empty_query(self):
        res = self.client.get('/api/nutrition/foods/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, [])

    def test_create_recipe(self):
        res = self.client.post('/api/nutrition/recipes/', {
            'title': 'Chicken & Rice',
            'servings': 2,
            'is_public': True,
            'ingredients': [
                {'food_item_id': self.food.id, 'quantity_grams': 200},
                {'food_item_id': self.food2.id, 'quantity_grams': 150},
            ]
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['title'], 'Chicken & Rice')
        self.assertIn('nutrition_per_serving', res.data)

    def test_nutrition_per_serving(self):
        recipe = Recipe.objects.create(user=self.user, title='Test', servings=2, is_public=True)
        RecipeIngredient.objects.create(recipe=recipe, food_item=self.food, quantity_grams=200)
        n = recipe.nutrition_per_serving()
        self.assertAlmostEqual(n['calories'], 165.0, places=0)
        self.assertAlmostEqual(n['protein'], 31.0, places=0)

    def test_save_and_unsave_recipe(self):
        other = User.objects.create_user(email='other@test.com', username='other', password='pass1234!')
        recipe = Recipe.objects.create(user=other, title='Other Recipe', servings=1, is_public=True)
        res = self.client.post(f'/api/nutrition/recipes/{recipe.id}/save/')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        res = self.client.delete(f'/api/nutrition/recipes/{recipe.id}/unsave/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_meal_log(self):
        res = self.client.post('/api/nutrition/logs/', {
            'date': '2026-03-18',
            'meal_type': 'lunch',
            'items': [{'food_item_id': self.food.id, 'quantity_grams': 150}]
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('total_nutrition', res.data)

    def test_daily_summary(self):
        MealLog.objects.create(user=self.user, date='2026-03-18', meal_type='breakfast')
        res = self.client.get('/api/nutrition/logs/summary/?date=2026-03-18')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('nutrition', res.data)

    def test_my_recipes_only_own(self):
        other = User.objects.create_user(email='o@test.com', username='ouser', password='pass1234!')
        Recipe.objects.create(user=other, title='Other', servings=1, is_public=True)
        Recipe.objects.create(user=self.user, title='Mine', servings=1, is_public=True)
        res = self.client.get('/api/nutrition/recipes/mine/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 1)
        self.assertEqual(res.data['results'][0]['title'], 'Mine')
