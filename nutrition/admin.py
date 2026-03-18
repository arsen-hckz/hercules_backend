from django.contrib import admin
from .models import FoodItem, Recipe, RecipeIngredient, MealLog, MealLogItem


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'calories', 'protein', 'carbs', 'fat']
    search_fields = ['name', 'brand', 'barcode']


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'servings', 'is_public', 'created_at']
    inlines = [RecipeIngredientInline]


class MealLogItemInline(admin.TabularInline):
    model = MealLogItem
    extra = 1


@admin.register(MealLog)
class MealLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'meal_type']
    list_filter = ['meal_type', 'date']
    inlines = [MealLogItemInline]
