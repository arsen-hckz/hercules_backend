from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


class AuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@test.com', username='testuser', password='pass1234!'
        )

    def test_register(self):
        res = self.client.post('/api/auth/register/', {
            'email': 'new@test.com', 'username': 'newuser', 'password': 'pass1234!'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_register_duplicate_email(self):
        res = self.client.post('/api/auth/register/', {
            'email': 'test@test.com', 'username': 'other', 'password': 'pass1234!'
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login(self):
        res = self.client.post('/api/auth/login/', {
            'email': 'test@test.com', 'password': 'pass1234!'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)

    def test_login_wrong_password(self):
        res = self.client.post('/api/auth/login/', {
            'email': 'test@test.com', 'password': 'wrong'
        })
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def _auth(self):
        res = self.client.post('/api/auth/login/', {
            'email': 'test@test.com', 'password': 'pass1234!'
        })
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {res.data["access"]}')

    def test_me(self):
        self._auth()
        res = self.client.get('/api/auth/me/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['username'], 'testuser')

    def test_me_unauthenticated(self):
        res = self.client.get('/api/auth/me/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tdee_missing_data(self):
        self._auth()
        res = self.client.get('/api/auth/me/tdee/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsNone(res.data['tdee'])

    def test_tdee_with_data(self):
        self.user.gender = 'M'
        self.user.weight_kg = 80
        self.user.height_cm = 180
        from datetime import date
        self.user.date_of_birth = date(1995, 1, 1)
        self.user.goal = 'bulk'
        self.user.save()
        self._auth()
        res = self.client.get('/api/auth/me/tdee/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(res.data['tdee'])
        self.assertGreater(res.data['tdee'], 0)

    def test_follow_unfollow(self):
        User.objects.create_user(email='other@test.com', username='otheruser', password='pass1234!')
        self._auth()
        res = self.client.post('/api/auth/profile/otheruser/follow/')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        res = self.client.delete('/api/auth/profile/otheruser/unfollow/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_cannot_follow_self(self):
        self._auth()
        res = self.client.post('/api/auth/profile/testuser/follow/')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_request(self):
        res = self.client.post('/api/auth/password-reset/', {'email': 'test@test.com'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_password_reset_unknown_email(self):
        res = self.client.post('/api/auth/password-reset/', {'email': 'nobody@test.com'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
