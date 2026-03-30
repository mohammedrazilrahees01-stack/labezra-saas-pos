from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone

from .models import BusinessInvoice, BusinessInvoiceItem
from customers.models import Customer
from accounts.decorators import owner_required

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas as rl_canvas


# ==========================================
# BUSINESS INVOICES LIST
# ==========================================

@owner_required
@login_required
def business_invoices(request):

    invoices = BusinessInvoice.objects.filter(
        company=request.user.company
    ).select_related('customer').prefetch_related('items')

    # Toggle paid / unpaid status
    if request.method == 'POST':

        invoice = get_object_or_404(
            BusinessInvoice,
            id=request.POST.get('invoice_id'),
            company=request.user.company
        )

        invoice.paid = not invoice.paid
        invoice.save()

        # FIX: was redirecting to '/business_invoices/' (wrong URL)
        return redirect(reverse('accounting:business_invoices'))

    return render(request, 'pos/business_invoices.html', {
        'invoices': invoices,
    })


# ==========================================
# CREATE BUSINESS INVOICE
# ==========================================

@owner_required
@login_required
def create_business_invoice(request):

    customers = Customer.objects.filter(company=request.user.company)

    if request.method == 'POST':

        customer = get_object_or_404(
            Customer,
            id=request.POST.get('customer'),
            company=request.user.company
        )

        due_date_raw = request.POST.get('due_date')
        due_date = due_date_raw if due_date_raw else None

        # Create invoice shell first
        invoice = BusinessInvoice.objects.create(
            company=request.user.company,
            customer=customer,
            subtotal=Decimal('0.00'),
            vat=Decimal('0.00'),
            total=Decimal('0.00'),
            due_date=due_date,
            notes=request.POST.get('notes', ''),
        )

        subtotal = Decimal('0.00')

        # FIX: template posts item_name[], qty[], price[] lists
        names  = request.POST.getlist('item_name')
        qtys   = request.POST.getlist('qty')
        prices = request.POST.getlist('price')

        for idx in range(len(names)):

            name  = names[idx].strip()
            if not name:
                continue  # skip blank rows

            try:
                qty   = Decimal(str(qtys[idx]  or '0'))
                price = Decimal(str(prices[idx] or '0'))
            except Exception:
                qty, price = Decimal('0'), Decimal('0')

            line_total = qty * price
            subtotal  += line_total

            BusinessInvoiceItem.objects.create(
                invoice=invoice,
                item_name=name,
                qty=qty,
                price=price,
            )

        # Determine VAT rate (UAE = 5%, Saudi = 15%)
        vat_rate = Decimal('0.05')

        if hasattr(request.user.company, 'country') and request.user.company.country:
            country = request.user.company.country.lower()
            if 'saudi' in country or 'ksa' in country:
                vat_rate = Decimal('0.15')

        vat   = (subtotal * vat_rate).quantize(Decimal('0.01'))
        total = (subtotal + vat).quantize(Decimal('0.01'))

        invoice.subtotal = subtotal.quantize(Decimal('0.01'))
        invoice.vat      = vat
        invoice.total    = total
        invoice.save()

        return redirect(reverse('accounting:business_invoices'))

    return render(request, 'pos/create_business_invoice.html', {
        'customers': customers,
    })


# ==========================================
# INVOICE PDF EXPORT  (government-grade)
# ==========================================

