from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', views.MeView.as_view(), name='me'),
    path('me/tdee/', views.TDEEView.as_view(), name='tdee'),
    path('profile/<str:username>/', views.UserProfileView.as_view(), name='user-profile'),
    path('profile/<str:username>/follow/', views.follow_user, name='follow-user'),
    path('profile/<str:username>/unfollow/', views.unfollow_user, name='unfollow-user'),
    path('profile/<str:username>/followers/', views.FollowerListView.as_view(), name='followers'),
    path('profile/<str:username>/following/', views.FollowingListView.as_view(), name='following'),
    path('password-reset/', views.password_reset_request, name='password-reset'),
    path('password-reset/confirm/', views.password_reset_confirm, name='password-reset-confirm'),
]
