import secrets
import hashlib
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction

from .models import User
from company.models import Company, Branch


# =====================================================
# LOGIN
# =====================================================

def login_view(request):

    # Already logged in → go to dashboard
    if request.user.is_authenticated:
        return redirect("/dashboard/")

    error = None

    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        next_url = request.POST.get("next", "").strip()

        if not username or not password:
            return render(request, "auth/login.html", {
                "error": "Please enter your username and password.",
                "next": next_url
            })

        user = authenticate(request, username=username, password=password)

        if not user:
            return render(request, "auth/login.html", {
                "error": "Invalid username or password.",
                "next": next_url
            })

        if not user.company:
            if user.is_superuser or user.is_staff:
                login(request, user)
                return redirect("/dashboard/")
            return render(request, "auth/login.html", {
                "error": "Account is not linked to a company. Contact support.",
                "next": next_url
            })

        if not user.company.active:
            return render(request, "auth/login.html", {
                "error": "Your company account is disabled. Contact support.",
                "next": next_url
            })

        login(request, user)

        # Respect the ?next= parameter (safe redirect only)
        if next_url and next_url.startswith("/") and not next_url.startswith("//"):
            return redirect(next_url)

        # Role-based default redirect
        if user.role == "CASHIER":
            return redirect("/pos/")
        return redirect("/dashboard/")

    # Pass ?next= from GET into the template so the form can carry it forward
    next_url = request.GET.get("next", "")
    return render(request, "auth/login.html", {"error": error, "next": next_url})


# =====================================================
# CASHIER LOGIN
# =====================================================

def cashier_login(request):

    if request.user.is_authenticated:
        return redirect("/pos/")

    error = None

    if request.method == "POST":

        next_url = request.POST.get("next", "").strip()

        user = authenticate(
            request,
            username=request.POST.get("username", "").strip(),
            password=request.POST.get("password", "")
        )

        if not user or user.role != "CASHIER":
            return render(request, "auth/cashier_login.html", {
                "error": "Invalid cashier credentials.",
                "next": next_url
            })

        login(request, user)

        if next_url and next_url.startswith("/") and not next_url.startswith("//"):
            return redirect(next_url)

        return redirect("/pos/")

    next_url = request.GET.get("next", "")
    return render(request, "auth/cashier_login.html", {"error": error, "next": next_url})


# =====================================================
# REGISTER (CREATE COMPANY + OWNER)
# =====================================================

def register_view(request):

    if request.user.is_authenticated:
        return redirect("/dashboard/")

    error = None

    if request.method == "POST":

        # ── Personal Info ──────────────────────────────
        first_name   = request.POST.get("first_name", "").strip()
        last_name    = request.POST.get("last_name", "").strip()
        email        = request.POST.get("email", "").strip()
        username     = request.POST.get("username", "").strip()
        password1    = request.POST.get("password1", "")
        password2    = request.POST.get("password2", "")

        # ── Company Info ───────────────────────────────
        company_name = request.POST.get("company_name", "").strip()
        phone        = request.POST.get("phone", "").strip()
        country      = request.POST.get("country", "").strip()
        address      = request.POST.get("address", "").strip()
        currency     = request.POST.get("currency", "AED").strip()
        trn          = request.POST.get("trn", "").strip()

        # ── Validation ─────────────────────────────────
        if not all([first_name, email, username, password1, company_name]):
            error = "Please fill in all required fields."
            return render(request, "auth/register.html", {"error": error})

        if password1 != password2:
            error = "Passwords do not match."
            return render(request, "auth/register.html", {"error": error})

        if len(password1) < 8:
            error = "Password must be at least 8 characters."
            return render(request, "auth/register.html", {"error": error})

        try:
            with transaction.atomic():

                # Create Company
                company = Company.objects.create(
                    name=company_name,
                    phone=phone,
                    email=email,
                    country=country,
                    address=address,
                    currency=currency,
                    vat_number=trn,
                    active=True,
                    business_category=request.POST.get('business_category', 'general')
                )

                # Create Owner User
                user = User.objects.create_user(
                    username=username,
                    password=password1,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    role="OWNER",
                    company=company
                )

                # Create Default Branch
                Branch.objects.create(
                    company=company,
                    name="Main Branch"
                )

                login(request, user)
                return redirect("/dashboard/")

        except IntegrityError:
            error = "Username already taken. Please choose another."

    return render(request, "auth/register.html", {"error": error})


# =====================================================
# ADD CASHIER
# =====================================================

@login_required
def add_cashier(request):

    if request.user.role != "OWNER":
        return redirect("/dashboard/")

    company  = request.user.company
    branches = Branch.objects.filter(company=company)
    error    = None

    if request.method == "POST":

        username  = request.POST.get("username", "").strip()
        password  = request.POST.get("password", "")
        branch_id = request.POST.get("branch")

        if not username or not password or not branch_id:
            error = "All fields are required."
        else:
            try:
                User.objects.create_user(
                    username=username,
                    password=password,
                    role="CASHIER",
                    company=company,
                    branch_id=branch_id
                )
                return redirect("/add-cashier/")
            except IntegrityError:
                error = "Username already exists."

    return render(request, "employees/add_cashier.html", {
        "branches": branches,
        "error": error
    })


