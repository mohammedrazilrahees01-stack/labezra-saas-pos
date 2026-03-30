from django.db import models
from company.models import Company, Branch
from accounts.models import User
from inventory.models import Product
from customers.models import Customer


# ==============================
# INVOICE
# ==============================

class Invoice(models.Model):

    PAYMENT_CHOICES = (
        ('CASH', 'Cash'),
        ('CARD', 'Card'),
        ('UPI',  'UPI'),
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE
    )

    cashier = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    shift = models.ForeignKey(
        'Shift',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    number = models.CharField(
        max_length=50
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    vat = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_CHOICES
    )

    cash_received = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    balance_returned = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # Hold / Recall
    is_hold   = models.BooleanField(default=False)
    cart_data = models.JSONField(null=True, blank=True)

    # Refund
    is_refunded = models.BooleanField(default=False)

    # Void (government-grade audit requirement)
    is_voided   = models.BooleanField(default=False)
    void_reason = models.CharField(max_length=300, blank=True, null=True)
    voided_by   = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='voided_invoices'
    )
    voided_at = models.DateTimeField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.number

    # Convenience aliases used by report templates
    @property
    def vat_amount(self):
        """Alias for .vat — used in report templates as tx.vat_amount."""
        return self.vat

    @property
    def items_count(self):
        """Number of line items — used in report templates as tx.items_count."""
        # If annotated by QuerySet, avoid an extra DB hit
        val = self.__dict__.get('_items_count')
        if val is not None:
            return val
        return self.items.count()


# ==============================
# INVOICE ITEMS
# ==============================

class InvoiceItem(models.Model):

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True
    )

    name = models.CharField(max_length=200)

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    quantity = models.IntegerField()

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    def __str__(self):
        return f'{self.name} x{self.quantity}'


# ==============================
# SHIFT
# ==============================

class Shift(models.Model):

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE
    )

    cashier = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    opening_cash = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    closing_cash = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    opened_at = models.DateTimeField(auto_now_add=True)

    closed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    is_open = models.BooleanField(default=True)

    class Meta:
        ordering = ['-opened_at']

    def __str__(self):
        return f'Shift {self.id} - {self.cashier}'

    @property
    def duration_display(self):
        if self.closed_at:
            delta = self.closed_at - self.opened_at
            hours, remainder = divmod(delta.seconds, 3600)
            minutes = remainder // 60
            return f'{hours}h {minutes}m'
        return 'Active'
