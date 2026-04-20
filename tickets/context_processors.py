from tickets.models import Notification

def notifications_context(request):
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:5]
        unread_count = unread_notifications.count()
        return {
            'unread_notifications': unread_notifications,
            'unread_count': unread_count
        }
    return {}
