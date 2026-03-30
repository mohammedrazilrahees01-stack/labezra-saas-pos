"""
Company-level context processors.
Injects business_type and related module flags into every template.
"""


def business_type(request):
    """
    Inject the active company's business category into all templates.
    Used to conditionally show/hide modules in the sidebar.
    """
    if not request.user.is_authenticated:
        return {}

    company = getattr(request.user, 'company', None)
    if not company:
        return {}

    cat = getattr(company, 'business_category', 'general')

    # Define which modules each business type uses
    MODULE_MAP = {
        'restaurant': {
            'show_tables': True,
            'show_kitchen': True,
            'show_modifiers': True,
            'show_reservations': True,
            'show_tips': True,
            'show_pharmacy': False,
            'show_appointments': False,
            'show_weight': False,
            'show_serial': False,
            'show_batch': False,
        },
        'grocery': {
            'show_tables': False,
            'show_kitchen': False,
            'show_modifiers': False,
            'show_reservations': False,
            'show_tips': False,
            'show_pharmacy': False,
            'show_appointments': False,
            'show_weight': True,
            'show_serial': False,
            'show_batch': True,
        },
        'pharmacy': {
            'show_tables': False,
            'show_kitchen': False,
            'show_modifiers': False,
            'show_reservations': False,
            'show_tips': False,
            'show_pharmacy': True,
            'show_appointments': False,
            'show_weight': False,
            'show_serial': False,
            'show_batch': True,
        },
        'salon': {
            'show_tables': False,
            'show_kitchen': False,
            'show_modifiers': True,
            'show_reservations': True,
            'show_tips': True,
            'show_pharmacy': False,
            'show_appointments': True,
            'show_weight': False,
            'show_serial': False,
            'show_batch': False,
        },
        'electronics': {
            'show_tables': False,
            'show_kitchen': False,
            'show_modifiers': False,
            'show_reservations': False,
            'show_tips': False,
            'show_pharmacy': False,
            'show_appointments': False,
            'show_weight': False,
            'show_serial': True,
            'show_batch': False,
        },
    }

    defaults = {
        'show_tables': False,
        'show_kitchen': False,
        'show_modifiers': False,
        'show_reservations': False,
        'show_tips': False,
        'show_pharmacy': False,
        'show_appointments': False,
        'show_weight': False,
        'show_serial': False,
        'show_batch': False,
    }

    modules = MODULE_MAP.get(cat, defaults)

    return {
        'business_type': cat,
        'business_type_label': dict(company.BUSINESS_CATEGORY_CHOICES).get(cat, 'General'),
        'company_currency': getattr(company, 'currency', 'AED'),
        'company_vat': getattr(company, 'vat_number', ''),
        **modules,
    }
