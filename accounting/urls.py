from django.urls import path
from . import views

app_name = "accounting"

urlpatterns = [

    path("", views.business_invoices, name="accounting_home"),

    # =====================================
    # BUSINESS INVOICES
    # =====================================

    path(
        "business-invoices/",
        views.business_invoices,
        name="business_invoices"
    ),

    path(
        "business-invoices/create/",
        views.create_business_invoice,
        name="create_business_invoice"
    ),

    path(
        "business-invoices/pdf/<int:id>/",
        views.invoice_pdf,
        name="business_invoice_pdf"
    ),

]