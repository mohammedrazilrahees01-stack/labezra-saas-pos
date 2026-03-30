from django.db import models
from company.models import Company
from customers.models import Customer


class BusinessInvoice(models.Model):

    STATUS_CHOICES = (
        ('unpaid', 'Unpaid'),
        ('paid',   'Paid'),
        ('overdue','Overdue'),
    )

    company  = models.ForeignKey(Company,  on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total    = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    due_date = models.DateField(null=True, blank=True)
    paid     = models.BooleanField(default=False)

    notes    = models.TextField(blank=True, null=True)

    created  = models.DateTimeField(auto_now_add=True)
    updated  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f"Invoice {self.id} - {self.customer.name}"

    @property
    def status_label(self):
        if self.paid:
            return 'paid'
        if self.due_date:
            from django.utils import timezone
            if self.due_date < timezone.now().date():
                return 'overdue'
        return 'unpaid'


class BusinessInvoiceItem(models.Model):

    invoice   = models.ForeignKey(
        BusinessInvoice,
        on_delete=models.CASCADE,
        related_name='items'
    )

    item_name = models.CharField(max_length=200)

    # FIX: was IntegerField — changed to DecimalField to support fractional qty
    qty       = models.DecimalField(max_digits=10, decimal_places=3, default=1)

    price     = models.DecimalField(max_digits=12, decimal_places=2)

    @property
    def line_total(self):
        return self.qty * self.price

    def __str__(self):
        return self.item_name
