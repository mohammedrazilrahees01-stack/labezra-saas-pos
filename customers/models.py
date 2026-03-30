from django.db import models
from company.models import Company


class Customer(models.Model):

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="customers"
    )

    name = models.CharField(max_length=200)

    phone = models.CharField(max_length=50, blank=True)

    email = models.EmailField(blank=True)

    trn = models.CharField(max_length=50, blank=True)

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["company"]),
        ]

    def __str__(self):
        return self.name