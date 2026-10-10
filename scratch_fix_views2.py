import re

with open('c:/laragon/www/Manajemen-Aset-IT/assets/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix distribusi_export_excel
content = content.replace("assignments.filter(status='active')", "assignments.filter(status='aktif')")
content = content.replace("assignments.filter(status='returned')", "assignments.filter(status='dikembalikan')")
content = content.replace("status_str = \"Aktif\" if a.status == 'active' else \"Dikembalikan\"", "status_str = \"Aktif\" if a.status == 'aktif' else \"Dikembalikan\"")
content = content.replace("a.assignment_date.strftime('%d %b %Y') if a.assignment_date else '-'", "a.assigned_date.strftime('%d %b %Y') if a.assigned_date else '-'")
content = content.replace(".order_by('-assignment_date')", ".order_by('-assigned_date')")

# 2. Fix status_aset_export_excel
content = content.replace("'No', 'Kode Unit', 'Nama Aset', 'S/N', 'Status', 'Keterangan'", "'No', 'Kode Unit', 'Nama Aset', 'Area', 'Status', 'Lokasi'")
content = content.replace("u.serial_number or '-'", "u.area or '-'")
content = content.replace("u.condition_notes or '-'", "u.location or '-'")

# 3. Fix employee_detail_export_excel
content = content.replace("status='active'", "status='aktif'")
content = content.replace("'No', 'Kode Unit', 'Nama Aset', 'S/N', 'Tanggal Diberikan'", "'No', 'Kode Unit', 'Nama Aset', 'Area', 'Tanggal Diberikan'")
content = content.replace("a.unit.serial_number if a.unit else '-'", "a.unit.area if a.unit else '-'")
# We already replaced assignment_date for `a` globally, let's verify if there's any left:
content = content.replace("a.assignment_date", "a.assigned_date")

# 4. Fix asset_units_export_excel
content = content.replace("'No', 'Kode Unit', 'S/N', 'Status', 'Lokasi/Pengguna', 'Keterangan'", "'No', 'Kode Unit', 'Area', 'Status', 'Lokasi/Pengguna', '-'")

with open('c:/laragon/www/Manajemen-Aset-IT/assets/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed attribute errors in views.py")
