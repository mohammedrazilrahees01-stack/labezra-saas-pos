import calendar
import csv
import json
from decimal import Decimal
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from django.db.models.functions import ExtractDay, ExtractHour
from django.db.models import Count as ItemCount
from django.contrib import messages

from inventory.models import Product, StockHistory, Category
from customers.models import Customer
from company.models import Branch
from .models import Invoice, InvoiceItem, Shift
from activity.logger import log_activity
from .pdf import generate_invoice_pdf


# =====================================================
# POS SCREEN
# =====================================================

@login_required
def pos_screen(request):
    branch_id = request.session.get("active_branch")
    if not branch_id:
        first_branch = Branch.objects.filter(company=request.user.company).first()
        if first_branch:
            request.session["active_branch"] = first_branch.id
            branch_id = first_branch.id
        else:
            return render(request, "pos/pos.html", {
                "blocker": True,
                "blocker_message": "No branch found. You need to create a Branch before using the POS.",
                "blocker_link": "/settings/branches/",
                "blocker_link_label": "Create Branch",
                "categories": [],
                "products": [],
                "customers": [],
                "cart": {},
                "cart_items": [],
                "cart_total": 0,
                "cart_tax": 0,
                "cart_grand_total": 0,
                "branches": [],
                "active_branch": None,
                "selected_category": None,
            })

    categories = Category.objects.filter(company=request.user.company)
    selected_category = request.GET.get("category")

    products = Product.objects.filter(company=request.user.company)
    if selected_category:
        products = products.filter(category_id=selected_category)

    customers = Customer.objects.filter(company=request.user.company)
    cart = request.session.get("cart", {})

    if request.method == "POST":
        pid = None

        if request.POST.get("barcode"):
            code = request.POST.get("barcode").strip()
            prod = Product.objects.filter(
                barcode=code, company=request.user.company
            ).first()
            if prod:
                pid = str(prod.id)

        elif request.POST.get("product"):
            pid = str(request.POST.get("product"))

        elif request.POST.get("plus"):
            pid = str(request.POST.get("plus"))

        if pid:
            cart[pid] = cart.get(pid, 0) + 1

        elif "minus" in request.POST:
            pid = str(request.POST.get("minus"))
            if pid in cart:
                cart[pid] -= 1
                if cart[pid] <= 0:
                    del cart[pid]

        elif request.POST.get("remove"):
            pid = str(request.POST.get("remove"))
            if pid in cart:
                del cart[pid]

        request.session["cart"] = cart
        request.session.modified = True
        return redirect(request.get_full_path())

    cart_items, subtotal, vat, grand = calculate_cart(cart, request.user.company)

    return render(request, "pos/pos.html", {
        "products": products,
        "categories": categories,
        "selected_category": selected_category,
        "customers": customers,
        "cart_items": cart_items,
        "total": subtotal,
        "vat": vat,
        "grand": grand,
    })


# =====================================================
# ADD PRODUCT TO CART (AJAX)
# =====================================================

@login_required
def add_to_cart(request):
    if "cart" not in request.session:
        request.session["cart"] = {}

    cart = request.session["cart"]
    product_id = request.POST.get("product_id")

    if product_id:
        pid = str(product_id)
        if Product.objects.filter(id=pid, company=request.user.company).exists():
            cart[pid] = cart.get(pid, 0) + 1
            request.session["cart"] = cart
            request.session.modified = True

            items, subtotal, vat, grand = calculate_cart(cart, request.user.company)

            return JsonResponse({
                "status": "success",
                "subtotal": float(subtotal),
                "vat": float(vat),
                "grand": float(grand),
                "item_count": len(cart),
            })

    return JsonResponse({"error": "Product not found or invalid ID"}, status=400)


# =====================================================
# CHECKOUT
# =====================================================

