from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import ActivityLog


@login_required
def activity_log(request):
    company = getattr(request.user, 'company', None)
    if company:
        logs = ActivityLog.objects.filter(company=company).select_related('user')
    else:
        logs = ActivityLog.objects.none()

    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'activity/activity_log.html', {
        'page_obj': page_obj,
        'total_count': logs.count(),
    })
