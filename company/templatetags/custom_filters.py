from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()


@register.filter(name='split')
def split(value, sep=','):
    """Split a string by separator. Usage: {{ value|split:',' }}"""
    if not value:
        return []
    return str(value).split(str(sep))


@register.filter(name='zip_lists')
def zip_lists(a, b):
    """Zip two lists together."""
    return zip(a, b)


@register.filter(name='get_item')
def get_item(obj, key):
    """Get item from dict or list by key/index."""
    try:
        return obj[key]
    except (KeyError, IndexError, TypeError):
        return ''


@register.filter(name='multiply')
def multiply(value, arg):
    """Multiply value by arg."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter(name='divide')
def divide(value, arg):
    """Divide value by arg."""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter(name='percentage')
def percentage(value, total):
    """Calculate percentage: value/total * 100."""
    try:
        return round(float(value) / float(total) * 100, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter(name='currency')
def currency(value, symbol='AED'):
    """Format as currency."""
    try:
        return f"{symbol} {float(value):,.2f}"
    except (ValueError, TypeError):
        return f"{symbol} 0.00"


@register.filter(name='abs_value')
def abs_value(value):
    """Return absolute value."""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return 0


@register.filter(name='add_class')
def add_class(field, css_class):
    """Add CSS class to form field widget."""
    try:
        return field.as_widget(attrs={'class': css_class})
    except Exception:
        return field


@register.filter(name='jsonify')
def jsonify(value):
    """Convert Python object to JSON string (safe for use in JS)."""
    try:
        return mark_safe(json.dumps(value))
    except (TypeError, ValueError):
        return mark_safe('{}')


@register.filter(name='status_badge')
def status_badge(value):
    """Return HTML badge for a status string."""
    colors = {
        'paid': 'success',
        'unpaid': 'danger',
        'partial': 'warning',
        'refunded': 'info',
        'active': 'success',
        'inactive': 'danger',
        'pending': 'warning',
        'completed': 'success',
        'cancelled': 'danger',
    }
    color = colors.get(str(value).lower(), 'secondary')
    return mark_safe(f'<span class="badge badge-{color}">{value}</span>')


@register.filter(name='intcomma')
def intcomma(value):
    """Format integer with commas."""
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return value


@register.filter(name='truncate_middle')
def truncate_middle(value, length=20):
    """Truncate string in the middle."""
    s = str(value)
    if len(s) <= length:
        return s
    half = (length - 3) // 2
    return s[:half] + '...' + s[-half:]


@register.simple_tag
def vat_amount(subtotal, rate=5):
    """Calculate VAT amount."""
    try:
        return round(float(subtotal) * float(rate) / 100, 2)
    except (ValueError, TypeError):
        return 0


@register.simple_tag
def include_if(condition, template_name):
    """Conditionally include a template."""
    if condition:
        from django.template.loader import render_to_string
        try:
            return mark_safe(render_to_string(template_name))
        except Exception:
            return ''
    return ''
