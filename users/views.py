from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from .models import Follow
from .serializers import RegisterSerializer, UserProfileSerializer, FollowSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        return self.request.user


class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    queryset = User.objects.all()
    lookup_field = 'username'


class TDEEView(generics.GenericAPIView):
    def get(self, request):
        user = request.user
        return Response({
            'bmi': user.calculate_bmi(),
            'tdee': user.calculate_tdee(),
            'goal': user.goal,
            'activity_level': user.activity_level,
        })


@api_view(['POST'])
def follow_user(request, username):
    target = get_object_or_404(User, username=username)
    if target == request.user:
        return Response({'detail': 'You cannot follow yourself.'}, status=status.HTTP_400_BAD_REQUEST)
    follow, created = Follow.objects.get_or_create(follower=request.user, following=target)
    if not created:
        return Response({'detail': 'Already following.'}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'detail': f'Now following {username}.'}, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
def unfollow_user(request, username):
    target = get_object_or_404(User, username=username)
    deleted, _ = Follow.objects.filter(follower=request.user, following=target).delete()
    if not deleted:
        return Response({'detail': 'Not following.'}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'detail': f'Unfollowed {username}.'})


class FollowerListView(generics.ListAPIView):
    serializer_class = FollowSerializer

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs['username'])
        return Follow.objects.filter(following=user).select_related('follower')


class FollowingListView(generics.ListAPIView):
    serializer_class = FollowSerializer

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs['username'])
        return Follow.objects.filter(follower=user).select_related('following')


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_request(request):
    email = request.data.get('email', '').strip()
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Don't reveal whether the email exists
        return Response({'detail': 'If that email exists, a reset link has been sent.'})

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    reset_link = f'http://localhost:3000/reset-password/{uid}/{token}/'

    send_mail(
        subject='Hercules — Password Reset',
        message=f'Use this link to reset your password:\n\n{reset_link}\n\nThis link expires in 24 hours.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )
    return Response({'detail': 'If that email exists, a reset link has been sent.'})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_confirm(request):
    uid = request.data.get('uid', '')
    token = request.data.get('token', '')
    new_password = request.data.get('new_password', '')

    if not all([uid, token, new_password]):
        return Response({'detail': 'uid, token and new_password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
    except (User.DoesNotExist, ValueError):
        return Response({'detail': 'Invalid reset link.'}, status=status.HTTP_400_BAD_REQUEST)

    if not default_token_generator.check_token(user, token):
        return Response({'detail': 'Reset link is invalid or has expired.'}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save(update_fields=['password'])
    return Response({'detail': 'Password reset successfully.'})


# ─── Admin endpoints ──────────────────────────────────────────────────────────

class AdminUserListView(generics.ListAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.all().order_by('-date_joined')


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_stats(request):
    from datetime import date, timedelta
    from social.models import Post
    from nutrition.models import MealLog, FoodItem
    from workouts.models import WorkoutSession

    today = date.today()
    week_ago = today - timedelta(days=7)

    return Response({
        'users': {
            'total': User.objects.count(),
            'new_today': User.objects.filter(date_joined__date=today).count(),
            'new_this_week': User.objects.filter(date_joined__date__gte=week_ago).count(),
        },
        'posts': {
            'total': Post.objects.count(),
            'today': Post.objects.filter(created_at__date=today).count(),
        },
        'meal_logs': {
            'total': MealLog.objects.count(),
            'today': MealLog.objects.filter(date=today).count(),
        },
        'workout_sessions': {
            'total': WorkoutSession.objects.count(),
            'today': WorkoutSession.objects.filter(date=today).count(),
        },
        'food_items': {
            'total': FoodItem.objects.count(),
            'pending_review': FoodItem.objects.filter(is_verified=False, submitted_by__isnull=False).count(),
        },
        'exercises': {
            'total': WorkoutSession.objects.model._meta.apps.get_model('workouts', 'Exercise').objects.count(),
        },
    })
