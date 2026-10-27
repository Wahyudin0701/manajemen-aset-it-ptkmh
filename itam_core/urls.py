from django.shortcuts import render

from django.contrib import admin
from django.urls import path, re_path
from assets.views import (
    profile_view, custom_404_view, login_view, logout_view, unit_qr_code, unit_public_detail,
    dashboard, status_aset_list, status_aset_export_pdf, asset_list, asset_add, asset_edit,
    asset_delete, asset_units, asset_units_export_pdf, unit_add, unit_edit, unit_delete,
    unit_history, unit_history_export_pdf, unit_update_status, distribusi_list, distribusi_handover,
    distribusi_mutation, distribusi_return, distribusi_export_pdf, distribusi_upload_doc,
    employee_list, employee_export_pdf, employee_detail, employee_detail_export_pdf,
    employee_create, employee_edit, employee_delete, employee_activate,
    ci_list, ci_detail, ci_create, ci_edit, ci_assign, ci_remove, ci_replace, ci_report_damage,
    asset_export_pdf, asset_export_excel, backup_database_view, asset_units_export_excel,
    unit_history_export_excel, status_aset_export_excel, distribusi_export_excel,
    employee_export_excel, employee_detail_export_excel,
    consumable_list, consumable_detail, consumable_create, consumable_edit,
    consumable_in, consumable_out, consumable_adjust, consumable_transaction_reverse,
    consumable_export_excel, consumable_export_pdf
)
from django.conf import settings
from django.conf.urls.static import static


admin.site.site_header = "Administrasi IT All Role PT. KMH"
admin.site.site_title = "Admin Portal IT"
admin.site.index_title = "Manajemen Database Inti"

urlpatterns = [
    path('profil/', profile_view, name='profile'),
    path('backup/', backup_database_view, name='backup_database'),
    path('404/', custom_404_view, name='test_404'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    # path('admin/', admin.site.urls),  # Django Admin dinonaktifkan
    path('', dashboard, name='dashboard'),
    path('aset/', asset_list, name='asset_list'),
    path('aset/export/', asset_export_pdf, name='asset_export_pdf'),
    path('aset/export-excel/', asset_export_excel, name='asset_export_excel'),
    path('aset/add/', asset_add, name='asset_add'),
    path('aset/<int:asset_id>/edit/', asset_edit, name='asset_edit'),
    path('aset/<int:asset_id>/delete/', asset_delete, name='asset_delete'),
    path('aset/<int:asset_id>/units/', asset_units, name='asset_units'),
    path('aset/<int:asset_id>/units/export/', asset_units_export_pdf, name='asset_units_export_pdf'),
    path('aset/<int:asset_id>/units/export-excel/', asset_units_export_excel, name='asset_units_export_excel'),
    path('aset/<int:asset_id>/units/add/', unit_add, name='unit_add'),
    path('unit/<int:unit_id>/edit/', unit_edit, name='unit_edit'),
    path('unit/<int:unit_id>/delete/', unit_delete, name='unit_delete'),
    path('unit/<int:unit_id>/status/', unit_update_status, name='unit_update_status'),
    path('unit/<int:unit_id>/history/', unit_history, name='unit_history'),
    path('unit/<int:unit_id>/history/export/', unit_history_export_pdf, name='unit_history_export_pdf'),
    path('unit/<int:unit_id>/history/export-excel/', unit_history_export_excel, name='unit_history_export_excel'),
    path('status-aset/', status_aset_list, name='status_aset_list'),
    path('status-aset/export/', status_aset_export_pdf, name='status_aset_export_pdf'),
    path('status-aset/export-excel/', status_aset_export_excel, name='status_aset_export_excel'),
    path('distribusi/', distribusi_list, name='distribusi_list'),
    path('distribusi/export/', distribusi_export_pdf, name='distribusi_export_pdf'),
    path('distribusi/export-excel/', distribusi_export_excel, name='distribusi_export_excel'),
    path('distribusi/handover/', distribusi_handover, name='distribusi_handover'),
    path('distribusi/mutation/', distribusi_mutation, name='distribusi_mutation'),
    path('distribusi/return/', distribusi_return, name='distribusi_return'),
    path('distribusi/<int:assignment_id>/upload/', distribusi_upload_doc, name='distribusi_upload_doc'),
    path('karyawan/', employee_list, name='employee_list'),
    path('karyawan/export/', employee_export_pdf, name='employee_export_pdf'),
    path('karyawan/export-excel/', employee_export_excel, name='employee_export_excel'),
    path('karyawan/<int:emp_id>/', employee_detail, name='employee_detail'),
    path('karyawan/<int:emp_id>/export/', employee_detail_export_pdf, name='employee_detail_export_pdf'),
    path('karyawan/<int:emp_id>/export-excel/', employee_detail_export_excel, name='employee_detail_export_excel'),
    path('karyawan/buat/', employee_create, name='employee_create'),
    path('karyawan/<int:emp_id>/edit/', employee_edit, name='employee_edit'),
    path('karyawan/<int:emp_id>/delete/', employee_delete, name='employee_delete'),
    path('karyawan/<int:emp_id>/activate/', employee_activate, name='employee_activate'),
    # Configuration Items (CI / CMDB)
    path('ci/', ci_list, name='ci_list'),
    path('ci/create/', ci_create, name='ci_create'),
    path('ci/<int:ci_id>/', ci_detail, name='ci_detail'),
    path('ci/<int:ci_id>/edit/', ci_edit, name='ci_edit'),
    path('ci/<int:ci_id>/assign/', ci_assign, name='ci_assign'),
    path('ci/<int:ci_id>/remove/', ci_remove, name='ci_remove'),
    path('ci/<int:ci_id>/replace/', ci_replace, name='ci_replace'),
    path('ci/<int:ci_id>/report-damage/', ci_report_damage, name='ci_report_damage'),
    # Consumable Items (Barang Habis Pakai)
    path('consumable/', consumable_list, name='consumable_list'),
    path('consumable/create/', consumable_create, name='consumable_create'),
    path('consumable/<int:item_id>/', consumable_detail, name='consumable_detail'),
    path('consumable/<int:item_id>/edit/', consumable_edit, name='consumable_edit'),
    path('consumable/in/', consumable_in, name='consumable_in'),
    path('consumable/out/', consumable_out, name='consumable_out'),
    path('consumable/adjust/', consumable_adjust, name='consumable_adjust'),
    path('consumable/transaction/<int:trx_id>/reverse/', consumable_transaction_reverse, name='consumable_transaction_reverse'),
    path('consumable/export-excel/', consumable_export_excel, name='consumable_export_excel'),
    path('consumable/export-pdf/', consumable_export_pdf, name='consumable_export_pdf'),
    path('qr/<uuid:uuid>/', unit_qr_code, name='unit_qr_code'),
    path('public/unit/<uuid:uuid>/', unit_public_detail, name='unit_public_detail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


handler404 = 'assets.views.custom_404_view'


