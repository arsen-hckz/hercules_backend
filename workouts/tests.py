from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import MuscleGroup, Exercise, WorkoutSession

User = get_user_model()


class WorkoutTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@test.com', username='testuser', password='pass1234!'
        )
        res = self.client.post('/api/auth/login/', {'email': 'test@test.com', 'password': 'pass1234!'})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {res.data["access"]}')

        self.chest = MuscleGroup.objects.create(name='Chest')
        self.exercise = Exercise.objects.create(
            name='Bench Press', muscle_group=self.chest, equipment='barbell'
        )

    def test_list_muscle_groups(self):
        res = self.client.get('/api/workouts/muscle-groups/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_list_exercises(self):
        res = self.client.get('/api/workouts/exercises/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_filter_exercises_by_equipment(self):
        res = self.client.get('/api/workouts/exercises/?equipment=barbell')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_custom_exercise(self):
        res = self.client.post('/api/workouts/exercises/', {
            'name': 'My Custom Move',
            'equipment': 'dumbbell',
            'muscle_group_id': self.chest.id,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['is_custom'])

    def test_create_workout_session(self):
        res = self.client.post('/api/workouts/sessions/', {
            'name': 'Chest Day',
            'date': '2026-03-18',
            'entries': [{
                'exercise_id': self.exercise.id,
                'order': 1,
                'sets': [
                    {'set_number': 1, 'weight_kg': 80, 'reps': 10},
                    {'set_number': 2, 'weight_kg': 85, 'reps': 8},
                ]
            }]
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['name'], 'Chest Day')

    def test_workout_volume(self):
        session = WorkoutSession.objects.create(user=self.user, name='Test', date='2026-03-18')
        from .models import WorkoutEntry, WorkoutSet
        entry = WorkoutEntry.objects.create(session=session, exercise=self.exercise)
        WorkoutSet.objects.create(entry=entry, set_number=1, weight_kg=100, reps=5)
        self.assertEqual(session.total_volume(), 500)

    def test_session_belongs_to_user(self):
        other = User.objects.create_user(email='o@test.com', username='other', password='pass1234!')
        WorkoutSession.objects.create(user=other, name='Other', date='2026-03-18')
        res = self.client.get('/api/workouts/sessions/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 0)

    def test_exercise_progress(self):
        res = self.client.get(f'/api/workouts/exercises/{self.exercise.id}/progress/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, [])

    def test_workout_stats(self):
        res = self.client.get('/api/workouts/stats/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('total_sessions', res.data)
