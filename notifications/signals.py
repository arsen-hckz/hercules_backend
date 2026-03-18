from django.db.models.signals import post_save
from django.dispatch import receiver
from social.models import Like, Comment
from users.models import Follow
from .models import Notification


@receiver(post_save, sender=Like)
def notify_like(sender, instance, created, **kwargs):
    if created and instance.user != instance.post.user:
        Notification.objects.create(
            recipient=instance.post.user,
            sender=instance.user,
            notification_type='like',
            message=f'{instance.user.username} liked your post.',
            post_id=instance.post.id,
        )


@receiver(post_save, sender=Comment)
def notify_comment(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.parent:
        # Reply to a comment
        if instance.user != instance.parent.user:
            Notification.objects.create(
                recipient=instance.parent.user,
                sender=instance.user,
                notification_type='reply',
                message=f'{instance.user.username} replied to your comment.',
                post_id=instance.post.id,
                comment_id=instance.id,
            )
    else:
        # Top-level comment on a post
        if instance.user != instance.post.user:
            Notification.objects.create(
                recipient=instance.post.user,
                sender=instance.user,
                notification_type='comment',
                message=f'{instance.user.username} commented on your post.',
                post_id=instance.post.id,
                comment_id=instance.id,
            )


@receiver(post_save, sender=Follow)
def notify_follow(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            recipient=instance.following,
            sender=instance.follower,
            notification_type='follow',
            message=f'{instance.follower.username} started following you.',
        )