@login_required
@transaction.atomic
def checkout(request):
    cart = request.session.get("cart", {})
    if not cart:
        messages.warning(request, "Your cart is empty.")
        return redirect("/pos/")

    company = request.user.company
    branch_id = request.session.get("active_branch")

    if not branch_id:
        fallback_branch = Branch.objects.filter(company=company).first()
        if fallback_branch:
            branch_id = fallback_branch.id
        else:
            messages.error(request, "No active branch found.")
            return redirect("/pos/")

    payment = request.POST.get("payment", "CASH")
    customer_id = request.POST.get("customer")
    discount_percent = Decimal(request.POST.get("discount_percent") or "0")
    discount_amount = Decimal(request.POST.get("discount_amount") or "0")
    cash_received = Decimal(request.POST.get("cash") or "0")

    subtotal = Decimal("0")
    products_to_update = []

    for pid, qty in cart.items():
        product = Product.objects.select_for_update().get(id=int(pid), company=company)
        if product.stock < qty:
            messages.error(request, f"Insufficient stock for {product.name}.")
            return redirect("/pos/")
        subtotal += product.price * qty
        products_to_update.append((product, qty))

    disc_from_percent = subtotal * (discount_percent / Decimal("100"))
    total_discount = disc_from_percent + discount_amount
    taxable_amount = subtotal - total_discount
    vat_amount = taxable_amount * Decimal("0.05")
    grand_total = taxable_amount + vat_amount

    if payment == "CASH" and cash_received < grand_total:
        messages.error(
            request,
            f"Insufficient cash! Total: {grand_total:.2f}, Received: {cash_received:.2f}",
        )
        return redirect("/pos/")

    customer = (
        Customer.objects.filter(id=customer_id, company=company).first()
        if customer_id
        else None
    )
    shift = Shift.objects.filter(cashier=request.user, is_open=True).first()
    inv_number = f"{company.invoice_prefix}-{company.next_invoice_number:06d}"

    invoice = Invoice.objects.create(
        company=company,
        branch_id=branch_id,
        cashier=request.user,
        customer=customer,
        shift=shift,
        number=inv_number,
        subtotal=subtotal,
        discount=total_discount,
        vat=vat_amount,
        total=grand_total,
        payment_method=payment,
        cash_received=cash_received,
        balance_returned=cash_received - grand_total if payment == "CASH" else Decimal("0"),
        is_hold=False,
        cart_data=cart,
    )

    company.next_invoice_number += 1
    company.save()

    for product, qty in products_to_update:
        product.stock -= qty
        product.save()

        StockHistory.objects.create(
            company=company,
            product=product,
            user=request.user,
            action="OUT",
            qty=qty,
            note=f"POS Sale {inv_number}",
        )

        InvoiceItem.objects.create(
            invoice=invoice,
            product=product,
            name=product.name,
            price=product.price,
            quantity=qty,
            total=product.price * qty,
        )

    log_activity(request.user, f"Completed Sale {inv_number}")
    request.session["cart"] = {}
    request.session.modified = True

    return redirect(f"/pos/receipt/{invoice.id}/")


# =====================================================
# RECEIPT
# =====================================================

@login_required
def receipt(request, id):
    invoice = get_object_or_404(Invoice, id=id, company=request.user.company)
    items = InvoiceItem.objects.filter(invoice=invoice)

    return render(request, "pos/receipt.html", {
        "invoice": invoice,
        "items": items,
        "now": datetime.now(),
    })


# =====================================================
# INVOICE LIST
# =====================================================

@login_required
def invoices(request):
    inv_qs = Invoice.objects.filter(
        company=request.user.company,
        is_hold=False,
    ).select_related("customer", "cashier").order_by("-created")

    agg = inv_qs.filter(is_refunded=False).aggregate(
        t_rev=Sum("total"),
        t_vat=Sum("vat"),
    )
    total_revenue   = agg["t_rev"] or Decimal("0")
    total_vat       = agg["t_vat"] or Decimal("0")
    refunded_count  = inv_qs.filter(is_refunded=True).count()

    return render(request, "pos/invoices.html", {
        "invoices": inv_qs,
        "total_revenue": total_revenue,
        "total_vat": total_vat,
        "refunded_count": refunded_count,
    })


# =====================================================
# DAILY REPORT
# =====================================================

