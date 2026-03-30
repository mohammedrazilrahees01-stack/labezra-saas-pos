from django.db import models
from company.models import Company


class Employee(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    position = models.CharField(max_length=200, blank=True)
    salary = models.FloatField(default=0)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
