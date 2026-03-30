"""
Auto-alert system: call check_and_create_alerts() to generate
low-stock and expiry notifications. Call this from dashboard view
or a periodic task.
"""
from datetime import date, timedelta
from .models import Notification


def check_and_create_alerts(company, users):
    """
    Check inventory for low stock and upcoming expiry.
    Creates notifications for each issue found.
    users: queryset of Users to notify (e.g. owner + managers)
    """
    from inventory.models import Product

    products = Product.objects.filter(company=company)
    alerts_created = []

    for product in products:
        # Low stock alert
        if product.stock <= product.low_stock:
            title = f"⚠️ Low Stock: {product.name}"
            message = f"Only {product.stock} units left (threshold: {product.low_stock}). Restock soon."
            for user in users:
                # Avoid duplicate (only if not already notified today)
                already = Notification.objects.filter(
                    user=user,
                    title=title,
                    created_at__date=date.today()
                ).exists()
                if not already:
                    Notification.objects.create(
                        user=user,
                        title=title,
                        message=message,
                        type='warning',
                        link='/inventory/'
                    )
                    alerts_created.append(title)

        # Expiry date alert
        if product.expiry_date:
            days_left = (product.expiry_date - date.today()).days
            if days_left <= 30 and days_left >= 0:
                if days_left == 0:
                    title = f"🚨 EXPIRES TODAY: {product.name}"
                    ntype = 'error'
                elif days_left <= 7:
                    title = f"🔴 Expires in {days_left} days: {product.name}"
                    ntype = 'error'
                else:
                    title = f"🟡 Expiring soon ({days_left} days): {product.name}"
                    ntype = 'warning'
                message = f"Expires on {product.expiry_date.strftime('%d %b %Y')}. Take action."
                for user in users:
                    already = Notification.objects.filter(
                        user=user,
                        title__startswith=f"Expires" if days_left > 7 else f"Exp",
                        created_at__date=date.today()
                    ).exists()
                    if not already:
                        Notification.objects.create(
                            user=user,
                            title=title,
                            message=message,
                            type=ntype,
                            link='/inventory/'
                        )
                        alerts_created.append(title)

    return alerts_created
