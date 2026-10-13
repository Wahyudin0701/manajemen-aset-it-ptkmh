import uuid
from django.db import models

class Employee(models.Model):
    nik = models.CharField(max_length=20, unique=True, verbose_name="NIK")
    name = models.CharField(max_length=150, verbose_name="Nama Karyawan")
    position = models.CharField(max_length=100, blank=True, null=True, verbose_name="Jabatan")

    def __str__(self):
        return f"{self.nik} - {self.name}"

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Kategori Aset")
    
    def __str__(self):
        return self.name

class Asset(models.Model):
    """Jenis/Tipe aset (SKU-level). Contoh: Wireless CCTV, Qty: 20"""
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name="Kategori")
    no_index = models.CharField(max_length=20, blank=True, null=True, verbose_name="No")
    asset_code = models.CharField(max_length=50, unique=True, verbose_name="Kode Aset")
    name = models.CharField(max_length=150, verbose_name="Nama Aset")
    brand = models.CharField(max_length=100, blank=True, null=True, verbose_name="Merek")
    
    qty = models.IntegerField(default=0, verbose_name="Jumlah (Qty)")
    sum_qty = models.IntegerField(default=0, verbose_name="sumQty")
    uom = models.CharField(max_length=50, blank=True, null=True, verbose_name="Satuan (UoM)")
    price = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Harga Satuan")
    total_price = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Total Harga")
    
    serial_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Serial Number")
    purchase_date = models.DateField(blank=True, null=True, verbose_name="Tanggal Pembelian")
    notes = models.TextField(blank=True, null=True, verbose_name="Catatan")

    def __str__(self):
        return f"{self.asset_code} - {self.name}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_code = None
        if not is_new:
            old_obj = Asset.objects.filter(pk=self.pk).only('asset_code').first()
            if old_obj and old_obj.asset_code != self.asset_code:
                old_code = old_obj.asset_code

        super().save(*args, **kwargs)

        if old_code and old_code != self.asset_code:
            from django.db import transaction
            with transaction.atomic():
                for unit in self.units.all():
                    if unit.unit_code.startswith(f"{old_code}-"):
                        suffix = unit.unit_code[len(f"{old_code}-"):]
                    elif '-' in unit.unit_code:
                        suffix = unit.unit_code.rsplit('-', 1)[-1]
                    else:
                        suffix = unit.unit_code

                    target_code = f"{self.asset_code}-{suffix}"
                    if AssetUnit.objects.filter(unit_code=target_code).exclude(pk=unit.pk).exists():
                        counter = 1
                        try:
                            base_num = int(suffix)
                            while AssetUnit.objects.filter(unit_code=target_code).exclude(pk=unit.pk).exists():
                                target_code = f"{self.asset_code}-{base_num + counter:03d}"
                                counter += 1
                        except ValueError:
                            while AssetUnit.objects.filter(unit_code=target_code).exclude(pk=unit.pk).exists():
                                target_code = f"{self.asset_code}-{suffix}-{counter}"
                                counter += 1
                    new_unit_code = target_code

                    if unit.unit_code != new_unit_code:
                        old_unit_code = unit.unit_code
                        unit.unit_code = new_unit_code
                        unit.save(update_fields=['unit_code'])
                        UnitLog.objects.create(
                            unit=unit,
                            action='other',
                            notes=f"Kode unit diperbarui otomatis dari {old_unit_code} ke {new_unit_code} karena perubahan kode aset induk."
                        )

class AssetUnit(models.Model):
    """Unit fisik individual dari sebuah jenis aset. Contoh: CCTV-001, CCTV-002"""
    STATUS_CHOICES = [
        ('tersedia', 'Tersedia'),
        ('digunakan', 'Digunakan'),
        ('rusak', 'Diperbaiki'),
        ('pensiun', 'Dipensiunkan'),
    ]

    AREA_CHOICES = [
        ('Regulating Weir (RW)', 'Regulating Weir (RW)'),
        ('Jakon', 'Jakon'),
        ('Beringin Tunggal (BT)', 'Beringin Tunggal (BT)'),
        ('DAM', 'DAM'),
        ('Adit 1', 'Adit 1'),
        ('Adit 2', 'Adit 2'),
        ('Adit 3', 'Adit 3'),
        ('Gudang Induk (GI)', 'Gudang Induk (GI)'),
        ('Vertical Shaft (VS)', 'Vertical Shaft (VS)'),
        ('Power House (PH)', 'Power House (PH)'),
        ('Lain-lainnya', 'Lain-lainnya'),
    ]

    id_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='units', verbose_name="Jenis Aset")
    unit_code = models.CharField(max_length=60, unique=True, verbose_name="Kode Unit")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='tersedia', verbose_name="Status")
    assigned_to = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='held_units', verbose_name="Pengguna Aset (PIC)")
    area = models.CharField(max_length=50, choices=AREA_CHOICES, blank=True, null=True, verbose_name="Area Pemasangan")
    location = models.CharField(max_length=255, blank=True, null=True, verbose_name="Lokasi Spesifik")

    def __str__(self):
        return self.unit_code

class UnitLog(models.Model):
    """Riwayat historis perjalanan unit aset (Timeline)"""
    ACTION_CHOICES = [
        ('created', 'Ditambahkan ke Sistem'),
        ('assigned', 'Diserahkan kepada Karyawan'),
        ('returned', 'Dikembalikan'),
        ('maintenance_in', 'Masuk Perbaikan'),
        ('maintenance_out', 'Selesai Perbaikan'),
        ('mutation', 'Pindah User'),
        ('retired', 'Dipensiunkan'),
        ('other', 'Lain-lain'),
    ]

    unit = models.ForeignKey(AssetUnit, on_delete=models.CASCADE, related_name='logs', verbose_name="Unit Aset")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Waktu Kejadian")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="Jenis Kejadian")
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Karyawan Terkait")
    notes = models.TextField(blank=True, null=True, verbose_name="Catatan")

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.unit.unit_code} - {self.get_action_display()}"

class AssetAssignment(models.Model):
    """Riwayat distribusi aset: serah terima, mutasi, dan pengembalian."""
    TYPE_CHOICES = [
        ('handover', 'Serah Terima'),
        ('mutation', 'Mutasi'),
        ('return', 'Pengembalian'),
    ]
    STATUS_CHOICES = [
        ('aktif', 'Aktif'),
        ('dikembalikan', 'Dikembalikan'),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='handover', verbose_name="Tipe Distribusi")
    unit = models.ForeignKey(AssetUnit, on_delete=models.PROTECT, verbose_name="Unit Aset")
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Karyawan Penerima", related_name='received_assignments')
    from_employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Karyawan Pengirim", related_name='sent_assignments')
    assigned_date = models.DateField(verbose_name="Tanggal Transaksi")
    returned_date = models.DateField(blank=True, null=True, verbose_name="Tanggal Dikembalikan")
    document = models.FileField(upload_to='bast_documents/', blank=True, null=True, verbose_name="Dokumen Fisik")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aktif', verbose_name="Status Penugasan")
    notes = models.TextField(blank=True, null=True, verbose_name="Catatan Tambahan")
    created_at = models.DateTimeField(auto_now_add=True, null=True, verbose_name="Waktu Dibuat")

    def __str__(self):
        return f"{self.get_type_display()} - {self.unit.unit_code} → {self.employee.name}"

