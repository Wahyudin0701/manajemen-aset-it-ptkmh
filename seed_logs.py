import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'itam_core.settings')
django.setup()

from assets.models import AssetUnit, UnitLog

created_count = 0
for unit in AssetUnit.objects.all():
    if not unit.logs.exists():
        UnitLog.objects.create(
            unit=unit,
            action='created',
            notes="Data Awal (Sistem Lama)"
        )
        if unit.status == 'digunakan' and unit.assigned_to:
             UnitLog.objects.create(
                unit=unit,
                action='assigned',
                employee=unit.assigned_to,
                notes="Data Awal (Sedang Dipinjam)"
            )
        created_count += 1

print(f"Selesai! {created_count} riwayat awal dibuat.")
