import django.db.models.deletion
from django.db import migrations, models


def migrate_muscle_data(apps, schema_editor):
    Exercise = apps.get_model('workouts', 'Exercise')
    ExerciseMuscleActivation = apps.get_model('workouts', 'ExerciseMuscleActivation')

    for ex in Exercise.objects.all():
        seen = set()
        # Primary muscle group → level 8
        if ex.muscle_group_id:
            ExerciseMuscleActivation.objects.get_or_create(
                exercise=ex,
                muscle_group_id=ex.muscle_group_id,
                defaults={'level': 8},
            )
            seen.add(ex.muscle_group_id)
        # Secondary muscles → level 5
        for mg in ex.secondary_muscles.all():
            if mg.pk not in seen:
                ExerciseMuscleActivation.objects.get_or_create(
                    exercise=ex,
                    muscle_group=mg,
                    defaults={'level': 5},
                )


class Migration(migrations.Migration):

    dependencies = [
        ('workouts', '0001_initial'),
    ]

    operations = [
        # 1. Create the new through-model table
        migrations.CreateModel(
            name='ExerciseMuscleActivation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.PositiveSmallIntegerField(
                    default=5,
                    help_text='Activation level 1–10 (10 = primary mover, 1 = minimal)',
                )),
                ('exercise', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='muscle_activations',
                    to='workouts.exercise',
                )),
                ('muscle_group', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='activations',
                    to='workouts.musclegroup',
                )),
            ],
            options={
                'ordering': ['-level'],
                'unique_together': {('exercise', 'muscle_group')},
            },
        ),
        # 2. Migrate existing data
        migrations.RunPython(migrate_muscle_data, migrations.RunPython.noop),
        # 3. Drop the old fields
        migrations.RemoveField(model_name='exercise', name='secondary_muscles'),
        migrations.RemoveField(model_name='exercise', name='muscle_group'),
    ]
