from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseBadRequest

from accounts.decorators import owner_required

from .models import (
    Product,
    Category,
    Supplier,
    Purchase,
    StockHistory
)


# ======================================================
# PRODUCTS
# ======================================================

@owner_required
@login_required
def inventory(request):

    products = Product.objects.filter(
        company=request.user.company
    ).select_related("category").order_by("-created")

    return render(request, "inventory/inventory.html", {
        "products": products
    })


@owner_required
@login_required
def add_product(request):

    categories = Category.objects.filter(company=request.user.company)

    if request.method == "POST":

        image = request.FILES.get("image")

        product = Product.objects.create(
            company=request.user.company,
            name=request.POST["name"],
            price=request.POST["price"],
            stock=request.POST.get("stock", 0),
            category_id=request.POST.get("category") or None,
            barcode=request.POST.get("barcode") or None,
            image=image
        )

        stock_qty = int(request.POST.get("stock", 0))

        if stock_qty > 0:

            StockHistory.objects.create(
                company=request.user.company,
                product=product,
                user=request.user,
                action="IN",
                qty=stock_qty,
                note="Opening Stock"
            )

        return redirect("/inventory/")

    return render(request, "inventory/add_product.html", {
        "categories": categories
    })


@owner_required
@login_required
@transaction.atomic
def edit_product(request, id):

    product = get_object_or_404(
        Product,
        id=id,
        company=request.user.company
    )

    categories = Category.objects.filter(company=request.user.company)

    if request.method == "POST":

        name = request.POST.get("name")
        stock = int(request.POST.get("stock", 0))
        price = request.POST.get("price")
        barcode = request.POST.get("barcode") or None

        if not name or not price:
            return HttpResponseBadRequest("Invalid product data")

        product.name = name
        product.category_id = request.POST.get("category") or None
        product.barcode = barcode
        product.stock = stock
        product.price = price

        image = request.FILES.get("image")
        if image:
            product.image = image

        product.save()

        return redirect("/inventory/")

    return render(request, "inventory/edit_product.html", {
        "product": product,
        "categories": categories
    })


@owner_required
@login_required
def delete_product(request, id):

    product = get_object_or_404(
        Product,
        id=id,
        company=request.user.company
    )

    product.delete()

    return redirect("/inventory/")


# ======================================================
# CATEGORY MANAGER
# ======================================================

@owner_required
@login_required
def category_list(request):

    categories = Category.objects.filter(
        company=request.user.company
    ).order_by("name")

    return render(request, "category/category_list.html", {
        "categories": categories
    })


@owner_required
@login_required
def add_category(request):

    if request.method == "POST":

        name = request.POST.get("name", "").strip()

        if name:
            Category.objects.create(
                company=request.user.company,
                name=name
            )

        return redirect("/inventory/categories/")

    return render(request, "category/category_add.html")


@owner_required
@login_required
def edit_category(request, id):

    category = get_object_or_404(
        Category,
        id=id,
        company=request.user.company
    )

    if request.method == "POST":

        category.name = request.POST.get("name", "").strip()
        category.save()

        return redirect("/inventory/categories/")

    # ✅ FIXED: was "inventory/category_edit.html" — template is at category/category_edit.html
    return render(request, "category/category_edit.html", {
        "category": category
    })


@owner_required
@login_required
def delete_category(request, id):

    category = get_object_or_404(
        Category,
        id=id,
        company=request.user.company
    )

    category.delete()

    return redirect("/inventory/categories/")


# ======================================================
# SUPPLIERS
# ======================================================

@owner_required
@login_required
def suppliers(request):

    suppliers = Supplier.objects.filter(
        company=request.user.company
    ).order_by("-created")

    return render(request, "suppliers/supplier_list.html", {
        "suppliers": suppliers
    })


@owner_required
@login_required
def add_supplier(request):

    if request.method == "POST":

        Supplier.objects.create(
            company=request.user.company,
            name=request.POST.get("name"),
            phone=request.POST.get("phone"),
            email=request.POST.get("email"),
            address=request.POST.get("address")
        )

        return redirect("/inventory/suppliers/")

    return render(request, "suppliers/supplier_add.html")


