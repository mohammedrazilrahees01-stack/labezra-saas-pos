from decimal import Decimal

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, F
from django.utils import timezone
from django.contrib import messages

from .models import Plan, Branch, UpgradeRequest, Company
from accounts.models import User
from pos.models import Invoice
from expenses.models import Expense
from inventory.models import Product
from employees.models import Employee
from customers.models import Customer
from activity.models import ActivityLog


# ==========================================
# COMPANY SETTINGS
# ==========================================

@login_required
def company_settings(request):

    if request.user.role != "OWNER":
        return redirect("/dashboard/")

    company = request.user.company

    if request.method == "POST":

        company.name = request.POST.get("name")
        company.country = request.POST.get("country")
        company.address = request.POST.get("address")
        company.phone = request.POST.get("phone")
        company.email = request.POST.get("email")
        company.vat_number = request.POST.get("vat_number")
        company.currency = request.POST.get("currency")
        company.invoice_prefix = request.POST.get("invoice_prefix")

        if request.FILES.get("logo"):
            company.logo = request.FILES.get("logo")

        company.save()

        return redirect("/settings/company/")

    return render(request, "company/company_settings.html", {
        "company": company
    })


# ==========================================
# VAT CALCULATOR
# ==========================================

@login_required
def vat_calculator(request):

    result = None
    vat_amount = None
    net_amount = None

    vat_rate = Decimal("0.05")

    if request.user.company and request.user.company.country:

        country = request.user.company.country.lower()

        if "saudi" in country or "ksa" in country:
            vat_rate = Decimal("0.15")

    if request.method == "POST":

        amount = Decimal(request.POST.get("amount", "0"))
        mode = request.POST.get("mode")

        if mode == "exclusive":

            vat_amount = amount * vat_rate
            net_amount = amount + vat_amount

        elif mode == "inclusive":

            vat_amount = amount - (amount / (Decimal("1") + vat_rate))
            net_amount = amount - vat_amount

        result = True

    return render(request, "settings/vat_calculator.html", {
        "result": result,
        "vat_amount": vat_amount,
        "net_amount": net_amount,
        "vat_rate": vat_rate
    })
# ==========================================
# DASHBOARD
# ==========================================
from django.shortcuts import render
from django.db.models import Sum, F
from django.utils import timezone
import json
from django.contrib.auth.decorators import login_required

from pos.models import Invoice, InvoiceItem
from expenses.models import Expense
from inventory.models import Product
from customers.models import Customer
from employees.models import Employee
from activity.models import ActivityLog