@login_required
def daily_report(request):
    date_str = request.GET.get("date")
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else timezone.now().date()
    except ValueError:
        selected_date = timezone.now().date()

    invoices = Invoice.objects.filter(
        company=request.user.company,
        created__date=selected_date,
        is_refunded=False,
        is_hold=False,
    ).select_related("customer", "cashier").annotate(
        _items_count=ItemCount("items")
    ).order_by("-created")

    total         = invoices.aggregate(t=Sum("total"))["t"]    or Decimal("0")
    total_vat     = invoices.aggregate(t=Sum("vat"))["t"]      or Decimal("0")
    total_disc    = invoices.aggregate(t=Sum("discount"))["t"] or Decimal("0")
    invoice_count = invoices.count()

    # Payment method breakdowns
    cash_total = invoices.filter(payment_method="CASH").aggregate(s=Sum("total"))["s"] or Decimal("0")
    card_total = invoices.filter(payment_method="CARD").aggregate(s=Sum("total"))["s"] or Decimal("0")
    bank_total = invoices.filter(payment_method="UPI").aggregate(s=Sum("total"))["s"]  or Decimal("0")

    # Percentages (safe divide)
    total_f  = float(total) if total else 1
    cash_pct = round(float(cash_total) / total_f * 100, 1) if total else 0
    card_pct = round(float(card_total) / total_f * 100, 1) if total else 0
    bank_pct = round(float(bank_total) / total_f * 100, 1) if total else 0

    # Average order value
    avg_order_value = round(float(total) / invoice_count, 2) if invoice_count else 0

    # Net revenue (excl. VAT)
    net_revenue = total - total_vat

    # Hourly breakdown — 24-element list
    hourly_raw = (
        invoices
        .annotate(hour=ExtractHour("created"))
        .values("hour")
        .annotate(t=Sum("total"))
        .order_by("hour")
    )
    hourly_map = {row["hour"]: float(row["t"]) for row in hourly_raw}
    hourly_data = json.dumps([round(hourly_map.get(h, 0), 2) for h in range(24)])


    # ---- EXPORT CSV / PDF ----
    export_fmt = request.GET.get("export")
    if export_fmt == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="daily_report_{selected_date}.csv"'
        writer = csv.writer(response)
        writer.writerow(["Daily Sales Report", str(selected_date)])
        writer.writerow([])
        writer.writerow(["Summary"])
        writer.writerow(["Total Sales (AED)", str(total)])
        writer.writerow(["Total Orders", str(invoice_count)])
        writer.writerow(["Average Order Value (AED)", str(avg_order_value)])
        writer.writerow(["VAT Collected (AED)", str(total_vat)])
        writer.writerow(["Net Revenue (AED)", str(net_revenue)])
        writer.writerow(["Cash Sales (AED)", str(cash_total)])
        writer.writerow(["Card Sales (AED)", str(card_total)])
        writer.writerow(["Bank Transfer (AED)", str(bank_total)])
        writer.writerow([])
        writer.writerow(["Time", "Invoice #", "Customer", "Total", "Payment"])
        for tx in invoices:
            writer.writerow([
                tx.created.strftime("%H:%M") if tx.created else "",
                tx.number, getattr(tx.customer, "name", "Walk-in") if tx.customer else "Walk-in",
                str(tx.total), tx.payment_method,
            ])
        return response

    if export_fmt == "pdf":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="daily_report_{selected_date}.csv"'
        writer = csv.writer(response)
        writer.writerow(["Daily Sales Report", str(selected_date)])
        writer.writerow(["Total Sales (AED)", str(total)])
        writer.writerow(["Total Orders", str(invoice_count)])
        writer.writerow(["VAT Collected (AED)", str(total_vat)])
        writer.writerow([])
        writer.writerow(["Time", "Invoice #", "Total", "Payment"])
        for tx in invoices:
            writer.writerow([tx.created.strftime("%H:%M") if tx.created else "", tx.number, str(tx.total), tx.payment_method])
        return response

    return render(request, "reports/daily_report.html", {
        # Both naming conventions so the template always finds the right var
        "invoices":        invoices,
        "transactions":    invoices,
        "report_date":     selected_date,
        "selected_date":   selected_date,
        "total":           total,
        "total_sales":     total,
        "total_vat":       total_vat,
        "total_discount":  total_disc,
        "total_orders":    invoice_count,
        "invoice_count":   invoice_count,
        "avg_order_value": avg_order_value,
        "cash_sales":      cash_total,
        "card_sales":      card_total,
        "cash_total":      cash_total,
        "card_total":      card_total,
        "bank_total":      bank_total,
        "cash_pct":        cash_pct,
        "card_pct":        card_pct,
        "bank_pct":        bank_pct,
        "net_revenue":     net_revenue,
        "hourly_data":     hourly_data,
    })


# =====================================================
# MONTHLY REPORT
# =====================================================

