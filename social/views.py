from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from .models import Post, PostMedia, Like, Comment
from .serializers import PostSerializer, CommentSerializer
from users.models import Follow


class FeedView(generics.ListAPIView):
    """Posts from users the current user follows + own posts."""
    serializer_class = PostSerializer
    filter_backends = [filters.OrderingFilter]
    ordering = ['-created_at']

    def get_queryset(self):
        following_ids = Follow.objects.filter(
            follower=self.request.user
        ).values_list('following_id', flat=True)
        return Post.objects.filter(
            user_id__in=list(following_ids) + [self.request.user.id]
        ).select_related('user').prefetch_related('media', 'likes')


class PostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user']

    def get_queryset(self):
        return Post.objects.select_related('user').prefetch_related('media', 'likes')

    def perform_create(self, serializer):
        post = serializer.save(user=self.request.user)
        # Handle uploaded media files
        files = self.request.FILES.getlist('media_files')
        for i, f in enumerate(files):
            media_type = 'video' if f.content_type.startswith('video') else 'image'
            PostMedia.objects.create(post=post, file=f, media_type=media_type, order=i)


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostSerializer

    def get_queryset(self):
        return Post.objects.select_related('user').prefetch_related('media')

    def perform_update(self, serializer):
        if self.get_object().user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied
        serializer.save()

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied
        instance.delete()


@api_view(['POST'])
def like_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    _, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        return Response({'detail': 'Already liked.'}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'detail': 'Post liked.', 'likes_count': post.likes_count}, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
def unlike_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    deleted, _ = Like.objects.filter(user=request.user, post=post).delete()
    if not deleted:
        return Response({'detail': 'Not liked.'}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'detail': 'Post unliked.', 'likes_count': post.likes_count})


class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer

    def get_queryset(self):
        return Comment.objects.filter(
            post_id=self.kwargs['pk'], parent=None
        ).select_related('user').prefetch_related('replies__user')

    def perform_create(self, serializer):
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        serializer.save(user=self.request.user, post=post)


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer

    def get_queryset(self):
        return Comment.objects.select_related('user')

    def perform_update(self, serializer):
        if self.get_object().user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied
        serializer.save()

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied
        instance.delete()


class UserPostsView(generics.ListAPIView):
    serializer_class = PostSerializer

    def get_queryset(self):
        return Post.objects.filter(
            user__username=self.kwargs['username']
        ).select_related('user').prefetch_related('media', 'likes')
