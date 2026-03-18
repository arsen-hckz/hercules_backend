from django.db import models
from django.conf import settings


class FoodItem(models.Model):
    # Sourced from Open Food Facts API, cached locally, or user-submitted
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=200, blank=True)
    barcode = models.CharField(max_length=50, blank=True, db_index=True)
    off_id = models.CharField(max_length=100, blank=True, unique=True)

    # Nutrition per 100g
    calories = models.FloatField(default=0)
    protein = models.FloatField(default=0)
    carbs = models.FloatField(default=0)
    fat = models.FloatField(default=0)
    fiber = models.FloatField(default=0)
    sugars = models.FloatField(default=0)

    # User submissions
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='submitted_foods'
    )
    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.brand})' if self.brand else self.name

    def nutrition_for_grams(self, grams):
        factor = grams / 100
        return {
            'calories': round(self.calories * factor, 1),
            'protein': round(self.protein * factor, 1),
            'carbs': round(self.carbs * factor, 1),
            'fat': round(self.fat * factor, 1),
            'fiber': round(self.fiber * factor, 1),
            'sugars': round(self.sugars * factor, 1),
        }


class Recipe(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recipes')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    servings = models.PositiveIntegerField(default=1)
    is_public = models.BooleanField(default=True)
    image = models.ImageField(upload_to='recipes/', blank=True, null=True)
    saved_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='SavedRecipe',
        related_name='saved_recipes',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def total_nutrition(self):
        totals = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'fiber': 0, 'sugars': 0}
        for ingredient in self.ingredients.all():
            n = ingredient.food_item.nutrition_for_grams(ingredient.quantity_grams)
            for key in totals:
                totals[key] += n[key]
        return totals

    def nutrition_per_serving(self):
        totals = self.total_nutrition()
        return {k: round(v / self.servings, 1) for k, v in totals.items()}


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredients')
    food_item = models.ForeignKey(FoodItem, on_delete=models.PROTECT)
    quantity_grams = models.FloatField()

    def __str__(self):
        return f'{self.quantity_grams}g {self.food_item.name}'


class SavedRecipe(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recipe')


class MealLog(models.Model):
    MEAL_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='meal_logs')
    date = models.DateField()
    meal_type = models.CharField(max_length=20, choices=MEAL_CHOICES)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'meal_type']

    def __str__(self):
        return f'{self.user} - {self.meal_type} on {self.date}'

    def total_nutrition(self):
        totals = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'fiber': 0, 'sugars': 0}
        for item in self.items.all():
            n = item.get_nutrition()
            for key in totals:
                totals[key] += n[key]
        return totals


class MealLogItem(models.Model):
    meal_log = models.ForeignKey(MealLog, on_delete=models.CASCADE, related_name='items')
    food_item = models.ForeignKey(FoodItem, on_delete=models.PROTECT, null=True, blank=True)
    recipe = models.ForeignKey(Recipe, on_delete=models.PROTECT, null=True, blank=True)
    quantity_grams = models.FloatField(null=True, blank=True)
    servings = models.FloatField(default=1)

    def get_nutrition(self):
        if self.food_item and self.quantity_grams:
            return self.food_item.nutrition_for_grams(self.quantity_grams)
        elif self.recipe:
            n = self.recipe.nutrition_per_serving()
            return {k: round(v * self.servings, 1) for k, v in n.items()}
        return {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'fiber': 0, 'sugars': 0}
