from django.db import models
from django.conf import settings
from company.models import Company


class ActivityLog(models.Model):

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    action = models.CharField(
        max_length=255
    )

    created = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.user} - {self.action}"