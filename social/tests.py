from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Post, Like, Comment

User = get_user_model()


class SocialTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@test.com', username='testuser', password='pass1234!'
        )
        self.other = User.objects.create_user(
            email='other@test.com', username='otheruser', password='pass1234!'
        )
        res = self.client.post('/api/auth/login/', {'email': 'test@test.com', 'password': 'pass1234!'})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {res.data["access"]}')

    def test_create_post(self):
        res = self.client.post('/api/social/posts/', {'content': 'Great workout!'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['content'], 'Great workout!')

    def test_like_post(self):
        post = Post.objects.create(user=self.other, content='Hello')
        res = self.client.post(f'/api/social/posts/{post.id}/like/')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['likes_count'], 1)

    def test_like_twice_fails(self):
        post = Post.objects.create(user=self.other, content='Hello')
        self.client.post(f'/api/social/posts/{post.id}/like/')
        res = self.client.post(f'/api/social/posts/{post.id}/like/')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unlike_post(self):
        post = Post.objects.create(user=self.other, content='Hello')
        Like.objects.create(user=self.user, post=post)
        res = self.client.delete(f'/api/social/posts/{post.id}/unlike/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['likes_count'], 0)

    def test_add_comment(self):
        post = Post.objects.create(user=self.other, content='Hello')
        res = self.client.post(f'/api/social/posts/{post.id}/comments/', {'content': 'Nice!'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_reply_to_comment(self):
        post = Post.objects.create(user=self.other, content='Hello')
        comment = Comment.objects.create(user=self.other, post=post, content='First comment')
        res = self.client.post(f'/api/social/posts/{post.id}/comments/', {
            'content': 'Reply here', 'parent': comment.id
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_feed_shows_following_posts(self):
        from users.models import Follow
        Follow.objects.create(follower=self.user, following=self.other)
        Post.objects.create(user=self.other, content='From followed user')
        res = self.client.get('/api/social/feed/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreater(res.data['count'], 0)

    def test_feed_excludes_non_following(self):
        stranger = User.objects.create_user(email='s@test.com', username='stranger', password='pass1234!')
        Post.objects.create(user=stranger, content='You should not see this')
        res = self.client.get('/api/social/feed/')
        self.assertEqual(res.data['count'], 0)

    def test_delete_own_post(self):
        post = Post.objects.create(user=self.user, content='Mine')
        res = self.client.delete(f'/api/social/posts/{post.id}/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_cannot_delete_others_post(self):
        post = Post.objects.create(user=self.other, content='Not mine')
        res = self.client.delete(f'/api/social/posts/{post.id}/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class NotificationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@test.com', username='testuser', password='pass1234!'
        )
        self.other = User.objects.create_user(
            email='other@test.com', username='otheruser', password='pass1234!'
        )

    def _auth_as(self, email, password='pass1234!'):
        res = self.client.post('/api/auth/login/', {'email': email, 'password': password})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {res.data["access"]}')

    def test_like_creates_notification(self):
        post = Post.objects.create(user=self.user, content='My post')
        self._auth_as('other@test.com')
        self.client.post(f'/api/social/posts/{post.id}/like/')

        self._auth_as('test@test.com')
        res = self.client.get('/api/notifications/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(res.data['results'][0]['notification_type'], 'like')

    def test_follow_creates_notification(self):
        self._auth_as('other@test.com')
        self.client.post('/api/auth/profile/testuser/follow/')

        self._auth_as('test@test.com')
        res = self.client.get('/api/notifications/')
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(res.data['results'][0]['notification_type'], 'follow')

    def test_mark_notification_read(self):
        from notifications.models import Notification
        notif = Notification.objects.create(
            recipient=self.user, sender=self.other,
            notification_type='follow', message='Test'
        )
        self._auth_as('test@test.com')
        res = self.client.post(f'/api/notifications/{notif.id}/read/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_unread_count(self):
        from notifications.models import Notification
        Notification.objects.create(
            recipient=self.user, sender=self.other,
            notification_type='follow', message='Test'
        )
        self._auth_as('test@test.com')
        res = self.client.get('/api/notifications/unread/')
        self.assertEqual(res.data['unread_count'], 1)