@login_required
def monthly_report(request):
    now = timezone.now()
    try:
        year  = int(request.GET.get("year",  now.year))
        month = int(request.GET.get("month", now.month))
    except (ValueError, TypeError):
        year, month = now.year, now.month

    invoices = Invoice.objects.filter(
        company=request.user.company,
        created__year=year,
        created__month=month,
        is_refunded=False,
        is_hold=False,
    ).select_related("customer", "cashier").order_by("-created")

    total         = invoices.aggregate(t=Sum("total"))["t"] or Decimal("0")
    total_vat     = invoices.aggregate(t=Sum("vat"))["t"]   or Decimal("0")
    invoice_count = invoices.count()

    years = list(range(now.year - 3, now.year + 2))
    months_list = [
        (1, "January"),  (2, "February"), (3, "March"),    (4, "April"),
        (5, "May"),      (6, "June"),     (7, "July"),      (8, "August"),
        (9, "September"),(10, "October"), (11, "November"), (12, "December"),
    ]

    # ---- Daily breakdown (current month) ----
    days_in_month = calendar.monthrange(year, month)[1]
    daily_qs = (
        invoices
        .annotate(day=ExtractDay("created"))
        .values("day")
        .annotate(t=Sum("total"))
        .order_by("day")
    )
    daily_map = {row["day"]: float(row["t"]) for row in daily_qs}
    monthly_daily_data = json.dumps(
        [round(daily_map.get(d, 0), 2) for d in range(1, days_in_month + 1)]
    )

    # ---- Previous month comparison ----
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1

    prev_days = calendar.monthrange(prev_year, prev_month)[1]
    prev_invoices = Invoice.objects.filter(
        company=request.user.company,
        created__year=prev_year,
        created__month=prev_month,
        is_refunded=False,
        is_hold=False,
    )
    prev_daily_qs = (
        prev_invoices
        .annotate(day=ExtractDay("created"))
        .values("day")
        .annotate(t=Sum("total"))
        .order_by("day")
    )
    prev_map = {row["day"]: float(row["t"]) for row in prev_daily_qs}
    prev_monthly_data = json.dumps(
        [round(prev_map.get(d, 0), 2) for d in range(1, prev_days + 1)]
    )

    # ---- Best day ----
    best_day_date   = None
    best_day_amount = Decimal("0")
    if daily_map:
        best_day_num = max(daily_map, key=daily_map.get)
        import datetime as _dt
        best_day_date   = _dt.date(year, month, best_day_num)
        best_day_amount = Decimal(str(daily_map[best_day_num]))

    # ---- Average daily revenue ----
    active_days       = len(daily_map)
    avg_daily_revenue = round(float(total) / active_days, 2) if active_days else 0

    # ---- Top 10 products ----
    top_products = list(
        InvoiceItem.objects
        .filter(invoice__in=invoices)
        .values("name")
        .annotate(units_sold=Sum("quantity"), revenue=Sum("total"))
        .order_by("-revenue")[:10]
    )

    # ---- Payment breakdown ----
    total_f = float(total) if total else 1
    payment_breakdown = []
    for pm_code, pm_label in [("CASH", "Cash"), ("CARD", "Card"), ("UPI", "Bank Transfer")]:
        pm_total = (
            invoices.filter(payment_method=pm_code).aggregate(t=Sum("total"))["t"]
            or Decimal("0")
        )
        pct = round(float(pm_total) / total_f * 100, 1) if total else 0
        payment_breakdown.append({"method": pm_label, "total": pm_total, "pct": pct})

    # ---- VAT due date (28th of following month) ----
    import datetime as _dt2
    if month == 12:
        vat_due_date = _dt2.date(year + 1, 1, 28)
    else:
        vat_due_date = _dt2.date(year, month + 1, 28)


    # ---- EXPORT CSV / PDF ----
    export_fmt = request.GET.get("export")
    if export_fmt == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="monthly_report_{year}_{month:02d}.csv"'
        writer = csv.writer(response)
        writer.writerow(["Monthly Sales Report", f"{year}-{month:02d}"])
        writer.writerow([])
        writer.writerow(["Total Revenue (AED)", str(total)])
        writer.writerow(["Total Orders", str(invoice_count)])
        writer.writerow(["Total VAT (AED)", str(total_vat)])
        writer.writerow(["Average Daily Revenue (AED)", str(avg_daily_revenue)])
        writer.writerow([])
        writer.writerow(["Payment Breakdown"])
        for pb in payment_breakdown:
            writer.writerow([pb["method"], f'AED {pb["total"]}', f'{pb["pct"]}%'])
        writer.writerow([])
        writer.writerow(["Top Products"])
        writer.writerow(["Product", "Units Sold", "Revenue (AED)"])
        for p in top_products:
            writer.writerow([p["name"], p["units_sold"], str(p["revenue"])])
        return response

    if export_fmt == "pdf":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="monthly_report_{year}_{month:02d}.csv"'
        writer = csv.writer(response)
        writer.writerow(["Monthly Sales Report", f"{year}-{month:02d}"])
        writer.writerow(["Total Revenue (AED)", str(total)])
        writer.writerow(["Total Orders", str(invoice_count)])
        writer.writerow(["Total VAT (AED)", str(total_vat)])
        writer.writerow([])
        writer.writerow(["Top Products"])
        for p in top_products:
            writer.writerow([p["name"], p["units_sold"], str(p["revenue"])])
        return response

    return render(request, "reports/monthly_report.html", {
        "invoices":           invoices,
        "total":              total,
        "total_revenue":      total,
        "total_vat":          total_vat,
        "invoice_count":      invoice_count,
        "total_orders":       invoice_count,
        "selected_year":      year,
        "selected_month":     month,
        "years":              years,
        "available_years":    years,
        "months":             months_list,
        "monthly_daily_data": monthly_daily_data,
        "prev_monthly_data":  prev_monthly_data,
        "best_day_date":      best_day_date,
        "best_day_amount":    best_day_amount,
        "avg_daily_revenue":  avg_daily_revenue,
        "top_products":       top_products,
        "payment_breakdown":  payment_breakdown,
        "vat_due_date":       vat_due_date,
    })


