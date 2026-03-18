from rest_framework import serializers
from .models import Notification
from users.serializers import UserMinimalSerializer


class NotificationSerializer(serializers.ModelSerializer):
    sender = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'sender', 'notification_type', 'message', 'is_read', 'post_id', 'comment_id', 'created_at']
        read_only_fields = ['sender', 'notification_type', 'message', 'post_id', 'comment_id', 'created_at']
