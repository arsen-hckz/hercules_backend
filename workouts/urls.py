from django.urls import path
from . import views

urlpatterns = [
    path('muscle-groups/', views.MuscleGroupListView.as_view(), name='muscle-groups'),
    path('exercises/', views.ExerciseListCreateView.as_view(), name='exercise-list'),
    path('exercises/<int:pk>/', views.ExerciseDetailView.as_view(), name='exercise-detail'),
    path('exercises/<int:exercise_id>/progress/', views.exercise_progress, name='exercise-progress'),
    path('sessions/', views.WorkoutSessionListCreateView.as_view(), name='session-list'),
    path('sessions/<int:pk>/', views.WorkoutSessionDetailView.as_view(), name='session-detail'),
    path('stats/', views.workout_stats, name='workout-stats'),
    path('correlation/', views.diet_workout_correlation, name='diet-workout-correlation'),
]