@owner_required
@login_required
def edit_supplier(request, id):

    supplier = get_object_or_404(
        Supplier,
        id=id,
        company=request.user.company
    )

    if request.method == "POST":

        supplier.name = request.POST.get("name")
        supplier.phone = request.POST.get("phone")
        supplier.email = request.POST.get("email")
        supplier.address = request.POST.get("address")
        supplier.save()

        return redirect("/inventory/suppliers/")

    return render(request, "suppliers/edit_supplier.html", {
        "supplier": supplier
    })


@owner_required
@login_required
def delete_supplier(request, id):

    supplier = get_object_or_404(
        Supplier,
        id=id,
        company=request.user.company
    )

    supplier.delete()

    return redirect("/inventory/suppliers/")


# ======================================================
# PURCHASE / STOCK IN
# ======================================================

@owner_required
@login_required
@transaction.atomic
def add_purchase(request):

    suppliers = Supplier.objects.filter(company=request.user.company)
    products = Product.objects.filter(company=request.user.company)

    if request.method == "POST":

        supplier_id = request.POST.get("supplier")

        if not supplier_id:
            return HttpResponseBadRequest("Supplier required.")

        supplier = get_object_or_404(
            Supplier,
            id=supplier_id,
            company=request.user.company
        )

        for pid in request.POST.getlist("product"):

            product = get_object_or_404(
                Product,
                id=pid,
                company=request.user.company
            )

            qty = int(request.POST.get(f"qty_{pid}", 0))
            cost_price = request.POST.get(f"cost_{pid}", 0)

            if qty <= 0:
                continue

            # UPDATE PRODUCT STOCK
            product.stock += qty
            product.save()

            # RECORD PURCHASE ENTRY
            Purchase.objects.create(
                company=request.user.company,
                supplier=supplier,
                product=product,
                qty=qty,
                cost_price=cost_price or 0
            )

            # RECORD STOCK HISTORY
            StockHistory.objects.create(
                company=request.user.company,
                product=product,
                user=request.user,
                action="IN",
                qty=qty,
                note="Purchase Stock In"
            )

        return redirect("/inventory/purchases/")

    return render(request, "purchases/purchase_add.html", {
        "suppliers": suppliers,
        "products": products
    })


@owner_required
@login_required
def purchases(request):

    purchases = Purchase.objects.filter(
        company=request.user.company
    ).order_by("-created")

    return render(request, "purchases/purchase_list.html", {
        "purchases": purchases
    })


# ======================================================
# STOCK HISTORY
# ======================================================

@owner_required
@login_required
def stock_history(request):

    history = StockHistory.objects.filter(
        company=request.user.company
    ).select_related("product", "user").order_by("-created")

    return render(request, "stock/stock_history.html", {
        "history": history
    })


# ==========================================
# EDIT PURCHASE
# ==========================================

@login_required
def edit_purchase(request, id):
    company = request.user.company
    purchase = Purchase.objects.get(id=id, company=company)

    if request.method == "POST":
        supplier_id = request.POST.get("supplier")
        product_id = request.POST.get("product")
        purchase.supplier_id = supplier_id if supplier_id else None
        purchase.product_id = product_id if product_id else None
        purchase.qty = int(request.POST.get("qty", 0))
        purchase.cost_price = request.POST.get("cost_price", 0)
        purchase.save()
        messages.success(request, "Purchase updated.")
        return redirect("/inventory/purchases/")

    suppliers = Supplier.objects.filter(company=company)
    products = Product.objects.filter(company=company)
    return render(request, "purchases/purchase_edit.html", {
        "purchase": purchase, "suppliers": suppliers, "products": products
    })


# ==========================================
# DELETE PURCHASE
# ==========================================

@login_required
def delete_purchase(request, id):
    company = request.user.company
    purchase = Purchase.objects.get(id=id, company=company)
    purchase.delete()
    messages.success(request, "Purchase deleted.")
    return redirect("/inventory/purchases/")


# ==========================================
# EXPORT PRODUCTS CSV
# ==========================================

@login_required
def export_products_csv(request):
    import csv
    from django.http import HttpResponse

    company = request.user.company
    products = Product.objects.filter(company=company)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="products.csv"'

    writer = csv.writer(response)
    writer.writerow(["Name", "Category", "Barcode", "Price", "Stock", "Low Stock"])
    for p in products:
        writer.writerow([p.name, p.category.name if p.category else "", p.barcode or "", p.price, p.stock, p.low_stock])

    return response
