from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    # User inbox (both URLs work)
    path("", views.inbox, name="inbox"),
    path("inbox/", views.inbox, name="inbox_alias"),
    # AJAX
    path("mark-read/<int:pk>/", views.mark_read, name="mark_read"),
    path("mark-all-read/",      views.mark_all_read, name="mark_all_read"),
    # Admin notification center
    path("admin/",              views.admin_notify, name="admin_notify"),
]
