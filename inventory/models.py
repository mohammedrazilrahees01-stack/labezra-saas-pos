from django.db import models
from company.models import Company


class Category(models.Model):

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE
    )

    name = models.CharField(
        max_length=200
    )

    created = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


class Supplier(models.Model):

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE
    )

    name = models.CharField(
        max_length=200
    )

    phone = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    created = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


class Product(models.Model):

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE
    )


    image = models.ImageField(
        upload_to="products/",
        null=True,
        blank=True
    )

    name = models.CharField(
        max_length=200
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    barcode = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    stock = models.IntegerField(
        default=0
    )

    low_stock = models.IntegerField(
        default=5
    )

    expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="Optional: Product expiry/best-before date"
    )

    created = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


class Purchase(models.Model):

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE
    )

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    qty = models.IntegerField(
        default=0
    )

    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    created = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        if self.product:
            return f"{self.product.name} purchase"
        return "Purchase"


class StockHistory(models.Model):

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True
    )

    action = models.CharField(
        max_length=50
    )

    qty = models.IntegerField()

    note = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    created = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.product.name} {self.action}"