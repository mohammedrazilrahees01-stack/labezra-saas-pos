from django.contrib import admin
from .models import BusinessInvoice, BusinessInvoiceItem

admin.site.register(BusinessInvoice)
admin.site.register(BusinessInvoiceItem)