@login_required
def dashboard(request):

    company = request.user.company

    # Auto inventory alerts (v7)
    try:
        from notifications.auto_alerts import check_and_create_alerts
        from accounts.models import User as UserModel
        alert_users = UserModel.objects.filter(company=company, role__in=['OWNER', 'MANAGER'])
        check_and_create_alerts(company, alert_users)
    except Exception:
        pass

    range_filter = request.GET.get("range", "7d")

    today = timezone.now()

    if range_filter == "today":
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)

    elif range_filter == "30d":
        start_date = today - timezone.timedelta(days=30)

    elif range_filter == "1y":
        start_date = today - timezone.timedelta(days=365)

    else:  # default: 7d
        start_date = today - timezone.timedelta(days=7)


    # ── Filtered invoices for the selected range ──────────────────
    invoices = Invoice.objects.filter(
        company=company,
        created__gte=start_date,
        is_refunded=False
    )

    revenue = round(float(invoices.aggregate(
        total=Sum("total")
    )["total"] or 0), 2)

    orders = invoices.count()

    # NOTE: Expense.date is a DateField, so we compare with .date()
    expenses = round(float(Expense.objects.filter(
        company=company,
        date__gte=start_date.date()
    ).aggregate(
        total=Sum("amount")
    )["total"] or 0), 2)

    profit = round(revenue - expenses, 2)


    # ── Today's sales ─────────────────────────────────────────────
    today_sales = round(float(Invoice.objects.filter(
        company=company,
        created__date=today.date(),
        is_refunded=False
    ).aggregate(total=Sum("total"))["total"] or 0), 2)


    # ── Summary counts ────────────────────────────────────────────
    total_products  = Product.objects.filter(company=company).count()
    total_customers = Customer.objects.filter(company=company).count()
    total_employees = Employee.objects.filter(company=company).count()

    total_expenses = round(float(Expense.objects.filter(
        company=company
    ).aggregate(total=Sum("amount"))["total"] or 0), 2)


    # ── Recent invoices & activity ────────────────────────────────
    recent_invoices = Invoice.objects.filter(
        company=company
    ).order_by("-created")[:5]

    logs = ActivityLog.objects.filter(
        company=company
    ).order_by("-created")[:10]


    # ── Low stock products ────────────────────────────────────────
    low_stock_products = Product.objects.filter(
        company=company,
        stock__lte=F("low_stock")
    )


    # ── Weekly sales chart (last 7 days) ──────────────────────────
    sales_labels = []
    sales_data   = []

    for i in range(7):
        day = today - timezone.timedelta(days=6 - i)
        total = Invoice.objects.filter(
            company=company,
            created__date=day.date(),
            is_refunded=False
        ).aggregate(total=Sum("total"))["total"] or 0

        sales_labels.append(day.strftime("%a"))
        sales_data.append(round(float(total), 2))


    # ── Monthly revenue chart (last 12 months) ────────────────────
    monthly_labels = []
    monthly_data   = []

    for i in range(12):
        month = today - timezone.timedelta(days=30 * (11 - i))
        total = Invoice.objects.filter(
            company=company,
            created__year=month.year,
            created__month=month.month,
            is_refunded=False
        ).aggregate(total=Sum("total"))["total"] or 0

        monthly_labels.append(month.strftime("%b"))
        monthly_data.append(round(float(total), 2))


    # ── Inventory doughnut ────────────────────────────────────────
    total_products_count = Product.objects.filter(company=company).count()

    low_stock_count = Product.objects.filter(
        company=company,
        stock__lte=F("low_stock")
    ).count()

    in_stock = total_products_count - low_stock_count
    inventory_data = [in_stock, low_stock_count]


    # ── Top 5 selling products ────────────────────────────────────
    top_products = (
        InvoiceItem.objects
        .filter(invoice__company=company, invoice__is_refunded=False)
        .values("product__name")
        .annotate(total_qty=Sum("quantity"))
        .order_by("-total_qty")[:5]
    )

    product_labels = [p["product__name"] or "Unknown" for p in top_products]
    product_data   = [int(p["total_qty"]) for p in top_products]


    return render(request, "dashboard/dashboard.html", {

        "range": range_filter,

        "today_sales":     today_sales,
        "revenue":         revenue,
        "orders":          orders,
        "profit":          profit,

        "total_products":  total_products,
        "total_customers": total_customers,
        "total_employees": total_employees,
        "total_expenses":  total_expenses,

        "recent_invoices":    recent_invoices,
        "logs":               logs,
        "low_stock_products": low_stock_products,

        "sales_labels":   json.dumps(sales_labels),
        "sales_data":     json.dumps(sales_data),

        "monthly_labels": json.dumps(monthly_labels),
        "monthly_data":   json.dumps(monthly_data),

        "inventory_data": json.dumps(inventory_data),

        "product_labels": json.dumps(product_labels),
        "product_data":   json.dumps(product_data),
    })


# ==========================================
# BRANCHES
# ==========================================

@login_required
def branches(request):

    company = request.user.company

    if request.method == "POST":

        plan = company.plan

        branch_count = Branch.objects.filter(company=company).count()

        if plan and branch_count >= plan.branch_limit:

            messages.error(
                request,
                "Branch limit reached for your plan. Please upgrade."
            )

            return redirect("/settings/branches/")

        name = request.POST.get("name")

        Branch.objects.create(
            company=company,
            name=name
        )

        messages.success(request, "Branch created successfully.")

    branches = Branch.objects.filter(company=company)

    return render(
        request,
        "company/branches.html",
        {"branches": branches}
    )


@login_required
# ==========================================
# ADD BRANCH
# ==========================================

@login_required
def add_branch(request):
    """Dedicated page for adding a new branch."""

    company = request.user.company

    if request.method == "POST":

        plan = company.plan
        branch_count = Branch.objects.filter(company=company).count()

        if plan and branch_count >= plan.branch_limit:
            messages.error(request, "Branch limit reached for your current plan. Please upgrade.")
            return redirect("/settings/branches/")

        name    = request.POST.get("name", "").strip()
        address = request.POST.get("address", "").strip()
        phone   = request.POST.get("phone", "").strip()

        if name:
            Branch.objects.create(company=company, name=name)
            messages.success(request, f"Branch '{name}' created successfully.")
            return redirect("/settings/branches/")
        else:
            messages.error(request, "Branch name is required.")

    return render(request, "company/add_branch.html", {"company": company})


@login_required
def switch_branch(request, id):

    request.session["active_branch"] = id

    return redirect("/dashboard/")


# ==========================================
# CASHIERS
# ==========================================

@login_required
def cashiers(request):

    cashiers = User.objects.filter(
        company=request.user.company,
        role="CASHIER"
    )

    return render(request, "employees/cashiers.html", {
        "cashiers": cashiers
    })


