from django.shortcuts import redirect


class RoleRedirectMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.user.is_authenticated:

            if request.path.startswith("/dashboard/"):

                if request.user.role == "CASHIER":
                    return redirect("/pos/")

        response = self.get_response(request)
        return response