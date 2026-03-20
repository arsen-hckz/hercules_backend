from django.contrib import admin
from .models import MuscleGroup, Exercise, ExerciseMuscleActivation, WorkoutSession, WorkoutEntry, WorkoutSet


@admin.register(MuscleGroup)
class MuscleGroupAdmin(admin.ModelAdmin):
    list_display = ['name']


class ExerciseMuscleActivationInline(admin.TabularInline):
    model = ExerciseMuscleActivation
    extra = 1


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['name', 'equipment', 'is_custom']
    list_filter = ['equipment', 'is_custom']
    search_fields = ['name']
    inlines = [ExerciseMuscleActivationInline]


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
