from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Group

ROLE_ADMIN = 'admin'
ROLE_OPERATOR = 'operator'
ROLE_AUDITOR = 'auditor'

GROUP_ROLES = {
    'Administrator': ROLE_ADMIN,
    'Teknisi IT': ROLE_OPERATOR,
    'Operator IT': ROLE_OPERATOR,
    'Auditor': ROLE_AUDITOR,
    'Management': ROLE_AUDITOR,
}


def get_user_role(user):
    """Menentukan role pengguna berdasarkan is_superuser atau keanggotaan Django Group."""
    if not user.is_authenticated:
        return 'anonymous'

    # Superuser otomatis memiliki role admin tertinggi
    if user.is_superuser:
        return ROLE_ADMIN

    user_groups = list(user.groups.values_list('name', flat=True))

    for group_name, role in GROUP_ROLES.items():
        if group_name in user_groups:
            return role

    # Default jika staf biasa atau belum ada grup yang cocok: admin jika is_staff, operator jika biasa
    if user.is_staff:
        return ROLE_ADMIN

    return ROLE_OPERATOR


def admin_required(view_func):
    """Membatasi akses rute sensitif (seperti backup database) hanya untuk Super Admin."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect('login')

        role = get_user_role(request.user)
        if role != ROLE_ADMIN:
            raise PermissionDenied("Akses ditolak: Hanya Administrator yang berhak melakukan tindakan ini.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def operator_required(view_func):
    """Membatasi aksi modifikasi data (create, update, delete) hanya untuk Admin dan Operator/Teknisi.
    Pengguna dengan role Auditor (Read-Only) akan diblokir dengan HTTP 403 Forbidden.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect('login')

        role = get_user_role(request.user)
        if role == ROLE_AUDITOR:
            raise PermissionDenied("Akses ditolak: Akun Anda memiliki peran Read-Only (Auditor/Management) dan tidak diizinkan mengubah data.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
