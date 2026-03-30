from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Notification(models.Model):
    """
    Per-user notification (shown in the topbar bell icon).
    Created automatically when an admin dispatches a BroadcastNotification,
    or by system code (e.g. low stock alerts, shift reminders).
    """

    TYPE_CHOICES = [
        ("info",    "Info"),
        ("success", "Success"),
        ("warning", "Warning"),
        ("error",   "Error"),
    ]

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title      = models.CharField(max_length=200)
    message    = models.TextField(blank=True, default="")
    type       = models.CharField(max_length=20, choices=TYPE_CHOICES, default="info")
    link       = models.URLField(blank=True, default="")
    read       = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.type}] {self.title} → {self.user}"


class BroadcastNotification(models.Model):
    """
    A notification created by the Django admin that gets pushed to
    all users in a company (or all users if company is blank).

    How to use:
    1. Go to Django Admin → Notifications → Broadcast Notifications
    2. Click "Add Broadcast Notification" and fill in title + message
    3. Select the target company (leave blank to send to ALL companies)
    4. Save the record
    5. Back on the list, tick the checkbox and choose action
       "Send selected broadcasts to users" → Go

    The action will create a Notification row for each active user
    in the target company (or all active users if company is blank).
    The bell icon will then show the unread count immediately.
    """

    TYPE_CHOICES = [
        ("info",    "Info"),
        ("success", "Success"),
        ("warning", "Warning"),
        ("error",   "Error"),
    ]

    company    = models.ForeignKey(
                    "company.Company",
                    on_delete=models.CASCADE,
                    null=True,
                    blank=True,
                    help_text="Leave blank to broadcast to ALL companies."
                 )
    title      = models.CharField(max_length=200)
    message    = models.TextField(
                    blank=True,
                    default="",
                    help_text="Optional body text shown under the title."
                 )
    type       = models.CharField(max_length=20, choices=TYPE_CHOICES, default="info")
    link       = models.URLField(blank=True, default="", help_text="Optional click-through URL.")
    sent       = models.BooleanField(
                    default=False,
                    help_text="Set to True after the broadcast action runs."
                 )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Broadcast Notification"
        verbose_name_plural = "Broadcast Notifications"

    def __str__(self):
        target = self.company.name if self.company else "ALL"
        status = "✅ Sent" if self.sent else "⏳ Pending"
        return f"{status} | {self.title} → {target}"
