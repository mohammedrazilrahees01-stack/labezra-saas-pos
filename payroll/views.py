from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from employees.models import Employee
from accounts.decorators import owner_required


# ======================================================
# PAYROLL DASHBOARD
# ======================================================

@owner_required
@login_required
def payroll(request):

    employees = Employee.objects.filter(
        company=request.user.company
    )

    return render(request, "payroll/payroll.html", {
        "employees": employees
    })


# ======================================================
# RUN PAYROLL
# ======================================================

@owner_required
@login_required
def run_payroll(request):

    employees = Employee.objects.filter(
        company=request.user.company
    )

    return render(request, "payroll/payroll_run.html", {
        "employees": employees
    })