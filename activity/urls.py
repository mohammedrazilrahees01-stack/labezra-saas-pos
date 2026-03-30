from django.urls import path
from .views import activity_log

urlpatterns = [
    path('', activity_log, name='activity_log'),
]