@owner_required
@login_required
def invoice_pdf(request, id):

    invoice = get_object_or_404(
        BusinessInvoice,
        id=id,
        company=request.user.company
    )

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="BusinessInvoice-{invoice.id}.pdf"'
    )

    p = rl_canvas.Canvas(response, pagesize=A4)
    width, height = A4

    company  = invoice.company
    currency = getattr(company, 'currency', 'AED')

    # ── Header bar ──────────────────────────────────────────────────
    p.setFillColorRGB(0.12, 0.23, 0.37)
    p.rect(0, height - 90, width, 90, fill=1, stroke=0)

    p.setFillColor(colors.white)
    p.setFont('Helvetica-Bold', 18)
    p.drawString(40, height - 38, company.name)

    p.setFont('Helvetica', 10)
    p.drawString(40, height - 56, 'TAX INVOICE / فاتورة ضريبية')

    if getattr(company, 'vat_number', None):
        p.drawString(40, height - 72, f"TRN: {company.vat_number}")

    p.setFont('Helvetica-Bold', 11)
    p.drawRightString(width - 40, height - 32, f"Invoice # {invoice.id}")
    p.setFont('Helvetica', 10)
    p.drawRightString(width - 40, height - 48, f"Date: {invoice.created.strftime('%d %b %Y')}")
    p.drawRightString(width - 40, height - 64, f"Due: {invoice.due_date or 'N/A'}")
    status = 'PAID' if invoice.paid else 'UNPAID'
    p.drawRightString(width - 40, height - 80, f"Status: {status}")

    # ── Customer block ───────────────────────────────────────────────
    y = height - 120
    p.setFillColor(colors.black)
    p.setFont('Helvetica-Bold', 10)
    p.drawString(40, y, 'BILL TO')
    p.setFont('Helvetica', 10)
    p.drawString(40, y - 16, invoice.customer.name)
    if invoice.customer.phone:
        p.drawString(40, y - 30, invoice.customer.phone)
    if invoice.customer.email:
        p.drawString(40, y - 44, invoice.customer.email)
    if getattr(invoice.customer, 'trn', None):
        p.drawString(40, y - 58, f"TRN: {invoice.customer.trn}")

    # ── Table header ─────────────────────────────────────────────────
    y -= 85
    p.setFillColorRGB(0.15, 0.35, 0.75)
    p.rect(40, y - 4, width - 80, 22, fill=1, stroke=0)

    p.setFillColor(colors.white)
    p.setFont('Helvetica-Bold', 10)
    p.drawString(50,       y + 4, 'Description')
    p.drawString(330,      y + 4, 'Qty')
    p.drawString(395,      y + 4, 'Unit Price')
    p.drawRightString(width - 40, y + 4, 'Total')

    # ── Items ────────────────────────────────────────────────────────
    y -= 22
    row_a = colors.HexColor('#F8FAFC')
    row_b = colors.white

    for idx, item in enumerate(invoice.items.all()):
        bg = row_a if idx % 2 == 0 else row_b
        p.setFillColor(bg)
        p.rect(40, y - 4, width - 80, 20, fill=1, stroke=0)

        p.setFillColor(colors.black)
        p.setFont('Helvetica', 10)
        p.drawString(50,       y + 4, str(item.item_name)[:45])
        p.drawString(330,      y + 4, str(item.qty))
        p.drawString(395,      y + 4, f'{currency} {item.price:.2f}')
        p.drawRightString(width - 40, y + 4, f'{currency} {float(item.qty) * float(item.price):.2f}')

        y -= 22
        if y < 130:
            p.showPage()
            y = height - 60

    # ── Totals ───────────────────────────────────────────────────────
    y -= 10
    p.setStrokeColorRGB(0.8, 0.8, 0.8)
    p.line(40, y, width - 40, y)
    y -= 20

    def draw_total_line(label, value, bold=False):
        nonlocal y
        p.setFont('Helvetica-Bold' if bold else 'Helvetica', 10)
        p.setFillColor(colors.black)
        p.drawRightString(width - 140, y, label)
        p.drawRightString(width - 40,  y, value)
        y -= 18

    draw_total_line('Subtotal:', f'{currency} {invoice.subtotal:.2f}')
    draw_total_line('VAT (5%):', f'{currency} {invoice.vat:.2f}')

    # Grand total highlight
    p.setFillColorRGB(0.12, 0.23, 0.37)
    p.rect(width - 220, y - 6, 180, 24, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont('Helvetica-Bold', 11)
    p.drawRightString(width - 44, y + 5, f'TOTAL  {currency} {invoice.total:.2f}')

    # ── Footer ───────────────────────────────────────────────────────
    p.setFillColor(colors.HexColor('#64748B'))
    p.setFont('Helvetica', 8)
    p.drawCentredString(width / 2, 36, 'Thank you for your business  |  شكراً لتعاملكم معنا')
    p.drawCentredString(width / 2, 24, 'This is a computer-generated tax invoice')

    p.showPage()
    p.save()

    return response
