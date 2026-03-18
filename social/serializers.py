from rest_framework import serializers
from .models import Post, PostMedia, Like, Comment
from users.serializers import UserMinimalSerializer


class PostMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostMedia
        fields = ['id', 'file', 'media_type', 'order']


class CommentSerializer(serializers.ModelSerializer):
    user = UserMinimalSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'user', 'content', 'parent', 'replies', 'created_at']
        read_only_fields = ['user']

    def get_replies(self, obj):
        if obj.parent is None:
            return CommentSerializer(obj.replies.all(), many=True, context=self.context).data
        return []


class PostSerializer(serializers.ModelSerializer):
    user = UserMinimalSerializer(read_only=True)
    media = PostMediaSerializer(many=True, read_only=True)
    likes_count = serializers.ReadOnlyField()
    comments_count = serializers.ReadOnlyField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'user', 'content', 'workout_session',
            'media', 'likes_count', 'comments_count', 'is_liked',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['user']

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(user=request.user, post=obj).exists()
        return False
