def user_role(request):
    if request.user.is_authenticated:
        user = request.user
        role = get_user_role(user)
        return {'role': role}
    return {}

def get_user_role(user):
    if user.is_superuser:
        return 'админа'
    elif hasattr(user, 'seller'):
        return 'продавца'
    elif hasattr(user, 'master'):
        return 'мастера'
    elif hasattr(user, 'client'):
        return 'клиента'
    return None