from django.urls import path
from . import views

urlpatterns = [
    # Food
    path('foods/', views.FoodItemSearchView.as_view(), name='food-search'),
    path('foods/recent/', views.recent_foods, name='food-recent'),
    path('foods/submit/', views.SubmitFoodView.as_view(), name='food-submit'),
    path('foods/<int:pk>/', views.FoodItemDetailView.as_view(), name='food-detail'),
    path('foods/<int:pk>/verify/', views.FoodItemVerifyView.as_view(), name='food-verify'),
    path('foods/barcode/<str:barcode>/', views.barcode_lookup, name='food-barcode'),
    # Recipes
    path('recipes/', views.RecipeListCreateView.as_view(), name='recipe-list'),
    path('recipes/mine/', views.MyRecipesView.as_view(), name='my-recipes'),
    path('recipes/saved/', views.SavedRecipesView.as_view(), name='saved-recipes'),
    path('recipes/<int:pk>/', views.RecipeDetailView.as_view(), name='recipe-detail'),
    path('recipes/<int:pk>/save/', views.save_recipe, name='save-recipe'),
    path('recipes/<int:pk>/unsave/', views.unsave_recipe, name='unsave-recipe'),
    # Admin food/log management
    path('admin/foods/', views.AdminFoodListView.as_view(), name='admin-food-list'),
    path('admin/logs/', views.AdminMealLogListView.as_view(), name='admin-meal-logs'),
    # Meal logs
    path('logs/', views.MealLogListCreateView.as_view(), name='meal-log-list'),
    path('logs/<int:pk>/', views.MealLogDetailView.as_view(), name='meal-log-detail'),
    path('logs/summary/', views.daily_nutrition_summary, name='daily-summary'),
]
