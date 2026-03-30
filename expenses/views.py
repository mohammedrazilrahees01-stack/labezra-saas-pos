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