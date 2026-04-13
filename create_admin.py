import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import User
from company.models import Company, Branch

username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@labezra.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Admin@12345')

# Create default company if not exists
company, created = Company.objects.get_or_create(
    name="Labezra Demo",
    defaults={
        "country": "UAE",
        "currency": "AED",
        "active": True,
        "is_demo": True,
        "subscription_active": True,
        "business_category": "general",
    }
)
if created:
    print(f"✅ Company 'Labezra Demo' created")
else:
    print(f"ℹ️  Company 'Labezra Demo' already exists")

# Create default branch if not exists
branch, created = Branch.objects.get_or_create(
    company=company,
    name="Main Branch",
    defaults={
        "location": "Dubai, UAE",
        "is_active": True,
    }
)
if created:
    print(f"✅ Branch 'Main Branch' created")

# Create or update superuser
if not User.objects.filter(username=username).exists():
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password,
    )
    user.company = company
    user.branch = branch
    user.role = "OWNER"
    user.save()
    print(f"✅ Superuser '{username}' created with company")
else:
    user = User.objects.get(username=username)
    user.set_password(password)
    if not user.company:
        user.company = company
        user.branch = branch
        user.role = "OWNER"
    user.save()
    print(f"✅ Superuser '{username}' updated with company")
