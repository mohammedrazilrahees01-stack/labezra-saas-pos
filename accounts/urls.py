from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [

    path("login/", views.login_view, name="login"),

    path("register/", views.register_view, name="register"),

    path("logout/", views.logout_view, name="logout"),

    path("profile/", views.profile, name="profile"),
    path("profile/update-photo/", views.update_photo, name="update_photo"),

    path("cashier-login/", views.cashier_login, name="cashier_login"),

    path("add-cashier/", views.add_cashier, name="add_cashier"),


    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("reset-password/", views.reset_password, name="reset_password"),

    path("accounts/change-password/", views.change_password, name="change_password"),
]