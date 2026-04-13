from django.shortcuts import render, redirect
from .models import Expense
from django.contrib.auth.decorators import login_required
from accounts.decorators import owner_required
from django.utils import timezone


@owner_required
@login_required
def expenses(request):

    company = request.user.company

    if request.method == "POST":

        title = request.POST.get("title")
        amount = request.POST.get("amount")
        date = request.POST.get("date")

        if not date:
            date = timezone.now().date()

        Expense.objects.create(
            company=company,
            title=title,
            amount=amount,
            date=date
        )

        return redirect("/expenses/")

    data = Expense.objects.filter(company=company).order_by("-date")

    return render(request, "expenses/expenses.html", {
        "expenses": data
    })

# ==========================================
# EXPORT EXPENSES CSV
# ==========================================

@login_required
def export_expenses_csv(request):
    import csv
    from django.http import HttpResponse

    company = request.user.company
    expenses = Expense.objects.filter(company=company)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="expenses.csv"'

    writer = csv.writer(response)
    writer.writerow(["Title", "Amount", "Date"])
    for e in expenses:
        writer.writerow([e.title, e.amount, e.date])

    return response