# =====================================================
# REFUND
# =====================================================

@login_required
@transaction.atomic
def refund_invoice(request, id):
    invoice = get_object_or_404(Invoice, id=id, company=request.user.company)

    if invoice.is_refunded:
        messages.warning(request, "This invoice has already been refunded.")
        return redirect("/pos/refunds/")

    items = InvoiceItem.objects.filter(invoice=invoice)

    for item in items:
        if item.product:
            item.product.stock += item.quantity
            item.product.save()

            StockHistory.objects.create(
                company=request.user.company,
                product=item.product,
                user=request.user,
                action="IN",
                qty=item.quantity,
                note=f"Refund Invoice {invoice.number}",
            )

    invoice.is_refunded = True
    invoice.save()

    log_activity(request.user, f"Refunded Invoice {invoice.number}")
    messages.success(request, f"Invoice {invoice.number} refunded successfully.")
    return redirect("/pos/refunds/")


# =====================================================
# REFUND LIST
# =====================================================

@login_required
def refunds(request):
    refunded = Invoice.objects.filter(
        company=request.user.company,
        is_refunded=True,
    ).select_related("customer", "cashier").order_by("-created")

    total_refunded = refunded.aggregate(t=Sum("total"))["t"] or Decimal("0")

    return render(request, "pos/refunds.html", {
        "refunds": refunded,
        "total_refunded": total_refunded,
    })


# =====================================================
# HELD BILLS
# =====================================================

@login_required
def held_bills(request):
    holds = Invoice.objects.filter(
        company=request.user.company,
        is_hold=True,
    ).select_related("cashier").order_by("-created")

    return render(request, "pos/held_bills.html", {"holds": holds})


# =====================================================
# HOLD BILL
# =====================================================

@login_required
def hold_bill(request):
    cart = request.session.get("cart", {})
    if not cart:
        messages.warning(request, "Cart is empty — nothing to hold.")
        return redirect("/pos/")

    company = request.user.company
    branch_id = request.session.get("active_branch")

    if not branch_id:
        fallback = Branch.objects.filter(company=company).first()
        if fallback:
            branch_id = fallback.id
        else:
            messages.error(request, "No active branch found.")
            return redirect("/pos/")

    cart_items, subtotal, vat, grand = calculate_cart(cart, company)
    hold_number = f"HOLD-{timezone.now().strftime('%Y%m%d%H%M%S')}-{request.user.id}"

    Invoice.objects.create(
        company=company,
        branch_id=branch_id,
        cashier=request.user,
        number=hold_number,
        subtotal=subtotal,
        discount=Decimal("0"),
        vat=vat,
        total=grand,
        payment_method="CASH",
        cash_received=Decimal("0"),
        balance_returned=Decimal("0"),
        is_hold=True,
        cart_data=cart,
    )

    request.session["cart"] = {}
    request.session.modified = True
    messages.success(request, "Bill held successfully.")
    return redirect("/pos/")


# =====================================================
# RECALL HOLD BILL
# =====================================================

@login_required
def recall_bill(request, id):
    bill = get_object_or_404(
        Invoice, id=id, is_hold=True, company=request.user.company
    )
    request.session["cart"] = bill.cart_data
    request.session.modified = True
    bill.delete()
    return redirect("/pos/")


# =====================================================
# CLEAR CART
# =====================================================

@login_required
def clear_cart(request):
    request.session["cart"] = {}
    request.session.modified = True
    return redirect("/pos/")


# =====================================================
# SHIFT REPORT
# =====================================================

