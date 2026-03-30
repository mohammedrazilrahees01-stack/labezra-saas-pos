from .models import ActivityLog


def log_activity(user, action):

    if not user:
        return

    company = getattr(user, "company", None)

    if not company:
        return

    ActivityLog.objects.create(
        company=company,
        user=user,
        action=action
    )