# ==========================================
# UPGRADE
# ==========================================

@login_required
def upgrade(request):

    company = request.user.company
    plans = Plan.objects.all()

    if request.method == "POST":

        selected_plan_id = request.POST.get("plan")

        if selected_plan_id:

            selected_plan = Plan.objects.get(id=selected_plan_id)

            UpgradeRequest.objects.create(
                company=company,
                requested_plan=selected_plan,
                approved=False
            )

            return redirect("/upgrade/done/")

    return render(request, "subscription/upgrade.html", {
        "plans": plans
    })


@login_required
def upgrade_done(request):

    return render(request, "subscription/upgrade_done.html")


# ==========================================
# ADMIN UPGRADE APPROVAL
# ==========================================

@staff_member_required
def admin_upgrade_requests(request):

    requests = UpgradeRequest.objects.select_related(
        "company",
        "requested_plan"
    ).filter(approved=False)

    return render(request, "subscription/admin_upgrade_requests.html", {
        "requests": requests
    })


@staff_member_required
def approve_upgrade(request, id):

    req = UpgradeRequest.objects.get(id=id)

    company = req.company
    company.plan = req.requested_plan
    company.save()

    req.approved = True
    req.save()

    return redirect("/admin-upgrades/")


# ─────────────────────────────────────────────────────────────
# ROLES & PERMISSIONS
# ─────────────────────────────────────────────────────────────

@login_required
def roles_list(request):
    from .models import Role
    company = request.user.company
    roles = Role.objects.filter(company=company)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if name:
            Role.objects.get_or_create(
                company=company,
                name=name,
                defaults={'description': description}
            )
            messages.success(request, f'Role "{name}" created successfully!')
        else:
            messages.error(request, 'Role name is required.')
        return redirect('/settings/roles/')

    return render(request, 'settings/roles_permissions.html', {
        'roles': roles,
    })


# =====================================================
# SUBSCRIPTION PAGE
# =====================================================

@login_required
def subscription_page(request):
    from django.shortcuts import redirect as _redirect
    from django.utils import timezone as tz

    # Superusers / staff with no company attached → send to admin panel
    if request.user.is_superuser or request.user.is_staff:
        return _redirect("/admin/")

    company = getattr(request.user, "company", None)

    # Edge-case: regular user with no company record yet
    if not company:
        return render(request, "subscription/subscription.html", {
            "company": None,
            "plans": [],
            "has_subscription": False,
            "has_demo": False,
            "demo_days_left": 0,
            "pending_request": None,
        })

    # If they already have an active subscription → go straight to dashboard
    if company.subscription_active:
        if not (company.subscription_end and tz.now() > company.subscription_end):
            return _redirect("/dashboard/")

    # If they have an active demo → go straight to dashboard
    if company.is_demo:
        if not (company.demo_expiry and tz.now() > company.demo_expiry):
            return _redirect("/dashboard/")

    # Auto-create default plans if none exist yet
    if not Plan.objects.exists():
        Plan.objects.create(name="Starter", branch_limit=1, cashiers_per_branch=3, price=35)
        Plan.objects.create(name="Pro", branch_limit=3, cashiers_per_branch=10, price=75)
        Plan.objects.create(name="Enterprise", branch_limit=10, cashiers_per_branch=25, price=150)

    plans = Plan.objects.all().order_by("price")

    has_subscription = company.subscription_active
    has_demo = company.is_demo
    demo_days_left = 0

    if has_demo and company.demo_expiry:
        delta = company.demo_expiry - tz.now()
        demo_days_left = max(0, delta.days)
        if delta.total_seconds() > 0:
            demo_days_left = max(1, demo_days_left)

    from .models import DemoRequest
    pending_request = DemoRequest.objects.filter(company=company, status="pending").first()

    return render(request, "subscription/subscription.html", {
        "company": company,
        "plans": plans,
        "has_subscription": has_subscription,
        "has_demo": has_demo,
        "demo_days_left": demo_days_left,
        "pending_request": pending_request,
    })


@login_required
def request_demo(request):
    if request.method == "POST":
        company = getattr(request.user, "company", None)
        if not company:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("No company associated with this account.")
        from .models import DemoRequest

        existing = DemoRequest.objects.filter(company=company, status="pending").exists()
        if existing:
            messages.warning(request, "You already have a pending demo request.")
            return redirect("/subscription/")

        msg = request.POST.get("message", "").strip()
        DemoRequest.objects.create(company=company, requested_by=request.user, message=msg)
        company.demo_requested = True
        company.save(update_fields=["demo_requested"])

        try:
            from activity.logger import log_activity
            log_activity(request, "demo_request", f"Demo requested for {company.name}")
        except Exception:
            pass

        messages.success(request, "Demo request submitted! The Labezra team will review it shortly.")
        return redirect("/subscription/")

    return redirect("/subscription/")


