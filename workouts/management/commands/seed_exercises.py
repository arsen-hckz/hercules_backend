from django.core.management.base import BaseCommand
from workouts.models import MuscleGroup, Exercise


MUSCLE_GROUPS = [
    'Chest', 'Back', 'Shoulders', 'Biceps', 'Triceps',
    'Forearms', 'Core', 'Quads', 'Hamstrings', 'Glutes', 'Calves', 'Traps',
]

# (name, muscle_group, equipment)
EXERCISES = [
    # Chest
    ('Bench Press', 'Chest', 'barbell'),
    ('Incline Bench Press', 'Chest', 'barbell'),
    ('Decline Bench Press', 'Chest', 'barbell'),
    ('Dumbbell Fly', 'Chest', 'dumbbell'),
    ('Incline Dumbbell Press', 'Chest', 'dumbbell'),
    ('Cable Fly', 'Chest', 'cable'),
    ('Push Up', 'Chest', 'bodyweight'),
    ('Dips', 'Chest', 'bodyweight'),

    # Back
    ('Deadlift', 'Back', 'barbell'),
    ('Barbell Row', 'Back', 'barbell'),
    ('T-Bar Row', 'Back', 'barbell'),
    ('Pull Up', 'Back', 'bodyweight'),
    ('Chin Up', 'Back', 'bodyweight'),
    ('Lat Pulldown', 'Back', 'cable'),
    ('Seated Cable Row', 'Back', 'cable'),
    ('Dumbbell Row', 'Back', 'dumbbell'),

    # Shoulders
    ('Overhead Press', 'Shoulders', 'barbell'),
    ('Dumbbell Shoulder Press', 'Shoulders', 'dumbbell'),
    ('Arnold Press', 'Shoulders', 'dumbbell'),
    ('Lateral Raise', 'Shoulders', 'dumbbell'),
    ('Front Raise', 'Shoulders', 'dumbbell'),
    ('Face Pull', 'Shoulders', 'cable'),
    ('Upright Row', 'Shoulders', 'barbell'),

    # Biceps
    ('Barbell Curl', 'Biceps', 'barbell'),
    ('Dumbbell Curl', 'Biceps', 'dumbbell'),
    ('Hammer Curl', 'Biceps', 'dumbbell'),
    ('Incline Dumbbell Curl', 'Biceps', 'dumbbell'),
    ('Preacher Curl', 'Biceps', 'barbell'),
    ('Cable Curl', 'Biceps', 'cable'),
    ('Concentration Curl', 'Biceps', 'dumbbell'),

    # Triceps
    ('Close Grip Bench Press', 'Triceps', 'barbell'),
    ('Skull Crusher', 'Triceps', 'barbell'),
    ('Tricep Pushdown', 'Triceps', 'cable'),
    ('Overhead Tricep Extension', 'Triceps', 'dumbbell'),
    ('Tricep Kickback', 'Triceps', 'dumbbell'),
    ('Diamond Push Up', 'Triceps', 'bodyweight'),

    # Forearms
    ('Wrist Curl', 'Forearms', 'barbell'),
    ('Reverse Wrist Curl', 'Forearms', 'barbell'),
    ('Farmers Walk', 'Forearms', 'dumbbell'),

    # Core
    ('Crunch', 'Core', 'bodyweight'),
    ('Plank', 'Core', 'bodyweight'),
    ('Leg Raise', 'Core', 'bodyweight'),
    ('Hanging Leg Raise', 'Core', 'bodyweight'),
    ('Russian Twist', 'Core', 'bodyweight'),
    ('Cable Crunch', 'Core', 'cable'),
    ('Ab Rollout', 'Core', 'other'),
    ('Bicycle Crunch', 'Core', 'bodyweight'),

    # Quads
    ('Squat', 'Quads', 'barbell'),
    ('Front Squat', 'Quads', 'barbell'),
    ('Hack Squat', 'Quads', 'machine'),
    ('Leg Press', 'Quads', 'machine'),
    ('Leg Extension', 'Quads', 'machine'),
    ('Bulgarian Split Squat', 'Quads', 'dumbbell'),
    ('Lunges', 'Quads', 'dumbbell'),
    ('Step Up', 'Quads', 'dumbbell'),

    # Hamstrings
    ('Romanian Deadlift', 'Hamstrings', 'barbell'),
    ('Leg Curl', 'Hamstrings', 'machine'),
    ('Good Morning', 'Hamstrings', 'barbell'),
    ('Nordic Curl', 'Hamstrings', 'bodyweight'),
    ('Stiff Leg Deadlift', 'Hamstrings', 'barbell'),

    # Glutes
    ('Hip Thrust', 'Glutes', 'barbell'),
    ('Glute Bridge', 'Glutes', 'bodyweight'),
    ('Cable Kickback', 'Glutes', 'cable'),
    ('Sumo Deadlift', 'Glutes', 'barbell'),

    # Calves
    ('Standing Calf Raise', 'Calves', 'machine'),
    ('Seated Calf Raise', 'Calves', 'machine'),
    ('Donkey Calf Raise', 'Calves', 'machine'),

    # Traps
    ('Barbell Shrug', 'Traps', 'barbell'),
    ('Dumbbell Shrug', 'Traps', 'dumbbell'),
]


class Command(BaseCommand):
    help = 'Seed the database with muscle groups and exercises'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding muscle groups...')
        groups = {}
        for name in MUSCLE_GROUPS:
            group, created = MuscleGroup.objects.get_or_create(name=name)
            groups[name] = group
            if created:
                self.stdout.write(f'  + {name}')

        self.stdout.write('Seeding exercises...')
        created_count = 0
        for name, muscle_group, equipment in EXERCISES:
            _, created = Exercise.objects.get_or_create(
                name=name,
                defaults={
                    'muscle_group': groups[muscle_group],
                    'equipment': equipment,
                    'is_custom': False,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'  + {name}')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {len(MUSCLE_GROUPS)} muscle groups, {created_count} exercises seeded.'
        ))
