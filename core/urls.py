from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect, render
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView


# Privacy Policy view (simple inline view — no separate app needed)
def privacy_policy(request):
    return render(request, "core/privacy_policy.html")


def create_quotation(request):
    from django.contrib import messages
    if request.method == 'POST':
        messages.success(request, f"Quotation created for {request.POST.get('customer_name', 'customer')}. Add line items to complete.")
    return redirect('/sales/quotations/')


# Generic coming-soon view for stub modules
def coming_soon(request, title='Coming Soon'):
    return render(request, "coming_soon.html", {'title': title})


urlpatterns = [

    # ROOT REDIRECT
    path("", lambda request: redirect("/login/")),

    # ==============================
    # DJANGO ADMIN
    # ==============================
    path("admin/", admin.site.urls),

    # ==============================
    # AUTHENTICATION
    # ==============================
    path("", include("accounts.urls")),

    # ==============================
    # COMPANY / DASHBOARD
    # ==============================
    path("", include("company.urls")),

    # ==============================
    # BUSINESS MODULES
    # ==============================
    path("inventory/", include("inventory.urls")),
    path("pos/", include("pos.urls")),
    path("customers/", include("customers.urls")),
    path("employees/", include("employees.urls")),
    path("expenses/", include("expenses.urls")),
    path("payroll/", include("payroll.urls")),
    path("accounting/", include("accounting.urls")),

    # ==============================
    # ACTIVITY LOG
    # ==============================
    path("activity/", include("activity.urls")),

    # ==============================
    # NOTIFICATIONS
    # ==============================
    path("notifications/", include("notifications.urls")),

    # ==============================
    # STATIC PAGES
    # ==============================
    path("privacy-policy/", privacy_policy, name="privacy_policy"),

    # ==============================
    # SALES MODULE (STUB)
    # ==============================
    path("sales/quotations/", lambda r: render(r, "sales/quotations.html"), name="sales_quotations"),
    path("sales/quotations/create/", create_quotation, name="quotation_create"),
    path("sales/orders/", lambda r: render(r, "sales/sales_orders.html"), name="sales_orders"),
    path("sales/credit-notes/", lambda r: render(r, "sales/credit_notes.html"), name="credit_notes"),
    path("sales/delivery-notes/", lambda r: render(r, "sales/delivery_notes.html"), name="delivery_notes"),
    path("sales/invoices/", lambda r: render(r, 'sales/invoices.html'), name="sales_invoices"),
    path("sales/invoices/create/", lambda r: render(r, 'sales/create_invoice.html'), name="create_invoice"),
    path("sales/proforma/", lambda r: render(r, 'sales/proforma.html'), name="proforma_invoices"),
    path("sales/recurring/", lambda r: render(r, 'sales/recurring.html'), name="recurring_invoices"),
    path("sales/returns/", lambda r: render(r, 'sales/returns.html'), name="sales_returns"),

    # ==============================
    # CRM MODULE (STUB)
    # ==============================
    path("crm/leads/", lambda r: render(r, "crm/leads.html"), name="crm_leads"),
    path("crm/loyalty/", lambda r: render(r, "crm/loyalty.html"), name="crm_loyalty"),
    path("crm/portal/", lambda r: render(r, 'crm/portal.html'), name="customer_portal"),

    # ==============================
    # WAREHOUSE MODULE (STUB)
    # ==============================
    path("warehouse/", lambda r: render(r, "warehouse/list.html"), name="warehouse_list"),
    path("warehouse/movements/", lambda r: render(r, "warehouse/transfers.html"), name="warehouse_movements"),
    path("warehouse/audit/", lambda r: render(r, "warehouse/audit.html"), name="warehouse_audit"),

    # ==============================
    # PURCHASES (STUB)
    # ==============================
    path("purchases/supplier-quotes/", lambda r: render(r, 'purchases/supplier_quotes.html'), name="supplier_quotes"),
    path("purchases/grn/", lambda r: render(r, 'purchases/grn.html'), name="grn"),
    path("purchases/returns/", lambda r: render(r, 'purchases/returns.html'), name="purchase_returns"),

    # ==============================
    # FINANCE MODULE (STUB)
    # ==============================
    path("finance/general-ledger/", lambda r: render(r, "finance/general_ledger.html"), name="general_ledger"),
    path("finance/chart-of-accounts/", lambda r: render(r, 'finance/chart_of_accounts.html'), name="chart_of_accounts"),
    path("finance/journal-entries/", lambda r: render(r, "finance/journal_entries.html"), name="journal_entries"),
    path("finance/trial-balance/", lambda r: render(r, "finance/trial_balance.html"), name="trial_balance"),
    path("finance/pl-statement/", lambda r: render(r, "finance/pl_statement.html"), name="pl_statement"),
    path("finance/balance-sheet/", lambda r: render(r, "finance/balance_sheet.html"), name="balance_sheet"),
    path("finance/cash-flow/", lambda r: render(r, "finance/cash_flow.html"), name="cash_flow"),

    # ==============================
    # PAYROLL EXTRAS (STUB)
    # ==============================
    path("payroll/payslips/", lambda r: render(r, 'payroll/payslips.html'), name="payslips"),

    # ==============================
    # TAX / ZATCA (STUB)
    # ==============================
    path("tax/zatca/", lambda r: render(r, 'tax/zatca.html'), name="zatca"),

    # ==============================
    # HR EXTRAS (STUB)
    # ==============================
    path("employees/attendance/", lambda r: render(r, 'employees/attendance.html'), name="attendance"),
    path("employees/leaves/", lambda r: render(r, 'employees/leaves.html'), name="leave_management"),
    path("employees/performance/", lambda r: render(r, 'employees/performance.html'), name="performance"),

    # ==============================
    # BRANCHES EXTRAS (STUB)
    # ==============================
    path("settings/settings/branches/warehouses/", lambda r: render(r, 'branches/warehouses.html'), name="branch_warehouses"),

    # ==============================
    # PROJECTS MODULE (STUB)
    # ==============================
    path("projects/", include("projects.urls")),

    # ==============================
    # ANALYTICS MODULE (STUB)
    # ==============================
    path("analytics/", lambda r: render(r, "analytics/dashboard.html"), name="analytics_dashboard"),
    path("reports/sales/", lambda r: render(r, "analytics/sales_report.html"), name="sales_report"),
    path("reports/inventory/", lambda r: render(r, "analytics/inventory_report.html"), name="inventory_report"),
    path("reports/financial/", lambda r: render(r, 'reports/financial.html'), name="financial_report"),

    # ==============================
    # SETTINGS EXTRAS (STUB)
    # ==============================
    path("settings/security/", lambda r: render(r, "settings/security.html"), name="settings_security"),
    path("settings/notifications/", lambda r: render(r, "settings/notifications_settings.html"), name="settings_notifications"),
    path("settings/integrations/", lambda r: render(r, "settings/integrations.html"), name="settings_integrations"),
    # settings/roles/ is handled by company.urls
    path("settings/backup/", lambda r: render(r, "settings/backup.html"), name="settings_backup"),
    path("settings/privacy/", lambda r: render(r, "settings/privacy.html"), name="settings_privacy"),
    path("settings/users/", lambda r: render(r, 'settings/users.html'), name="user_management"),
    path("settings/payment-gateways/", lambda r: render(r, 'settings/payment_gateways.html'), name="payment_gateways"),

    # ==============================
    # SUPPORT (STUB)
    # ==============================
    path("support/", lambda r: render(r, "support/index.html"), name="support"),

    # admin-panel is handled by company.urls (included via path("", include("company.urls")))

    # ==============================
    # REPORTS HUB
    # ==============================
    path("reports/", login_required(lambda r: render(r, "reports/reports.html")), name="reports_hub"),

    # ==============================
    # CALENDAR (v7)
    # ==============================
    path("calendar/", login_required(TemplateView.as_view(template_name='calendar/calendar.html')), name="calendar"),

    # ==============================
    # GUIDELINES (v7)
    # ==============================
    path("guidelines/", login_required(TemplateView.as_view(template_name='guidelines/guidelines.html')), name="guidelines"),

    # ==============================
    # AI INTELLIGENCE (v7)
    # ==============================
    path("ai/", login_required(TemplateView.as_view(template_name='ai/ai_dashboard.html')), name="ai_dashboard"),

    # ==============================
    # SUBSCRIPTION EXTRAS (STUB)
    # ==============================
    # usage handled by company.urls
    path("pos/shifts/", lambda r: render(r, 'pos/shifts.html'), name="shift_management"),
    path("pos/cash-management/", lambda r: render(r, 'pos/cash_management.html'), name="cash_management"),

    # ==============================
    # EXPENSE EXTRAS (STUB)
    # ==============================
    path("expenses/add/", lambda r: render(r, 'expenses/add_expense.html'), name="add_expense"),
    path("expenses/reports/", lambda r: render(r, 'expenses/reports.html'), name="expense_reports"),

    # ==============================
    # INVENTORY EXTRAS (STUB)
    # ==============================
    path("inventory/variants/", lambda r: render(r, 'inventory/variants.html'), name="product_variants"),
    path("inventory/barcodes/", lambda r: render(r, 'inventory/barcodes.html'), name="barcodes"),
    path("inventory/stock-adjustments/", lambda r: render(r, 'inventory/stock_adjustments.html'), name="stock_adjustments"),
    path("inventory/stock-transfers/", lambda r: render(r, "inventory/stock_transfers.html"), name="stock_transfers"),

]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