# ==========================================
# USAGE & BILLING PAGE
# ==========================================

@login_required
def usage_page(request):
    from django.utils import timezone as tz
    company = request.user.company
    plan = company.plan

    now = tz.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Real counts from DB
    try:
        from pos.models import Invoice
        transactions_this_month = Invoice.objects.filter(
            branch__company=company, created_at__gte=start_of_month
        ).count()
    except Exception:
        transactions_this_month = 0

    product_count = Product.objects.filter(company=company).count()
    employee_count = Employee.objects.filter(company=company).count()
    branch_count = company.branches.count()

    # Plan limits (defaults if no plan)
    plan_branch_limit = plan.branch_limit if plan else "—"
    plan_cashiers = plan.cashiers_per_branch if plan else "—"
    plan_price = plan.price if plan else None
    plan_name = plan.name if plan else "No Active Plan"

    return render(request, "subscription/usage.html", {
        "company": company,
        "plan": plan,
        "plan_name": plan_name,
        "plan_price": plan_price,
        "plan_branch_limit": plan_branch_limit,
        "plan_cashiers": plan_cashiers,
        "transactions_this_month": transactions_this_month,
        "product_count": product_count,
        "employee_count": employee_count,
        "branch_count": branch_count,
    })


# ==========================================
# ADMIN PANEL VIEW
# ==========================================

@staff_member_required
def admin_panel(request):
    """
    Central admin panel: manage demo requests, subscriptions, companies.
    Staff/superuser only.
    """
    from .models import DemoRequest
    from django.utils import timezone as tz
    from datetime import timedelta

    # ── Stats cards ──────────────────────────────────────────
    total_companies      = Company.objects.count()
    pending_demos        = DemoRequest.objects.filter(status="pending").count()
    active_subscriptions = Company.objects.filter(subscription_active=True).count()
    active_demos         = Company.objects.filter(is_demo=True, demo_expiry__gt=tz.now()).count()
    expired              = Company.objects.filter(subscription_active=False, is_demo=False, demo_requested=True).count()

    # ── Data ─────────────────────────────────────────────────
    demo_requests = DemoRequest.objects.filter(
        status="pending"
    ).select_related("company", "requested_by").order_by("-created")

    all_companies = Company.objects.prefetch_related("users").order_by("-created_at")[:50]
    plans         = Plan.objects.all().order_by("price")

    # ── POST actions ─────────────────────────────────────────
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "approve_demo":
            try:
                demo_req = DemoRequest.objects.get(id=request.POST.get("demo_id"))
                demo_req.status      = "approved"
                demo_req.reviewed_at = tz.now()
                demo_req.save()
                company              = demo_req.company
                company.is_demo      = True
                company.demo_expiry  = tz.now() + timedelta(hours=72)
                company.save(update_fields=["is_demo", "demo_expiry"])
                messages.success(request, f"✅ Demo approved for {company.name}. 72-hour trial active.")
            except DemoRequest.DoesNotExist:
                messages.error(request, "Demo request not found.")

        elif action == "reject_demo":
            try:
                demo_req             = DemoRequest.objects.get(id=request.POST.get("demo_id"))
                demo_req.status      = "rejected"
                demo_req.reviewed_at = tz.now()
                demo_req.save()
                messages.success(request, "Demo request rejected.")
            except DemoRequest.DoesNotExist:
                messages.error(request, "Demo request not found.")

        elif action == "enable_subscription":
            try:
                company  = Company.objects.get(id=request.POST.get("company_id"))
                plan_id  = request.POST.get("plan_id")
                months   = int(request.POST.get("months", 3))
                if plan_id:
                    company.plan = Plan.objects.get(id=plan_id)
                now                        = tz.now()
                company.subscription_active = True
                company.subscription_start  = now
                company.subscription_end    = now + timedelta(days=30 * months)
                company.is_demo             = False
                company.save()
                messages.success(request, f"✅ Subscription enabled for {company.name} ({months} months).")
            except (Company.DoesNotExist, Plan.DoesNotExist) as e:
                messages.error(request, f"Error: {e}")

        return redirect("/admin-panel/")

    return render(request, "admin_panel/index.html", {
        "total_companies":      total_companies,
        "pending_demos":        pending_demos,
        "active_subscriptions": active_subscriptions,
        "active_demos":         active_demos,
        "expired":              expired,
        "demo_requests":        demo_requests,
        "all_companies":        all_companies,
        "plans":                plans,
    })
