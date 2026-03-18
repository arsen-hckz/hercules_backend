from django.contrib import admin
from .models import MuscleGroup, Exercise, WorkoutSession, WorkoutEntry, WorkoutSet


@admin.register(MuscleGroup)
class MuscleGroupAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['name', 'muscle_group', 'equipment', 'is_custom']
    list_filter = ['muscle_group', 'equipment', 'is_custom']
    search_fields = ['name']


class WorkoutSetInline(admin.TabularInline):
    model = WorkoutSet
    extra = 1


class WorkoutEntryInline(admin.StackedInline):
    model = WorkoutEntry
    extra = 0


@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'date', 'duration_minutes']
    list_filter = ['date']
    inlines = [WorkoutEntryInline]
