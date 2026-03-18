from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user
        ).select_related('sender')


@api_view(['POST'])
def mark_read(request, pk):
    notif = generics.get_object_or_404(Notification, pk=pk, recipient=request.user)
    notif.is_read = True
    notif.save(update_fields=['is_read'])
    return Response({'detail': 'Marked as read.'})


@api_view(['POST'])
def mark_all_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return Response({'detail': 'All notifications marked as read.'})


@api_view(['GET'])
def unread_count(request):
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return Response({'unread_count': count})