@login_required
def shift_report(request):
    date_from_str    = request.GET.get("date_from", "")
    date_to_str      = request.GET.get("date_to",   "")
    selected_cashier = request.GET.get("cashier",   "")

    try:
        date_from = datetime.strptime(date_from_str, "%Y-%m-%d").date() if date_from_str else timezone.now().date()
    except ValueError:
        date_from = timezone.now().date()

    try:
        date_to = datetime.strptime(date_to_str, "%Y-%m-%d").date() if date_to_str else date_from
    except ValueError:
        date_to = date_from

    # Query Shift objects for the company/date range
    shifts_qs = Shift.objects.filter(
        branch__company=request.user.company,
        opened_at__date__gte=date_from,
        opened_at__date__lte=date_to,
    ).select_related("cashier", "branch").order_by("-opened_at")

    if selected_cashier:
        shifts_qs = shifts_qs.filter(cashier_id=selected_cashier)

    # Enrich each Shift with computed invoice totals
    enriched_shifts  = []
    total_sales      = Decimal("0")
    total_discounts  = Decimal("0")
    total_opening    = Decimal("0")
    total_closing    = Decimal("0")
    closing_count    = 0

    for shift in shifts_qs:
        inv_qs = Invoice.objects.filter(
            shift=shift, is_refunded=False, is_hold=False
        )
        shift_sales     = inv_qs.aggregate(t=Sum("total"))["t"]    or Decimal("0")
        shift_discounts = inv_qs.aggregate(t=Sum("discount"))["t"] or Decimal("0")

        if shift.closing_cash is not None:
            # Expected cash = opening + sales; difference = actual closing - expected
            cash_diff = shift.closing_cash - (shift.opening_cash + shift_sales)
            closing_count   += 1
            total_closing   += shift.closing_cash
        else:
            cash_diff = None

        total_opening   += shift.opening_cash
        total_sales     += shift_sales
        total_discounts += shift_discounts

        enriched_shifts.append({
            "number":         f"SHIFT-{shift.id:04d}",
            "cashier":        shift.cashier,
            "date":           shift.opened_at.date(),
            "opened_at":      shift.opened_at,
            "closed_at":      shift.closed_at,
            "opening_cash":   shift.opening_cash,
            "closing_cash":   shift.closing_cash,
            "sales_total":    shift_sales,
            "total_discounts": shift_discounts,
            "cash_difference": cash_diff,
            "status":         "open" if shift.is_open else "closed",
        })

    total_shifts      = len(enriched_shifts)
    avg_opening_cash  = (round(total_opening / total_shifts, 2)  if total_shifts   else Decimal("0"))
    avg_closing_cash  = (round(total_closing / closing_count, 2) if closing_count  else Decimal("0"))

    # Cashiers active in this date range (for filter dropdown)
    from accounts.models import User as AuthUser
    cashier_ids = Invoice.objects.filter(
        company=request.user.company,
        created__date__gte=date_from,
        created__date__lte=date_to,
        is_hold=False,
    ).values_list("cashier_id", flat=True).distinct()
    cashiers = AuthUser.objects.filter(id__in=cashier_ids)

    # Export CSV
    if request.GET.get("export") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="shift_report_{date_from}_{date_to}.csv"'
        writer = csv.writer(response)
        writer.writerow([
            "Shift #", "Cashier", "Date", "Opened", "Closed",
            "Opening Cash", "Closing Cash", "Sales Total", "Discounts", "Status"
        ])
        for s in enriched_shifts:
            writer.writerow([
                s["number"],
                s["cashier"].username if s["cashier"] else "",
                s["date"],
                s["opened_at"].strftime("%H:%M"),
                s["closed_at"].strftime("%H:%M") if s["closed_at"] else "Active",
                round(s["opening_cash"],   2),
                round(s["closing_cash"],   2) if s["closing_cash"] is not None else "",
                round(s["sales_total"],    2),
                round(s["total_discounts"], 2),
                s["status"],
            ])
        return response

    return render(request, "reports/shift_report.html", {
        "shifts":           enriched_shifts,
        "total_shifts":     total_shifts,
        "total_sales":      total_sales,
        "total_discounts":  total_discounts,
        "avg_opening_cash": avg_opening_cash,
        "avg_closing_cash": avg_closing_cash,
        "selected_cashier": selected_cashier,
        "cashiers":         cashiers,
        "date_from":        date_from_str,
        "date_to":          date_to_str,
    })


# =====================================================
# CASHIER ANALYTICS
# =====================================================

