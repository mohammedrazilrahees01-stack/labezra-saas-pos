"""
Core middleware for Labezra ERP.
"""
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings


class MaintenanceModeMiddleware:
    """
    Shows a maintenance page when MAINTENANCE_MODE = True in settings.
    Superusers bypass the maintenance mode.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(settings, 'MAINTENANCE_MODE', False):
            if hasattr(request, 'user') and request.user.is_superuser:
                return self.get_response(request)
            if request.path.startswith('/admin/'):
                return self.get_response(request)
            return render(request, 'errors/maintenance.html', status=503)
        return self.get_response(request)
