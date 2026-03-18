from django.db import models
from django.conf import settings


class MuscleGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Exercise(models.Model):
    EQUIPMENT_CHOICES = [
        ('barbell', 'Barbell'),
        ('dumbbell', 'Dumbbell'),
        ('machine', 'Machine'),
        ('cable', 'Cable'),
        ('bodyweight', 'Bodyweight'),
        ('kettlebell', 'Kettlebell'),
        ('resistance_band', 'Resistance Band'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200, unique=True)
    muscle_group = models.ForeignKey(MuscleGroup, on_delete=models.SET_NULL, null=True, related_name='exercises')
    secondary_muscles = models.ManyToManyField(MuscleGroup, blank=True, related_name='secondary_exercises')
    equipment = models.CharField(max_length=20, choices=EQUIPMENT_CHOICES, default='other')
    description = models.TextField(blank=True)
    is_custom = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='custom_exercises'
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class WorkoutSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='workout_sessions')
    name = models.CharField(max_length=200, blank=True)
    date = models.DateField()
    notes = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'{self.user} - {self.name or "Workout"} on {self.date}'

    def total_volume(self):
        """Total volume lifted (kg * reps) across all sets."""
        return sum(
            s.weight_kg * s.reps
            for entry in self.entries.all()
            for s in entry.sets.all()
            if s.weight_kg and s.reps
        )


class WorkoutEntry(models.Model):
    session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE, related_name='entries')
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT)
    order = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.exercise.name} in {self.session}'


class WorkoutSet(models.Model):
    entry = models.ForeignKey(WorkoutEntry, on_delete=models.CASCADE, related_name='sets')
    set_number = models.PositiveIntegerField()
    weight_kg = models.FloatField(null=True, blank=True)
    reps = models.PositiveIntegerField(null=True, blank=True)
    rest_seconds = models.PositiveIntegerField(null=True, blank=True)
    is_warmup = models.BooleanField(default=False)

    class Meta:
        ordering = ['set_number']

    def __str__(self):
        return f'Set {self.set_number}: {self.weight_kg}kg x {self.reps}'

    @property
    def volume(self):
        if self.weight_kg and self.reps:
            return round(self.weight_kg * self.reps, 1)
        return 0
