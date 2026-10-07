import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'itam_core.settings')
django.setup()

from assets.models import Asset, AssetUnit

created_count = 0
for asset in Asset.objects.all():
    existing = asset.units.count()
    to_create = asset.qty - existing
    if to_create > 0:
        for i in range(1, to_create + 1):
            unit_num = existing + i
            unit_code = f"{asset.asset_code}-{unit_num:03d}"
            AssetUnit.objects.get_or_create(
                unit_code=unit_code,
                defaults={'asset': asset, 'status': 'tersedia'}
            )
            created_count += 1

print(f"Selesai! {created_count} unit baru dibuat.")
