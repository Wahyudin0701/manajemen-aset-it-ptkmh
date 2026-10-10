from django.shortcuts import render

from django.contrib import admin
from django.urls import path, re_path
from assets.views import profile_view, custom_404_view, login_view, logout_view, unit_qr_code, unit_public_detail, dashboard, status_aset_list, status_aset_export_pdf, asset_list, asset_add, asset_edit, asset_delete, asset_units, asset_units_export_pdf, unit_add, unit_edit, unit_history, unit_history_export_pdf, unit_update_status, distribusi_list, distribusi_handover, distribusi_mutation, distribusi_return, distribusi_export_pdf, distribusi_upload_doc, employee_list, employee_export_pdf, employee_detail, employee_detail_export_pdf, employee_create, employee_edit, employee_delete, asset_export_pdf, asset_export_excel, backup_database_view
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
    path('aset/<int:asset_id>/units/add/', unit_add, name='unit_add'),
    path('unit/<int:unit_id>/edit/', unit_edit, name='unit_edit'),
    path('unit/<int:unit_id>/status/', unit_update_status, name='unit_update_status'),
    path('unit/<int:unit_id>/history/', unit_history, name='unit_history'),
    path('unit/<int:unit_id>/history/export/', unit_history_export_pdf, name='unit_history_export_pdf'),
    path('status-aset/', status_aset_list, name='status_aset_list'),
    path('status-aset/export/', status_aset_export_pdf, name='status_aset_export_pdf'),
    path('distribusi/', distribusi_list, name='distribusi_list'),
    path('distribusi/export/', distribusi_export_pdf, name='distribusi_export_pdf'),
    path('distribusi/handover/', distribusi_handover, name='distribusi_handover'),
    path('distribusi/mutation/', distribusi_mutation, name='distribusi_mutation'),
    path('distribusi/return/', distribusi_return, name='distribusi_return'),
    path('distribusi/<int:assignment_id>/upload/', distribusi_upload_doc, name='distribusi_upload_doc'),
    path('karyawan/', employee_list, name='employee_list'),
    path('karyawan/export/', employee_export_pdf, name='employee_export_pdf'),
    path('karyawan/<int:emp_id>/', employee_detail, name='employee_detail'),
    path('karyawan/<int:emp_id>/export/', employee_detail_export_pdf, name='employee_detail_export_pdf'),
    path('karyawan/buat/', employee_create, name='employee_create'),
    path('karyawan/<int:emp_id>/edit/', employee_edit, name='employee_edit'),
    path('karyawan/<int:emp_id>/delete/', employee_delete, name='employee_delete'),
    path('qr/<uuid:uuid>/', unit_qr_code, name='unit_qr_code'),
    path('public/unit/<uuid:uuid>/', unit_public_detail, name='unit_public_detail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


handler404 = 'assets.views.custom_404_view'