@login_required
def cashier_analytics(request):
    date_from_str = request.GET.get("date_from", "")
    date_to_str   = request.GET.get("date_to",   "")

    qs = Invoice.objects.filter(
        company=request.user.company,
        is_refunded=False,
        is_hold=False,
    )

    try:
        if date_from_str:
            qs = qs.filter(created__date__gte=datetime.strptime(date_from_str, "%Y-%m-%d").date())
        if date_to_str:
            qs = qs.filter(created__date__lte=datetime.strptime(date_to_str, "%Y-%m-%d").date())
    except ValueError:
        pass

    # Per-cashier aggregation
    raw_data = list(
        qs.values("cashier__username", "cashier__first_name", "cashier__last_name")
        .annotate(
            sales=Sum("total"),
            invoice_count=Count("id"),
            avg_sale=Avg("total"),
            total_vat=Sum("vat"),
            total_discount=Sum("discount"),
        )
        .order_by("-sales")
    )

    # Grand totals
    grand_total = Decimal("0")
    for row in raw_data:
        row["sales"]          = row["sales"]         or Decimal("0")
        row["avg_sale"]       = row["avg_sale"]       or Decimal("0")
        row["total_vat"]      = row["total_vat"]      or Decimal("0")
        row["total_discount"] = row["total_discount"] or Decimal("0")
        grand_total          += row["sales"]

    # Share % + payment breakdown per cashier
    for row in raw_data:
        row["share_pct"] = (
            round(float(row["sales"] / grand_total * 100), 1) if grand_total else 0
        )
        cashier_qs = qs.filter(cashier__username=row["cashier__username"])
        row["cash_sales"] = cashier_qs.filter(payment_method="CASH").aggregate(s=Sum("total"))["s"] or Decimal("0")
        row["card_sales"] = cashier_qs.filter(payment_method="CARD").aggregate(s=Sum("total"))["s"] or Decimal("0")
        row["upi_sales"]  = cashier_qs.filter(payment_method="UPI").aggregate(s=Sum("total"))["s"]  or Decimal("0")

    grand_count = sum(r["invoice_count"] for r in raw_data)
    grand_avg   = (grand_total / grand_count) if grand_count else Decimal("0")
    grand_vat   = sum(r["total_vat"] for r in raw_data)

    cash_total = qs.filter(payment_method="CASH").aggregate(s=Sum("total"))["s"] or Decimal("0")
    card_total = qs.filter(payment_method="CARD").aggregate(s=Sum("total"))["s"] or Decimal("0")
    upi_total  = qs.filter(payment_method="UPI").aggregate(s=Sum("total"))["s"]  or Decimal("0")

    # Build cashier list matching template expectations
    cashier_objects = []
    for row in raw_data:
        uname     = row["cashier__username"] or "Unknown"
        fname     = (row["cashier__first_name"] or "").strip()
        lname     = (row["cashier__last_name"]  or "").strip()
        full_name = f"{fname} {lname}".strip() or uname
        cashier_objects.append({
            "name":             full_name,
            "username":         uname,
            "total_sales":      row["sales"],
            "transaction_count": row["invoice_count"],
            "avg_transaction":  row["avg_sale"],
            "share_pct":        row["share_pct"],
            "discounts_given":  row["total_discount"],
        })

    top_cashier_name  = cashier_objects[0]["name"] if cashier_objects else "—"
    avg_per_cashier   = round(float(grand_total) / len(cashier_objects), 2) if cashier_objects else 0

    # Chart data as JSON (used by template's <script type="application/json">)
    cashier_chart_data = json.dumps({
        "labels": [c["name"] for c in cashier_objects],
        "values": [float(c["total_sales"]) for c in cashier_objects],
    })

    # Also provide legacy chart vars for any direct template usage
    chart_labels       = json.dumps([c["name"]              for c in cashier_objects])
    chart_data         = json.dumps([float(c["total_sales"]) for c in cashier_objects])
    payment_chart_data = json.dumps([float(cash_total), float(card_total), float(upi_total)])

    # Export CSV
    if request.GET.get("export") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="cashier_analytics.csv"'
        writer = csv.writer(response)
        writer.writerow(["Cashier", "Invoices", "Total Sales", "Avg Sale", "Cash", "Card", "UPI", "Discounts"])
        for c in cashier_objects:
            writer.writerow([
                c["username"], c["transaction_count"],
                round(float(c["total_sales"]),      2),
                round(float(c["avg_transaction"]),  2),
                round(float(raw_data[cashier_objects.index(c)]["cash_sales"]), 2) if cashier_objects.index(c) < len(raw_data) else 0,
                round(float(raw_data[cashier_objects.index(c)]["card_sales"]), 2) if cashier_objects.index(c) < len(raw_data) else 0,
                round(float(raw_data[cashier_objects.index(c)]["upi_sales"]),  2) if cashier_objects.index(c) < len(raw_data) else 0,
                round(float(c["discounts_given"]),  2),
            ])
        return response

    return render(request, "reports/cashier_analytics.html", {
        # Template-expected keys
        "cashiers":           cashier_objects,
        "grand_total_sales":  grand_total,
        "top_cashier_name":   top_cashier_name,
        "avg_per_cashier":    avg_per_cashier,
        "cashier_chart_data": cashier_chart_data,
        # Legacy / extra keys
        "data":               raw_data,
        "date_from":          date_from_str,
        "date_to":            date_to_str,
        "grand_total":        grand_total,
        "grand_count":        grand_count,
        "grand_avg":          grand_avg,
        "grand_vat":          grand_vat,
        "chart_labels":       chart_labels,
        "chart_data":         chart_data,
        "payment_chart_data": payment_chart_data,
        "cash_total":         cash_total,
        "card_total":         card_total,
        "upi_total":          upi_total,
    })


