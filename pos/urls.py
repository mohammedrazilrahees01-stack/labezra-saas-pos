from django.urls import path
from . import views

app_name = "pos"

urlpatterns = [

    # POS MAIN SCREEN
    path("", views.pos_screen, name="pos"),

    # CART ACTIONS
    path("add-to-cart/", views.add_to_cart, name="add_to_cart"),
    path("clear-cart/", views.clear_cart, name="clear_cart"),

    # HOLD BILL SYSTEM
    path("hold-bill/", views.hold_bill, name="hold_bill"),
    path("held-bills/", views.held_bills, name="held_bills"),
    path("held/<int:id>/delete/", views.delete_held_bill, name="delete_held_bill"),
    path("recall/<int:id>/", views.recall_bill, name="recall_bill"),

    # CHECKOUT
    path("checkout/", views.checkout, name="checkout"),

    # RECEIPT
    path("receipt/<int:id>/", views.receipt, name="receipt"),

    # INVOICES
    path("invoices/", views.invoices, name="invoices"),

    # REPORTS
    path("daily-report/", views.daily_report, name="daily_report"),
    path("monthly-report/", views.monthly_report, name="monthly_report"),

    # REFUNDS
    path("refund/<int:id>/", views.refund_invoice, name="refund"),
    path("refunds/", views.refunds, name="refunds"),

    # CSV EXPORT
    path("export-csv/", views.export_csv, name="export_csv"),

    # SHIFT REPORT
    path("shift-report/", views.shift_report, name="shift_report"),

    # CASHIER ANALYTICS
    path("cashier-analytics/", views.cashier_analytics, name="cashier_analytics"),

    # PDF INVOICE
    path("invoice-pdf/<int:id>/", views.invoice_pdf, name="invoice_pdf"),

    # OFFLINE SYNC
    path("sync-offline/", views.sync_offline_transactions, name="sync_offline"),
]