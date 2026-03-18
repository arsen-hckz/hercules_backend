from django.urls import path
from . import views

urlpatterns = [
    path('feed/', views.FeedView.as_view(), name='feed'),
    path('posts/', views.PostListCreateView.as_view(), name='post-list'),
    path('posts/<int:pk>/', views.PostDetailView.as_view(), name='post-detail'),
    path('posts/<int:pk>/like/', views.like_post, name='like-post'),
    path('posts/<int:pk>/unlike/', views.unlike_post, name='unlike-post'),
    path('posts/<int:pk>/comments/', views.CommentListCreateView.as_view(), name='comment-list'),
    path('comments/<int:pk>/', views.CommentDetailView.as_view(), name='comment-detail'),
    path('users/<str:username>/posts/', views.UserPostsView.as_view(), name='user-posts'),
]
