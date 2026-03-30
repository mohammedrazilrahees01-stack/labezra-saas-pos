from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date

from .models import Project, Task, TimeEntry


@login_required
def project_list(request):
    company = request.user.company
    projects = Project.objects.filter(company=company)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        status = request.POST.get('status', 'active')
        start_date = request.POST.get('start_date') or None
        due_date = request.POST.get('due_date') or None
        budget = request.POST.get('budget', '0') or '0'

        if name:
            Project.objects.create(
                company=company,
                name=name,
                description=description,
                status=status,
                start_date=start_date,
                due_date=due_date,
                budget=budget,
                created_by=request.user,
            )
            messages.success(request, f'Project "{name}" created successfully!')
        else:
            messages.error(request, 'Project name is required.')
        return redirect('/projects/')

    return render(request, 'projects/list.html', {
        'projects': projects,
        'project_count': projects.count(),
        'active_count': projects.filter(status='active').count(),
    })


@login_required
def task_list(request):
    company = request.user.company
    tasks = Task.objects.filter(company=company)
    projects = Project.objects.filter(company=company)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        status = request.POST.get('status', 'todo')
        priority = request.POST.get('priority', 'medium')
        project_id = request.POST.get('project_id') or None
        due_date = request.POST.get('due_date') or None

        if title:
            project = None
            if project_id:
                try:
                    project = Project.objects.get(id=project_id, company=company)
                except Project.DoesNotExist:
                    pass

            Task.objects.create(
                company=company,
                project=project,
                title=title,
                description=description,
                status=status,
                priority=priority,
                due_date=due_date,
                created_by=request.user,
            )
            messages.success(request, f'Task "{title}" created successfully!')
        else:
            messages.error(request, 'Task title is required.')
        return redirect('/projects/tasks/')

    return render(request, 'projects/tasks.html', {
        'tasks': tasks,
        'projects': projects,
        'todo_count': tasks.filter(status='todo').count(),
        'in_progress_count': tasks.filter(status='in_progress').count(),
        'done_count': tasks.filter(status='done').count(),
    })


@login_required
def time_tracking(request):
    company = request.user.company
    entries = TimeEntry.objects.filter(company=company)
    projects = Project.objects.filter(company=company)

    if request.method == 'POST':
        description = request.POST.get('description', '').strip()
        hours = request.POST.get('hours', '').strip()
        entry_date = request.POST.get('date', '') or str(date.today())
        project_id = request.POST.get('project_id') or None

        if description and hours:
            project = None
            if project_id:
                try:
                    project = Project.objects.get(id=project_id, company=company)
                except Project.DoesNotExist:
                    pass

            TimeEntry.objects.create(
                company=company,
                project=project,
                user=request.user,
                description=description,
                hours=hours,
                date=entry_date,
            )
            messages.success(request, f'Time entry logged: {hours}h for "{description}"')
        else:
            messages.error(request, 'Description and hours are required.')
        return redirect('/projects/time-tracking/')

    total_hours = sum(e.hours for e in entries)
    return render(request, 'projects/time_tracking.html', {
        'entries': entries,
        'projects': projects,
        'total_hours': total_hours,
    })
