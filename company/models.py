from django.db import models



# =====================================================
# PLAN
# =====================================================

class Plan(models.Model):

    name = models.CharField(max_length=50)

    branch_limit = models.IntegerField()

    cashiers_per_branch = models.IntegerField(default=10)

    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )

    created = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ["price"]

    def __str__(self):
        return self.name


# =====================================================
# COMPANY
# =====================================================

class Company(models.Model):

    name = models.CharField(max_length=200)

    country = models.CharField(max_length=50)

    plan = models.ForeignKey(
        "company.Plan",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    active = models.BooleanField(default=True)

    is_demo = models.BooleanField(default=False)

    demo_expiry = models.DateTimeField(null=True, blank=True, help_text="Demo expires after this datetime")
    demo_requested = models.BooleanField(default=False, help_text="Has requested a demo")

    subscription_active = models.BooleanField(default=False, help_text="Has active paid subscription")
    subscription_start = models.DateTimeField(null=True, blank=True)
    subscription_end = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )

    logo = models.ImageField(
        upload_to="company_logos/",
        null=True,
        blank=True
    )

    address = models.TextField(blank=True, null=True)

    phone = models.CharField(max_length=30, blank=True, null=True)

    email = models.EmailField(blank=True, null=True)

    vat_number = models.CharField(max_length=50, blank=True, null=True)

    currency = models.CharField(max_length=10, default="AED")

    invoice_prefix = models.CharField(max_length=10, default="INV")

    next_invoice_number = models.IntegerField(
        default=1
    )

    BUSINESS_CATEGORY_CHOICES = [
        ('restaurant', '🍕 Restaurant / Café'),
        ('grocery', '🛒 Grocery / Supermarket'),
        ('pharmacy', '💊 Pharmacy'),
        ('salon', '💇 Salon / Spa'),
        ('retail', '👗 Retail / Fashion'),
        ('flower', '🌸 Flower / Gift Shop'),
        ('cloud_kitchen', '☁️ Cloud Kitchen'),
        ('bakery', '🥖 Bakery'),
        ('electronics', '📱 Electronics'),
        ('general', '🏪 General / Other'),
    ]

    business_category = models.CharField(
        max_length=50,
        choices=BUSINESS_CATEGORY_CHOICES,
        default='general',
        blank=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# =====================================================
# BRANCH
# =====================================================

class Branch(models.Model):

    company = models.ForeignKey(
        "company.Company",
        on_delete=models.CASCADE,
        related_name="branches"
    )

    name = models.CharField(max_length=200)

    manager = models.OneToOneField(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_branch"
    )

    created = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.company.name} - {self.name}"


# =====================================================
# UPGRADE REQUEST
# =====================================================

class UpgradeRequest(models.Model):

    company = models.ForeignKey(
        "company.Company",
        on_delete=models.CASCADE,
        related_name="upgrade_requests"
    )

    requested_plan = models.ForeignKey(
        "company.Plan",
        on_delete=models.CASCADE
    )

    approved = models.BooleanField(default=False)

    created = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.company} → {self.requested_plan}"


class Role(models.Model):
    """Custom roles for company users."""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='roles')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    permissions = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['company', 'name']

    def __str__(self):
        return f"{self.company} — {self.name}"


# =====================================================
# DEMO REQUEST
# =====================================================

class DemoRequest(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="demo_requests")
    requested_by = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ], default="pending")
    created = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"Demo Request: {self.company.name} ({self.status})"
