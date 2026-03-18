from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_CHOICES = [
        ('like', 'Liked your post'),
        ('comment', 'Commented on your post'),
        ('reply', 'Replied to your comment'),
        ('follow', 'Started following you'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_notifications'
    )
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)

    # Generic link to the relevant object
    post_id = models.PositiveIntegerField(null=True, blank=True)
    comment_id = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.sender} → {self.recipient}: {self.notification_type}'
