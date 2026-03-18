from django.urls import path
from . import views

urlpatterns = [
    # Food
    path('foods/', views.FoodItemSearchView.as_view(), name='food-search'),
    path('foods/submit/', views.SubmitFoodView.as_view(), name='food-submit'),
    # Recipes
    path('recipes/', views.RecipeListCreateView.as_view(), name='recipe-list'),
    path('recipes/mine/', views.MyRecipesView.as_view(), name='my-recipes'),
    path('recipes/saved/', views.SavedRecipesView.as_view(), name='saved-recipes'),
    path('recipes/<int:pk>/', views.RecipeDetailView.as_view(), name='recipe-detail'),
    path('recipes/<int:pk>/save/', views.save_recipe, name='save-recipe'),
    path('recipes/<int:pk>/unsave/', views.unsave_recipe, name='unsave-recipe'),
    # Meal logs
    path('logs/', views.MealLogListCreateView.as_view(), name='meal-log-list'),
    path('logs/<int:pk>/', views.MealLogDetailView.as_view(), name='meal-log-detail'),
    path('logs/summary/', views.daily_nutrition_summary, name='daily-summary'),
]
