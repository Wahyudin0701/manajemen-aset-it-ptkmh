"""
Package assets.views
Mengekspos seluruh controller view untuk backward compatibility penuh
dengan konfigurasi URL dan import existing di itam_core.
"""

# Base & Dashboard
from .base_views import (
    dashboard,
    custom_404_view,
)

# Authentication & Profile
from .auth_views import (
    login_view,
    logout_view,
    profile_view,
)

# Assets & Units Management
from .asset_views import (
    asset_list,
    asset_add,
    asset_edit,
    asset_delete,
    asset_units,
    unit_add,
    unit_edit,
    unit_update_status,
    unit_delete,
    unit_history,
)

# Status Aset
from .status_views import (
    status_aset_list,
)

# Distribusi & Penugasan
from .distribution_views import (
    distribusi_list,
    distribusi_handover,
    distribusi_mutation,
    distribusi_return,
    distribusi_upload_doc,
    validate_uploaded_document,
)

# Karyawan (Employees)
from .employee_views import (
    employee_list,
    employee_detail,
    employee_create,
    employee_edit,
    employee_delete,
    employee_activate,
)

# Configuration Item (CI / CMDB)
from .ci_views import (
    ci_list,
    ci_detail,
    ci_create,
    ci_edit,
    ci_assign,
    ci_remove,
    ci_replace,
    ci_report_damage,
    ci_export_excel,
    ci_export_pdf,
)

# Consumable Item (Barang Habis Pakai)
from .consumable_views import (
    consumable_list,
    consumable_detail,
    consumable_create,
    consumable_edit,
    consumable_in,
    consumable_out,
    consumable_adjust,
    consumable_transaction_reverse,
    consumable_export_excel,
    consumable_export_pdf,
)

# QR Code & Public Info
from .qr_views import (
    unit_qr_code,
    unit_public_detail,
)

# Database Backup
from .backup_views import (
    backup_database_view,
)

# Report Exports - PDF
from .report_pdf_views import (
    asset_export_pdf,
    distribusi_export_pdf,
    status_aset_export_pdf,
    employee_export_pdf,
    employee_detail_export_pdf,
    unit_history_export_pdf,
    asset_units_export_pdf,
)

# Report Exports - Excel
from .report_excel_views import (
    asset_export_excel,
    distribusi_export_excel,
    status_aset_export_excel,
    employee_export_excel,
    employee_detail_export_excel,
    unit_history_export_excel,
    asset_units_export_excel,
)

__all__ = [
    # Base
    'dashboard',
    'custom_404_view',
    # Auth
    'login_view',
    'logout_view',
    'profile_view',
    # Assets & Units
    'asset_list',
    'asset_add',
    'asset_edit',
    'asset_delete',
    'asset_units',
    'unit_add',
    'unit_edit',
    'unit_update_status',
    'unit_delete',
    'unit_history',
    # Status
    'status_aset_list',
    # Distribusi
    'distribusi_list',
    'distribusi_handover',
    'distribusi_mutation',
    'distribusi_return',
    'distribusi_upload_doc',
    'validate_uploaded_document',
    # Employees
    'employee_list',
    'employee_detail',
    'employee_create',
    'employee_edit',
    'employee_delete',
    'employee_activate',
    # Configuration Items (CI)
    'ci_list',
    'ci_detail',
    'ci_create',
    'ci_edit',
    'ci_assign',
    'ci_remove',
    'ci_replace',
    'ci_report_damage',
    'ci_export_excel',
    'ci_export_pdf',
    # Consumable Items
    'consumable_list',
    'consumable_detail',
    'consumable_create',
    'consumable_edit',
    'consumable_in',
    'consumable_out',
    'consumable_adjust',
    'consumable_transaction_reverse',
    'consumable_export_excel',
    'consumable_export_pdf',
    # QR & Public
    'unit_qr_code',
    'unit_public_detail',
    # Backup
    'backup_database_view',
    # Export PDF
    'asset_export_pdf',
    'distribusi_export_pdf',
    'status_aset_export_pdf',
    'employee_export_pdf',
    'employee_detail_export_pdf',
    'unit_history_export_pdf',
    'asset_units_export_pdf',
    # Export Excel
    'asset_export_excel',
    'distribusi_export_excel',
    'status_aset_export_excel',
    'employee_export_excel',
    'employee_detail_export_excel',
    'unit_history_export_excel',
    'asset_units_export_excel',
]
