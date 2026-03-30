from .models import Notification


def notifications(request):

    if not request.user.is_authenticated:
        return {}

    notes = Notification.objects.filter(
        user=request.user,
        read=False
    ).order_by("-created_at")[:10]

    # Convert to list first so we can call len() after slicing
    notes_list = list(notes)

    return {
        "notifications": notes_list,
        "notifications_count": len(notes_list)
    }
