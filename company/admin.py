from django.contrib import admin
from django.utils import timezone
from datetime import timedelta
from .models import Company, Branch, Plan, UpgradeRequest, DemoRequest, Role


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "branch_limit", "cashiers_per_branch"]
    search_fields = ["name"]


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "country", "plan", "subscription_active", "is_demo", "demo_expiry", "active"]
    list_filter = ["subscription_active", "is_demo", "active", "country"]
    search_fields = ["name", "email"]
    list_editable = ["subscription_active", "is_demo", "active"]
    actions = ["activate_demo_3_days", "activate_subscription", "deactivate_all"]

    def activate_demo_3_days(self, request, queryset):
        for company in queryset:
            company.is_demo = True
            company.demo_expiry = timezone.now() + timedelta(days=3)
            company.save(update_fields=["is_demo", "demo_expiry"])
        self.message_user(request, f"Demo activated for {queryset.count()} companies (3 days).")
    activate_demo_3_days.short_description = "Activate 3-day demo"

    def activate_subscription(self, request, queryset):
        for company in queryset:
            company.subscription_active = True
            company.subscription_start = timezone.now()
            company.subscription_end = timezone.now() + timedelta(days=365)
            company.is_demo = False
            company.save(update_fields=["subscription_active", "subscription_start", "subscription_end", "is_demo"])
        self.message_user(request, f"Subscription activated for {queryset.count()} companies (1 year).")
    activate_subscription.short_description = "Activate 1-year subscription"

    def deactivate_all(self, request, queryset):
        queryset.update(subscription_active=False, is_demo=False)
        self.message_user(request, f"Deactivated {queryset.count()} companies.")
    deactivate_all.short_description = "Deactivate subscription & demo"


@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = ["company", "requested_by", "status", "created", "reviewed_at"]
    list_filter = ["status"]
    search_fields = ["company__name"]
    list_editable = ["status"]
    actions = ["approve_and_activate_demo"]

    def approve_and_activate_demo(self, request, queryset):
        for demo_req in queryset.filter(status="pending"):
            demo_req.status = "approved"
            demo_req.reviewed_at = timezone.now()
            demo_req.save()
            company = demo_req.company
            company.is_demo = True
            company.demo_expiry = timezone.now() + timedelta(days=3)
            company.save(update_fields=["is_demo", "demo_expiry"])
        self.message_user(request, f"Approved {queryset.count()} demo requests (3-day demo activated).")
    approve_and_activate_demo.short_description = "Approve & activate 3-day demo"


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "manager"]
    list_filter = ["company"]


@admin.register(UpgradeRequest)
class UpgradeRequestAdmin(admin.ModelAdmin):
    list_display = ["company", "requested_plan", "approved", "created"]
    list_filter = ["approved"]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "is_active"]
    list_filter = ["company", "is_active"]
