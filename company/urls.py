from django.urls import path
from . import views


urlpatterns = [

    # DASHBOARD
    path("dashboard/", views.dashboard, name="dashboard"),

    # COMPANY SETTINGS
    path("settings/company/", views.company_settings, name="company_settings"),

    # BRANCH MANAGEMENT
    path("settings/branches/", views.branches, name="branches"),
    path("settings/branches/add/", views.add_branch, name="add_branch"),
    path("settings/switch-branch/<int:id>/", views.switch_branch, name="switch_branch"),

    # CASHIERS
    path("cashiers/", views.cashiers, name="cashiers"),

    # SUBSCRIPTION
    path("upgrade/", views.upgrade, name="upgrade"),
    path("upgrade/done/", views.upgrade_done, name="upgrade_done"),
    path("subscription/", views.subscription_page, name="subscription"),
    path("demo-request/", views.request_demo, name="request_demo"),

    # USAGE & BILLING
    path("subscription/usage/", views.usage_page, name="usage_page"),

    # VAT TOOL
    path("vat/", views.vat_calculator, name="vat_calculator"),

    # ROLES
    path("settings/roles/", views.roles_list, name="roles_list"),

    # ADMIN UPGRADES
    path("admin-upgrades/", views.admin_upgrade_requests, name="admin_upgrade_requests"),
    path("admin-upgrades/approve/<int:id>/", views.approve_upgrade, name="approve_upgrade"),

    # ADMIN PANEL
    path("admin-panel/", views.admin_panel, name="admin_panel"),

]