# =====================================================
# EXPORT CSV
# =====================================================

@login_required
def export_csv(request):
    date_str = request.GET.get("date")
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else timezone.now().date()
    except ValueError:
        selected_date = timezone.now().date()

    invoices = Invoice.objects.filter(
        company=request.user.company,
        created__date=selected_date,
        is_hold=False,
    ).select_related("customer", "cashier")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="sales_{selected_date}.csv"'

    writer = csv.writer(response)
    writer.writerow(["Invoice Number", "Customer", "Cashier", "Payment", "Subtotal", "Discount", "VAT", "Total", "Date"])

    for i in invoices:
        writer.writerow([
            i.number,
            i.customer.name if i.customer else "Walk-in",
            i.cashier.username if i.cashier else "",
            i.payment_method,
            round(i.subtotal, 2),
            round(i.discount, 2),
            round(i.vat, 2),
            round(i.total, 2),
            i.created.strftime("%d/%m/%Y %H:%M"),
        ])

    return response


# =====================================================
# PDF INVOICE
# =====================================================

@login_required
def invoice_pdf(request, id):
    invoice = get_object_or_404(Invoice, id=id, company=request.user.company)
    return generate_invoice_pdf(invoice)


# =====================================================
# HELPER: CALCULATE CART TOTALS
# =====================================================

def calculate_cart(cart, company):
    subtotal = Decimal("0")
    items = []

    for pid, qty in cart.items():
        product = Product.objects.filter(id=int(pid), company=company).first()
        if not product:
            continue

        line = product.price * qty
        subtotal += line

        items.append({
            "product": product,
            "qty": qty,
            "subtotal": line,
        })

    vat   = subtotal * Decimal("0.05")
    grand = subtotal + vat

    return items, subtotal, vat, grand


# =====================================================
# OFFLINE SYNC ENDPOINT
# =====================================================

@login_required
def sync_offline_transactions(request):
    """
    Receives offline transactions from IndexedDB and saves them to the DB.
    Returns count of synced records.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json as _json
    from decimal import Decimal as _Dec

    try:
        data = _json.loads(request.body)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    transactions = data.get('transactions', [])
    company = request.user.company
    synced = 0

    for tx in transactions:
        try:
            # Skip already synced
            if tx.get('db_id'):
                synced += 1
                continue

            # Build invoice from offline tx
            items_data = tx.get('items', [])
            if not items_data:
                continue

            subtotal = _Dec(str(tx.get('subtotal', 0)))
            vat_amt  = _Dec(str(tx.get('vat', 0)))
            total    = _Dec(str(tx.get('total', 0)))

            inv = Invoice.objects.create(
                company=company,
                created_by=request.user,
                subtotal=subtotal,
                vat=vat_amt,
                total=total,
                payment_method=tx.get('payment_method', 'cash'),
                status='paid',
                notes='[Offline Sync]',
            )

            for item in items_data:
                product = Product.objects.filter(
                    id=item.get('product_id'),
                    company=company
                ).first()
                if product:
                    InvoiceItem.objects.create(
                        invoice=inv,
                        product=product,
                        quantity=item.get('qty', 1),
                        price=_Dec(str(item.get('price', 0))),
                        subtotal=_Dec(str(item.get('subtotal', 0))),
                    )
                    # Deduct inventory
                    qty = int(item.get('qty', 1))
                    if product.stock >= qty:
                        product.stock -= qty
                        product.save(update_fields=['stock'])

            synced += 1

        except Exception as e:
            print(f'[SyncOffline] Error syncing tx: {e}')
            continue

    return JsonResponse({'synced': synced, 'status': 'ok'})
