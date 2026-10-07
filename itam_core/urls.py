from django.contrib import admin
from django.urls import path
from assets.views import dashboard, status_aset_list, asset_list, asset_add, asset_edit, asset_delete, asset_units, unit_add, unit_edit, unit_history, unit_update_status, distribusi_list, distribusi_handover, distribusi_mutation, distribusi_return, distribusi_upload_doc, employee_list, employee_detail, employee_create, employee_edit, employee_delete
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),
    path('aset/', asset_list, name='asset_list'),
    path('aset/add/', asset_add, name='asset_add'),
    path('aset/<int:asset_id>/edit/', asset_edit, name='asset_edit'),
    path('aset/<int:asset_id>/delete/', asset_delete, name='asset_delete'),
    path('aset/<int:asset_id>/units/', asset_units, name='asset_units'),
    path('aset/<int:asset_id>/units/add/', unit_add, name='unit_add'),
    path('unit/<int:unit_id>/edit/', unit_edit, name='unit_edit'),
    path('unit/<int:unit_id>/status/', unit_update_status, name='unit_update_status'),
    path('unit/<int:unit_id>/history/', unit_history, name='unit_history'),
    path('status-aset/', status_aset_list, name='status_aset_list'),
    path('distribusi/', distribusi_list, name='distribusi_list'),
    path('distribusi/handover/', distribusi_handover, name='distribusi_handover'),
    path('distribusi/mutation/', distribusi_mutation, name='distribusi_mutation'),
    path('distribusi/return/', distribusi_return, name='distribusi_return'),
    path('distribusi/<int:assignment_id>/upload/', distribusi_upload_doc, name='distribusi_upload_doc'),
    path('karyawan/', employee_list, name='employee_list'),
    path('karyawan/<int:emp_id>/', employee_detail, name='employee_detail'),
    path('karyawan/buat/', employee_create, name='employee_create'),
    path('karyawan/<int:emp_id>/edit/', employee_edit, name='employee_edit'),
    path('karyawan/<int:emp_id>/delete/', employee_delete, name='employee_delete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
