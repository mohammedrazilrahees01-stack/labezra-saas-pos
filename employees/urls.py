from django.urls import path
from . import views

app_name = "employees"

urlpatterns = [
    path("", views.employees, name="employees"),
    path("add/", views.add_employee, name="add_employee"),
    path("edit/<int:id>/", views.edit_employee, name="edit_employee"),
    path("delete/<int:id>/", views.delete_employee, name="delete_employee"),
    path("export/", views.export_employees_csv, name="export_employees_csv"),
]