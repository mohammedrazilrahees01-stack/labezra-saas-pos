from django.shortcuts import render, redirect, get_object_or_404
from .models import Employee
from django.contrib.auth.decorators import login_required
from accounts.decorators import owner_required


# =========================
# LIST EMPLOYEES
# =========================

@owner_required
@login_required
def employees(request):
    data = Employee.objects.filter(company=request.user.company)
    return render(request, "employees/employees.html", {"employees": data})


# =========================
# ADD EMPLOYEE
# =========================

@owner_required
@login_required
def add_employee(request):

    if request.method == "POST":
        Employee.objects.create(
            company=request.user.company,
            name=request.POST.get("name"),
            salary=request.POST.get("salary"),
        )

        return redirect("/employees/")

    return render(request, "employees/employee_add.html")


# =========================
# EDIT EMPLOYEE
# =========================

@owner_required
@login_required
def edit_employee(request, id):

    employee = get_object_or_404(Employee, id=id, company=request.user.company)

    if request.method == "POST":
        employee.name = request.POST.get("name")
        employee.salary = request.POST.get("salary")
        employee.save()

        return redirect("/employees/")

    return render(request, "employees/employee_edit.html", {"employee": employee})


# =========================
# DELETE EMPLOYEE
# =========================

@owner_required
@login_required
def delete_employee(request, id):

    employee = get_object_or_404(Employee, id=id, company=request.user.company)
    employee.delete()

    return redirect("/employees/")

# ==========================================
# EXPORT EMPLOYEES CSV
# ==========================================

@login_required
def export_employees_csv(request):
    import csv
    from django.http import HttpResponse

    company = request.user.company
    from .models import Employee
    employees = Employee.objects.filter(company=company)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="employees.csv"'

    writer = csv.writer(response)
    writer.writerow(["Name", "Position", "Salary"])
    for e in employees:
        writer.writerow([e.name, e.position, e.salary])

    return response