# =====================================================
# PROFILE
# =====================================================

@login_required
def profile(request):

    user = request.user

    if request.method == "POST":
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name  = request.POST.get("last_name", user.last_name)
        user.email      = request.POST.get("email", user.email)
        # Handle avatar upload - form uses name="avatar"
        if request.FILES.get("avatar"):
            # Try profile_photo field first, then avatar field
            try:
                user.profile_photo = request.FILES["avatar"]
            except Exception:
                try:
                    user.avatar = request.FILES["avatar"]
                except Exception:
                    pass
        user.save()
        from django.contrib import messages as _msgs
        _msgs.success(request, "Profile updated successfully.")

    return render(request, "settings/profile.html", {"user": user})


# =====================================================
# LOGOUT
# =====================================================



# =====================================================
# PROFILE PHOTO UPLOAD
# =====================================================

@login_required
def update_photo(request):
    """AJAX/form endpoint to update the user's profile photo."""
    if request.method == "POST" and request.FILES.get("photo"):
        request.user.profile_photo = request.FILES["photo"]
        request.user.save()
    return redirect("/profile/")


def logout_view(request):
    logout(request)
    return redirect("/login/")


# =====================================================
# FORGOT PASSWORD
# =====================================================

def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        if not email:
            return render(request, "auth/forgot_password.html", {"error": "Please enter your email address."})

        from .models import User
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return render(request, "auth/forgot_password.html", {
                "success": True,
                "message": "If an account with that email exists, a password reset link has been sent."
            })

        from django.utils import timezone as tz
        import datetime
        if user.reset_last_attempt:
            time_diff = tz.now() - user.reset_last_attempt
            if time_diff < datetime.timedelta(hours=1) and user.reset_attempts >= 5:
                return render(request, "auth/forgot_password.html", {
                    "error": "Too many reset attempts. Please try again later."
                })

        token = secrets.token_urlsafe(32)
        user.reset_token = hashlib.sha256(token.encode()).hexdigest()
        user.reset_token_expiry = tz.now() + datetime.timedelta(minutes=30)
        user.reset_attempts = (user.reset_attempts or 0) + 1
        user.reset_last_attempt = tz.now()
        user.save(update_fields=["reset_token", "reset_token_expiry", "reset_attempts", "reset_last_attempt"])

        reset_url = request.build_absolute_uri(f"/accounts/reset-password/?token={token}")

        try:
            send_mail(
                subject="Password Reset - Labezra POS",
                message=f"Click the link below to reset your password:\n\n{reset_url}\n\nThis link expires in 30 minutes.\nIf you did not request this, please ignore this email.",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@labezra.com"),
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"[EMAIL ERROR] {e}")
            print(f"[EMAIL DEBUG] Reset URL: {reset_url}")

        return render(request, "auth/forgot_password.html", {
            "success": True,
            "message": "If an account with that email exists, a password reset link has been sent."
        })

    return render(request, "auth/forgot_password.html")


def reset_password(request):
    token = request.GET.get("token") or request.POST.get("token", "")
    if not token:
        return render(request, "auth/reset_password.html", {"error": "Invalid or missing reset token.", "invalid": True})

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    from .models import User
    from django.utils import timezone as tz

    try:
        user = User.objects.get(reset_token=token_hash)
    except User.DoesNotExist:
        return render(request, "auth/reset_password.html", {"error": "Invalid or expired reset link.", "invalid": True})

    if user.reset_token_expiry and tz.now() > user.reset_token_expiry:
        user.reset_token = None
        user.reset_token_expiry = None
        user.save(update_fields=["reset_token", "reset_token_expiry"])
        return render(request, "auth/reset_password.html", {"error": "This reset link has expired. Please request a new one.", "invalid": True})

    if request.method == "POST":
        password = request.POST.get("password", "")
        confirm  = request.POST.get("confirm_password", "")

        if len(password) < 8:
            return render(request, "auth/reset_password.html", {"error": "Password must be at least 8 characters.", "token": token})
        if password != confirm:
            return render(request, "auth/reset_password.html", {"error": "Passwords do not match.", "token": token})

        user.set_password(password)
        user.reset_token = None
        user.reset_token_expiry = None
        user.reset_attempts = 0
        user.save()

        return render(request, "auth/reset_password.html", {"success": True})

    return render(request, "auth/reset_password.html", {"token": token})


# =====================================================
# CHANGE PASSWORD
# =====================================================

@login_required
def change_password(request):
    error = None
    success = None

    if request.method == "POST":
        current = request.POST.get("current_password", "")
        new1 = request.POST.get("new_password", "")
        new2 = request.POST.get("confirm_password", "")

        if not request.user.check_password(current):
            error = "Current password is incorrect."
        elif new1 != new2:
            error = "New passwords do not match."
        elif len(new1) < 8:
            error = "Password must be at least 8 characters."
        else:
            request.user.set_password(new1)
            request.user.save()
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            success = "Password changed successfully."

    return render(request, "settings/change_password.html", {"error": error, "success": success})
