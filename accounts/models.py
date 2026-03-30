from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):

    ROLE_CHOICES = (
        ("OWNER", "Owner"),
        ("MANAGER", "Manager"),
        ("CASHIER", "Cashier"),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="OWNER"
    )

    company = models.ForeignKey(
        "company.Company",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="users"
    )

    branch = models.ForeignKey(
        "company.Branch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff"
    )

    is_active_employee = models.BooleanField(default=True)

    profile_photo = models.ImageField(
        upload_to="profile_photos/",
        null=True,
        blank=True,
        help_text="Profile photo shown in topbar and profile dropdown."
    )

    created = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )

    class Meta:
        indexes = [
            models.Index(fields=["company"]),
            models.Index(fields=["branch"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return f"{self.username} ({self.role})"