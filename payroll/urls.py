from django.urls import path
from . import views

app_name = "payroll"

urlpatterns = [
    path("", views.payroll, name="payroll"),
    path("run/", views.run_payroll, name="run_payroll"),
]