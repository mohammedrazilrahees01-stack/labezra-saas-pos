from django.contrib import admin
from django.contrib import messages as django_messages
from .models import Notification, BroadcastNotification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "type", "read", "created_at")
    list_filter = ("type", "read")
    search_fields = ("title", "message", "user__username")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


@admin.register(BroadcastNotification)
class BroadcastNotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "type", "sent", "created_at")
    list_filter = ("type", "sent", "company")
    search_fields = ("title", "message")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
    actions = ["dispatch_to_users"]

    def dispatch_to_users(self, request, queryset):
        """
        Send selected broadcast notifications to all target users.
        This action creates a per-user Notification row for every
        active user in the target company (or all companies if blank).
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()

        dispatched = 0

        for broadcast in queryset.filter(sent=False):

            if broadcast.company:
                users = User.objects.filter(company=broadcast.company, is_active=True)
            else:
                users = User.objects.filter(is_active=True)

            notifications = [
                Notification(
                    user=user,
                    title=broadcast.title,
                    message=broadcast.message,
                    type=broadcast.type,
                    link=broadcast.link,
                )
                for user in users
            ]

            Notification.objects.bulk_create(notifications)

            broadcast.sent = True
            broadcast.save()

            dispatched += len(notifications)

        self.message_user(
            request,
            f"✅ Dispatched {dispatched} notification(s) to users.",
            django_messages.SUCCESS
        )

    dispatch_to_users.short_description = "Send selected broadcasts to users"
