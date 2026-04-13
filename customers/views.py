from django.shortcuts import render, redirect, get_object_or_404
from .models import Customer
from django.contrib.auth.decorators import login_required
from accounts.decorators import owner_required


@owner_required
@login_required
def customers(request):
    data = Customer.objects.filter(company=request.user.company)
    return render(request, 'customers/customers.html', {'customers': data})


# ============================
# ADD CUSTOMER
# ============================

@owner_required
@login_required
def add_customer(request):

    if request.method == "POST":
        Customer.objects.create(
            company=request.user.company,
            name=request.POST.get("name"),
            phone=request.POST.get("phone"),
            email=request.POST.get("email"),
            trn=request.POST.get("trn"),
        )

        return redirect("/customers/")

    return render(request, "customers/customer_add.html")


# ============================
# EDIT CUSTOMER
# ============================

@owner_required
@login_required
def edit_customer(request, id):

    customer = get_object_or_404(Customer, id=id, company=request.user.company)

    if request.method == "POST":
        customer.name = request.POST.get("name")
        customer.phone = request.POST.get("phone")
        customer.email = request.POST.get("email")
        customer.trn = request.POST.get("trn")
        customer.save()

        return redirect("/customers/")

    return render(request, "customers/customer_edit.html", {"customer": customer})


# ============================
# DELETE CUSTOMER
# ============================

@owner_required
@login_required
def delete_customer(request, id):

    customer = get_object_or_404(Customer, id=id, company=request.user.company)
    customer.delete()

    return redirect("/customers/")

# ==========================================
# EXPORT CUSTOMERS CSV
# ==========================================

@login_required
def export_customers_csv(request):
    import csv
    from django.http import HttpResponse

    company = request.user.company
    customers = Customer.objects.filter(company=company)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="customers.csv"'

    writer = csv.writer(response)
    writer.writerow(["Name", "Phone", "Email", "TRN"])
    for c in customers:
        writer.writerow([c.name, c.phone, c.email, c.trn])

    return response
