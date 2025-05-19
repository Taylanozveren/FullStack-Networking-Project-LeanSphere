# core/context_processors.py

from .models import Notification

def unread_notifications(request):
    if request.user.is_authenticated:
        count = request.user.notifications.filter(is_read=False).count()
        return {'unread_notifications_count': count}
    return {'unread_notifications_count': 0}

def recent_notifications(request):
    if request.user.is_authenticated:
        notes = request.user.notifications.all()[:5]
        return {'recent_notifications': notes}
    return {'recent_notifications': []}

def notifications_processor(request):
    if request.user.is_authenticated:
        # okunmamış sayısı
        unread_qs = Notification.objects.filter(user=request.user, is_read=False)
        # son 5 bildirimi çekiyoruz (dropdown için)
        latest_qs = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        return {
            'unread_count': unread_qs.count(),
            'latest_notifications': latest_qs,
        }
    return {}