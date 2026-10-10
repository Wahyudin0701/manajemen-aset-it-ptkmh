import re

with open('c:/laragon/www/Manajemen-Aset-IT/itam_core/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Imports
new_imports = ", asset_units_export_excel, unit_history_export_excel, status_aset_export_excel, distribusi_export_excel, employee_export_excel, employee_detail_export_excel"
content = content.replace("asset_export_excel, backup_database_view", "asset_export_excel, backup_database_view" + new_imports)

# Paths
content = content.replace("path('aset/<int:asset_id>/units/export/', asset_units_export_pdf, name='asset_units_export_pdf'),", "path('aset/<int:asset_id>/units/export/', asset_units_export_pdf, name='asset_units_export_pdf'),\n    path('aset/<int:asset_id>/units/export-excel/', asset_units_export_excel, name='asset_units_export_excel'),")

content = content.replace("path('unit/<int:unit_id>/history/export/', unit_history_export_pdf, name='unit_history_export_pdf'),", "path('unit/<int:unit_id>/history/export/', unit_history_export_pdf, name='unit_history_export_pdf'),\n    path('unit/<int:unit_id>/history/export-excel/', unit_history_export_excel, name='unit_history_export_excel'),")

content = content.replace("path('status-aset/export/', status_aset_export_pdf, name='status_aset_export_pdf'),", "path('status-aset/export/', status_aset_export_pdf, name='status_aset_export_pdf'),\n    path('status-aset/export-excel/', status_aset_export_excel, name='status_aset_export_excel'),")

content = content.replace("path('distribusi/export/', distribusi_export_pdf, name='distribusi_export_pdf'),", "path('distribusi/export/', distribusi_export_pdf, name='distribusi_export_pdf'),\n    path('distribusi/export-excel/', distribusi_export_excel, name='distribusi_export_excel'),")

content = content.replace("path('karyawan/export/', employee_export_pdf, name='employee_export_pdf'),", "path('karyawan/export/', employee_export_pdf, name='employee_export_pdf'),\n    path('karyawan/export-excel/', employee_export_excel, name='employee_export_excel'),")

content = content.replace("path('karyawan/<int:emp_id>/export/', employee_detail_export_pdf, name='employee_detail_export_pdf'),", "path('karyawan/<int:emp_id>/export/', employee_detail_export_pdf, name='employee_detail_export_pdf'),\n    path('karyawan/<int:emp_id>/export-excel/', employee_detail_export_excel, name='employee_detail_export_excel'),")

with open('c:/laragon/www/Manajemen-Aset-IT/itam_core/urls.py', 'w', encoding='utf-8') as f:
    f.write(content)
    
print("Urls updated!")
