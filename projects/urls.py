from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('tasks/', views.task_list, name='task_list'),
    path('time-tracking/', views.time_tracking, name='time_tracking'),
]
