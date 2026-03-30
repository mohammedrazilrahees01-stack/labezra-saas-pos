from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from django.http import HttpResponse


def generate_invoice_pdf(invoice):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="Invoice-{invoice.number}.pdf"'
    )

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    currency = getattr(invoice.company, "currency", "AED")

    # ── Header Bar ──────────────────────────────────────────────────
    p.setFillColorRGB(0.15, 0.23, 0.42)   # dark navy
    p.rect(0, height - 80, width, 80, fill=1, stroke=0)

    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 18)
    p.drawString(40, height - 35, invoice.company.name)

    p.setFont("Helvetica", 10)
    p.drawString(40, height - 55, "TAX INVOICE")

    # Invoice number / date (right aligned)
    p.setFont("Helvetica-Bold", 11)
    p.drawRightString(width - 40, height - 30, f"Invoice # {invoice.number}")
    p.setFont("Helvetica", 10)
    p.drawRightString(
        width - 40,
        height - 48,
        f"Date: {invoice.created.strftime('%d %b %Y  %H:%M')}",
    )
    p.drawRightString(
        width - 40,
        height - 64,
        f"Payment: {invoice.payment_method}",
    )

    # ── Customer Block ───────────────────────────────────────────────
    y = height - 110
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(40, y, "BILLED TO")

    p.setFont("Helvetica", 10)
    if invoice.customer:
        p.drawString(40, y - 15, invoice.customer.name)
        if invoice.customer.phone:
            p.drawString(40, y - 28, invoice.customer.phone)
        if invoice.customer.trn:
            p.drawString(40, y - 41, f"TRN: {invoice.customer.trn}")
    else:
        p.drawString(40, y - 15, "Walk-in Customer")

    # Cashier info (right side)
    p.setFont("Helvetica-Bold", 10)
    p.drawRightString(width - 40, y, "CASHIER")
    p.setFont("Helvetica", 10)
    cashier_name = (
        invoice.cashier.get_full_name() or invoice.cashier.username
        if invoice.cashier
        else "—"
    )
    p.drawRightString(width - 40, y - 15, cashier_name)

    # ── Items Table Header ───────────────────────────────────────────
    y -= 70
    p.setFillColorRGB(0.24, 0.39, 0.93)   # blue header
    p.rect(40, y - 4, width - 80, 22, fill=1, stroke=0)

    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50,  y + 4, "Item")
    p.drawString(330, y + 4, "Qty")
    p.drawString(390, y + 4, "Unit Price")
    p.drawRightString(width - 40, y + 4, "Total")

    # ── Items Rows ───────────────────────────────────────────────────
    y -= 22
    p.setFillColor(colors.black)
    row_color_a = colors.HexColor("#F8FAFC")
    row_color_b = colors.white

    for idx, item in enumerate(invoice.items.all()):
        # Alternating row background
        bg = row_color_a if idx % 2 == 0 else row_color_b
        p.setFillColor(bg)
        p.rect(40, y - 4, width - 80, 20, fill=1, stroke=0)

        p.setFillColor(colors.black)
        p.setFont("Helvetica", 10)

        # FIX: use item.name and item.quantity (not product_name / qty)
        p.drawString(50,  y + 4, (item.name or "")[:40])
        p.drawString(330, y + 4, str(item.quantity))
        p.drawString(390, y + 4, f"{currency} {item.price:.2f}")
        p.drawRightString(width - 40, y + 4, f"{currency} {item.total:.2f}")

        y -= 22

        # New page guard
        if y < 120:
            p.showPage()
            y = height - 60

    # ── Totals Block ─────────────────────────────────────────────────
    y -= 10
    p.line(40, y, width - 40, y)
    y -= 18

    def summary_line(label, value, bold=False):
        nonlocal y
        font = "Helvetica-Bold" if bold else "Helvetica"
        p.setFont(font, 10)
        p.drawRightString(width - 130, y, label)
        p.drawRightString(width - 40,  y, value)
        y -= 18

    summary_line("Subtotal:",         f"{currency} {invoice.subtotal:.2f}")
    summary_line("Discount:",         f"- {currency} {invoice.discount:.2f}")
    summary_line("VAT (5%):",         f"{currency} {invoice.vat:.2f}")

    # Grand total highlight
    p.setFillColorRGB(0.15, 0.23, 0.42)
    p.rect(width - 200, y - 6, 160, 22, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 11)
    p.drawRightString(width - 46, y + 4, f"TOTAL  {currency} {invoice.total:.2f}")

    # ── Footer ───────────────────────────────────────────────────────
    p.setFillColor(colors.HexColor("#64748B"))
    p.setFont("Helvetica", 8)
    p.drawCentredString(width / 2, 30, "Thank you for your business!")

    p.showPage()
    p.save()

    return response
