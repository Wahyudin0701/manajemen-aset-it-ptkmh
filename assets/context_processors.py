from assets.permissions import get_user_role, ROLE_ADMIN, ROLE_OPERATOR, ROLE_AUDITOR


def role_context(request):
    """Menyediakan variabel otorisasi role untuk seluruh template antarmuka pengguna."""
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return {
            'user_role': 'anonymous',
            'is_admin': False,
            'is_operator': False,
            'is_read_only': True,
        }

    role = get_user_role(request.user)
    return {
        'user_role': role,
        'is_admin': role == ROLE_ADMIN,
        'is_operator': role in (ROLE_ADMIN, ROLE_OPERATOR),
        'is_read_only': role == ROLE_AUDITOR,
    }
