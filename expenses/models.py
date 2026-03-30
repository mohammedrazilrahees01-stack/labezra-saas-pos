from django.db import models
from django.utils import timezone
from company.models import Company


class Expense(models.Model):

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="expenses"
    )

    title = models.CharField(max_length=200)

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    date = models.DateField(default=timezone.now)

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["company"]),
            models.Index(fields=["date"]),
        ]

    def __str__(self):
        return self.title