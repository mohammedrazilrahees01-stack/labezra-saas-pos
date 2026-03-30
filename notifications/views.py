from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone

from .models import Notification
from accounts.models import User


# ───────────────────────────────────────────────
# USER-FACING: inbox
# ───────────────────────────────────────────────

@login_required
def inbox(request):
    """Full notifications inbox for the current user."""
    notifs_qs = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifs_qs.filter(read=False).count()
    notifs = notifs_qs[:100]

    # Auto-mark as read when inbox is opened
    Notification.objects.filter(user=request.user, read=False).update(read=True)

    return render(request, 'notifications/inbox.html', {
        'notifications': notifs,
        'unread_count': unread_count,
    })


# ───────────────────────────────────────────────
# AJAX: mark read
# ───────────────────────────────────────────────

@login_required
@require_POST
def mark_read(request, pk):
    try:
        n = Notification.objects.get(pk=pk, user=request.user)
        n.read = True
        n.save()
        return JsonResponse({"ok": True})
    except Notification.DoesNotExist:
        return JsonResponse({"ok": False}, status=404)


@login_required
@require_POST
def mark_all_read(request):
    Notification.objects.filter(user=request.user, read=False).update(read=True)
    return JsonResponse({"ok": True})


# ───────────────────────────────────────────────
# ADMIN: notification center (send messages to users)
# ───────────────────────────────────────────────

@login_required
def admin_notify(request):
    """
    Admin Notification Center — only accessible by OWNER or staff.
    Allows sending a notification to one user, all users in your company,
    or (superadmin) all users in all companies.
    """
    user = request.user

    if user.role not in ("OWNER",) and not user.is_staff:
        return redirect('/dashboard/')

    # Fetch recipients — owners see their company users; superadmin sees all
    if user.is_superuser or user.is_staff:
        recipients = User.objects.filter(is_active=True).order_by('company__name', 'username')
    else:
        recipients = User.objects.filter(company=user.company, is_active=True).order_by('username')

    # Fetch recent sent notifications (created by admin)
    recent_sent = Notification.objects.filter(
        title__icontains='[Admin]'
    ).order_by('-created_at')[:50] if user.is_staff else \
    Notification.objects.filter(
        user__company=user.company
    ).order_by('-created_at')[:30]

    if request.method == 'POST':
        title      = request.POST.get('title', '').strip()
        message    = request.POST.get('message', '').strip()
        notif_type = request.POST.get('type', 'info')
        link       = request.POST.get('link', '').strip()
        target     = request.POST.get('target', 'all')  # 'all' or specific user id

        if not title:
            messages.error(request, 'Title is required.')
            return redirect('/notifications/admin/')

        # Prefix with [Admin] so we can filter them in the sent list
        tagged_title = f'[Admin] {title}'

        if target == 'all':
            qs = recipients
        else:
            try:
                qs = User.objects.filter(pk=int(target))
            except (ValueError, User.DoesNotExist):
                qs = recipients

        count = 0
        for u in qs:
            Notification.objects.create(
                user=u,
                title=tagged_title,
                message=message,
                type=notif_type,
                link=link,
            )
            count += 1

        messages.success(request, f'Notification sent to {count} user(s) successfully.')
        return redirect('/notifications/admin/')

    return render(request, 'notifications/admin_notify.html', {
        'recipients': recipients,
        'recent_sent': recent_sent,
    })
