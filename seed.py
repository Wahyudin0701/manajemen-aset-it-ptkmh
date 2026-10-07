import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'itam_core.settings')
django.setup()

from assets.models import Asset, AssetUnit, UnitLog, Category, Employee, AssetAssignment

print("Menghapus data lama...")
UnitLog.objects.all().delete()
AssetAssignment.objects.all().delete()
AssetUnit.objects.all().delete()
Asset.objects.all().delete()
Employee.objects.all().delete()

# Pastikan Kategori ada
cat_karyawan, _ = Category.objects.get_or_create(name='Aset Karyawan')
cat_networking, _ = Category.objects.get_or_create(name='Aset Networking')

print("Membuat data Karyawan (PIC)...")
e1 = Employee.objects.create(nik='EMP-001', name='Budi Santoso')
e2 = Employee.objects.create(nik='EMP-002', name='Citra Kirana')
e3 = Employee.objects.create(nik='EMP-003', name='Andi Wijaya')
e4 = Employee.objects.create(nik='EMP-004', name='Dina Amelia')

print("Membuat Aset Karyawan...")
a1 = Asset.objects.create(category=cat_karyawan, asset_code='AST-A001', name='Laptop ThinkPad T14 Gen 3', brand='Lenovo', qty=0, uom='Unit', price=18000000, total_price=0)
a2 = Asset.objects.create(category=cat_karyawan, asset_code='AST-A002', name='Wireless Mouse M331 Silent', brand='Logitech', qty=0, uom='Pcs', price=250000, total_price=0)
a3 = Asset.objects.create(category=cat_karyawan, asset_code='AST-A003', name='Monitor 24 inch IPS Frameless', brand='Dell', qty=0, uom='Unit', price=2500000, total_price=0)
a4 = Asset.objects.create(category=cat_karyawan, asset_code='AST-A004', name='Mechanical Keyboard K8', brand='Keychron', qty=0, uom='Unit', price=1500000, total_price=0)

print("Membuat Aset Networking & Infrastruktur...")
n1 = Asset.objects.create(category=cat_networking, asset_code='AST-N001', name='Router Board RB450G', brand='MikroTik', qty=0, uom='Unit', price=1200000, total_price=0)
n2 = Asset.objects.create(category=cat_networking, asset_code='AST-N002', name='Switch Catalyst 24-Port Gigabit', brand='Cisco', qty=0, uom='Unit', price=5500000, total_price=0)
n3 = Asset.objects.create(category=cat_networking, asset_code='AST-N003', name='Kabel UTP Cat 6 (Roll 305m)', brand='Belden', qty=0, uom='Roll', price=1800000, total_price=0)
n4 = Asset.objects.create(category=cat_networking, asset_code='AST-N004', name='Access Point UniFi AC Pro', brand='Ubiquiti', qty=0, uom='Unit', price=2800000, total_price=0)

def add_units(asset, count, prefix, assign_to=None):
    for i in range(1, count + 1):
        unit_code = f"{prefix}-{i:03d}"
        status = 'tersedia'
        
        # Logika pembagian unit ke karyawan
        emp = None
        if assign_to and len(assign_to) >= i:
            status = 'digunakan'
            emp = assign_to[i-1]
            
        unit = AssetUnit.objects.create(asset=asset, unit_code=unit_code, status=status)
        UnitLog.objects.create(unit=unit, action='created', notes='Data awal migrasi sistem')
        
        if status == 'digunakan' and emp:
            unit.assigned_to = emp
            unit.save()
            AssetAssignment.objects.create(unit=unit, employee=emp, assigned_date=timezone.now(), notes='Distribusi BAST awal')
            UnitLog.objects.create(unit=unit, action='assigned', employee=emp, notes='Aset diserahkan ke PIC')

    asset.qty = count
    asset.total_price = asset.price * count
    asset.save()

print("Membuat Unit Fisik & Menyerahkan ke Karyawan...")
# Lenovo Laptop (3 unit, 2 digunakan)
add_units(a1, 3, 'LNV', assign_to=[e1, e2])
# Logitech Mouse (8 unit, 4 digunakan)
add_units(a2, 8, 'LGT', assign_to=[e1, e2, e3, e4])
# Dell Monitor (4 unit, 1 digunakan)
add_units(a3, 4, 'DLL', assign_to=[e2])
# Keychron Keyboard (2 unit, 1 digunakan)
add_units(a4, 2, 'KCH', assign_to=[e1])

# Networking (Tersedia semua karena tidak dibagikan via BAST)
add_units(n1, 2, 'MIK')
add_units(n2, 3, 'CSC')
add_units(n3, 2, 'BLD')
add_units(n4, 5, 'UBQ')

# Buat satu unit rusak untuk demo menu Maintenance
broken_unit = AssetUnit.objects.filter(asset=n4).last()
broken_unit.status = 'rusak'
broken_unit.save()
UnitLog.objects.create(unit=broken_unit, action='maintenance_in', notes='Access point sering putus koneksi (Indikator kedip merah)')

print("Seeding Selesai!")
