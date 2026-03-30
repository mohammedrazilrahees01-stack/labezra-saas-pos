"""
Run this from your project root (C:\labezra-pos-saas):
    python fix_migrations_local.py

It will:
1. Delete ALL migration files (except __init__.py) from every app
2. Print instructions to finish the setup
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
deleted = []

for root, dirs, files in os.walk(BASE):
    # Skip venv
    if 'venv' in root or '.git' in root:
        continue
    if os.path.basename(root) == 'migrations':
        for f in files:
            if f.endswith('.py') and f != '__init__.py':
                path = os.path.join(root, f)
                os.remove(path)
                deleted.append(path.replace(BASE, ''))

if deleted:
    print(f"✅ Deleted {len(deleted)} old migration files:")
    for p in deleted:
        print(f"   {p}")
else:
    print("No migration files found to delete.")

print("\n✅ Done! Now run:")
print("   python manage.py makemigrations")
print("   python manage.py migrate")
print("   python manage.py createsuperuser")
