from django.urls import path
from . import views

app_name = "expenses"

urlpatterns = [
    path("export/", views.export_expenses_csv, name="export_expenses_csv"),
    path("", views.expenses, name="expenses"),
]