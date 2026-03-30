def is_owner(user):
    return user.role == "OWNER"


def is_manager(user):
    return user.role == "MANAGER"


def is_cashier(user):
    return user.role == "CASHIER"