from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


def owner_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != "OWNER":
            return redirect("/dashboard/")
        return view_func(request, *args, **kwargs)
    return wrapper


def cashier_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != "CASHIER":
            return redirect("/dashboard/")
        return view_func(request, *args, **kwargs)
    return wrapper
