from django.shortcuts import redirect
from django.utils import timezone


class SubscriptionMiddleware:
    """Redirects users without active subscription/demo to subscription page."""

    ALLOWED_PATHS = [
        "/login/", "/register/", "/logout/",
        "/forgot-password/", "/reset-password/",
        "/cashier-login/",
        "/subscription/", "/demo-request/",
        "/admin/", "/static/", "/media/",
        "/privacy-policy/",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        for allowed in self.ALLOWED_PATHS:
            if path.startswith(allowed):
                return self.get_response(request)

        if not request.user.is_authenticated:
            return self.get_response(request)

        if request.user.is_superuser or request.user.is_staff:
            return self.get_response(request)

        if getattr(request.user, "is_cashier", False):
            return self.get_response(request)

        company = getattr(request.user, "company", None)
        if not company:
            return redirect("/subscription/")

        if company.subscription_active:
            if company.subscription_end and timezone.now() > company.subscription_end:
                company.subscription_active = False
                company.save(update_fields=["subscription_active"])
                return redirect("/subscription/")
            return self.get_response(request)

        if company.is_demo:
            if company.demo_expiry and timezone.now() > company.demo_expiry:
                company.is_demo = False
                company.save(update_fields=["is_demo"])
                return redirect("/subscription/")
            return self.get_response(request)

        return redirect("/subscription/")
