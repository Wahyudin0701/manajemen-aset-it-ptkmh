import uuid
from django.db import models

class Employee(models.Model):
    nik = models.CharField(max_length=20, unique=True, verbose_name="NIK")
    name = models.CharField(max_length=150, verbose_name="Nama Karyawan")
    position = models.CharField(max_length=100, blank=True, null=True, verbose_name="Jabatan")
    is_active = models.BooleanField(default=True, verbose_name="Status Aktif")

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


class ConfigurationItem(models.Model):
    """Configuration Item (CI) - Komponen individual, peripheral, atau modul sistem
    yang membentuk IT Asset atau dialokasikan langsung kepada pengguna.
    """
    CATEGORY_CHOICES = [
        ('storage', 'Storage (SSD, HDD, NVMe)'),
        ('memory', 'Memory (RAM)'),
        ('processor', 'Processor (CPU)'),
        ('motherboard', 'Motherboard / Mainboard'),
        ('gpu', 'Graphic Card / GPU'),
        ('peripheral', 'Peripheral (Monitor, Keyboard, Mouse, Headset)'),
        ('network', 'Network Component (SFP, NIC, Adapter)'),
        ('power', 'Power Supply & UPS'),
        ('other', 'Komponen Lainnya'),
    ]

    STATUS_CHOICES = [
        ('available', 'Tersedia di Gudang'),
        ('in_use', 'Sedang Digunakan'),
        ('under_inspection', 'Dalam Pemeriksaan'),
        ('under_repair', 'Dalam Perbaikan'),
        ('retired', 'Dipensiunkan'),
    ]

    CONDITION_CHOICES = [
        ('new', 'Baru (New)'),
        ('good', 'Bagus / Normal (Good)'),
        ('fair', 'Cukup / Bekas (Fair)'),
        ('damaged', 'Rusak (Damaged)'),
    ]

    ci_code = models.CharField(max_length=60, unique=True, verbose_name="Kode CI")
    name = models.CharField(max_length=150, verbose_name="Nama Item / Komponen")
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='storage', verbose_name="Kategori")
    brand = models.CharField(max_length=100, blank=True, null=True, verbose_name="Merek")
    model_series = models.CharField(max_length=100, blank=True, null=True, verbose_name="Model / Seri")
    serial_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nomor Seri (S/N)")
    specifications = models.TextField(blank=True, null=True, verbose_name="Spesifikasi Teknis")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available', verbose_name="Status Operasional")
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good', verbose_name="Kondisi Fisik")

    # Relasi Pemasangan atau Alokasi
    installed_on = models.ForeignKey(AssetUnit, on_delete=models.SET_NULL, null=True, blank=True, related_name='components', verbose_name="Terpasang Pada Perangkat")
    assigned_to = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='held_cis', verbose_name="Dialokasikan Langsung ke Karyawan")

    location = models.CharField(max_length=150, blank=True, null=True, verbose_name="Lokasi Penyimpanan")
    purchase_date = models.DateField(blank=True, null=True, verbose_name="Tanggal Pembelian")
    warranty_expiry = models.DateField(blank=True, null=True, verbose_name="Garansi Hingga")
    price = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Harga Perolehan")
    notes = models.TextField(blank=True, null=True, verbose_name="Catatan")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Waktu Ditambahkan")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Waktu Diperbarui")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ci_code']),
            models.Index(fields=['status']),
            models.Index(fields=['category']),
            models.Index(fields=['serial_number']),
        ]

    def __str__(self):
        return f"{self.ci_code} - {self.name}"

    @property
    def current_relation_display(self):
        """Menampilkan target penggunaan aktif (perangkat atau karyawan)."""
        if self.installed_on:
            user_suffix = f" (PIC: {self.installed_on.assigned_to.name})" if self.installed_on.assigned_to else ""
            return f"Terpasang: {self.installed_on.unit_code}{user_suffix}"
        elif self.assigned_to:
            return f"Dipegang: {self.assigned_to.name}"
        elif self.status == 'available':
            return self.location or "Gudang IT"
        return self.get_status_display()

    @property
    def effective_user(self):
        """Karyawan pemegang efektif, baik langsung maupun melalui perangkat terpasang."""
        if self.assigned_to:
            return self.assigned_to
        if self.installed_on and self.installed_on.assigned_to:
            return self.installed_on.assigned_to
        return None


class CIHistory(models.Model):
    """Riwayat historis perjalanan dan perubahan Configuration Item."""
    ACTION_CHOICES = [
        ('created', 'Didaftarkan ke Sistem'),
        ('installed', 'Dipasang ke Perangkat'),
        ('removed', 'Dilepas dari Perangkat'),
        ('assigned', 'Dialokasikan ke Karyawan'),
        ('returned', 'Dikembalikan ke Gudang'),
        ('replaced', 'Digantikan (Replacement / Upgrade)'),
        ('repair_in', 'Masuk Perbaikan'),
        ('repair_out', 'Selesai Perbaikan'),
        ('status_change', 'Perubahan Status / Kondisi'),
        ('retired', 'Dipensiunkan'),
    ]

    ci = models.ForeignKey(ConfigurationItem, on_delete=models.CASCADE, related_name='history', verbose_name="Configuration Item")
    action = models.CharField(max_length=25, choices=ACTION_CHOICES, verbose_name="Jenis Aksi")
    related_unit = models.ForeignKey(AssetUnit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Perangkat Terkait")
    related_employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Karyawan Terkait")
    performed_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Dilakukan Oleh")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Waktu Peristiwa")
    notes = models.TextField(blank=True, null=True, verbose_name="Catatan")

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.ci.ci_code} - {self.get_action_display()} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"


class ConsumableItem(models.Model):
    """Master Barang Habis Pakai (Consumable Item) untuk IT Network & Technical Support.
    Mendukung tracking kuantitas bulk, konversi satuan pembelian ke satuan dasar,
    serta pengawasan batas stok minimum dan out-of-stock.
    """
    CATEGORY_CHOICES = [
        ('cable', 'Kabel (UTP, Fiber Optic, HDMI, Patch Cord)'),
        ('connector', 'Konektor & Barrel (RJ45, Modular, Adapter)'),
        ('maintenance', 'Bahan Kimia & Perawatan (Thermal Paste, Contact Cleaner)'),
        ('fastener', 'Sekrup, Baut, Cable Ties & Mounting'),
        ('electrical', 'Kelistrikan & Isolasi (Isolasi Listrik, Heat Shrink)'),
        ('cleaning', 'Cleaning Supplies & Lap Microfiber'),
        ('tools_acc', 'Aksesori & Komponen Kecil Lainnya'),
    ]

    item_code = models.CharField(max_length=50, unique=True, verbose_name="Kode Barang", db_index=True)
    name = models.CharField(max_length=150, verbose_name="Nama Barang")
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='cable', verbose_name="Kategori")
    brand = models.CharField(max_length=100, blank=True, null=True, verbose_name="Merek / Brand")
    specification = models.CharField(max_length=255, blank=True, null=True, verbose_name="Spesifikasi")
    description = models.TextField(blank=True, null=True, verbose_name="Deskripsi")

    # Satuan & Konversi
    base_unit = models.CharField(max_length=30, default='pcs', verbose_name="Satuan Dasar (UoM)")
    purchase_unit = models.CharField(max_length=30, blank=True, null=True, verbose_name="Satuan Pembelian")
    conversion_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=1.00,
        verbose_name="Faktor Konversi (1 Satuan Pembelian = X Satuan Dasar)"
    )

    # Persediaan
    stock_available = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Stok Tersedia")
    minimum_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Batas Stok Minimum")
    location = models.CharField(max_length=100, default='Gudang Induk (GI)', verbose_name="Lokasi Penyimpanan")

    # Finansial & Pengadaan
    last_purchase_price = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Harga Beli Terakhir")

    notes = models.TextField(blank=True, null=True, verbose_name="Catatan")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Waktu Ditambahkan")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Waktu Diperbarui")

    class Meta:
        ordering = ['name']
        verbose_name = "Consumable Item"
        verbose_name_plural = "Consumable Items"
        indexes = [
            models.Index(fields=['item_code']),
            models.Index(fields=['category']),
            models.Index(fields=['stock_available']),
            models.Index(fields=['location']),
        ]

    def __str__(self):
        return f"{self.item_code} - {self.name}"

    @property
    def stock_status(self):
        """Menentukan status ketersediaan stok aktual."""
        if self.stock_available <= 0:
            return 'out_of_stock'
        elif self.stock_available <= self.minimum_stock:
            return 'low_stock'
        return 'available'

    @property
    def stock_status_display(self):
        status_labels = {
            'out_of_stock': 'Habis',
            'low_stock': 'Menipis',
            'available': 'Tersedia',
        }
        return status_labels.get(self.stock_status, 'Tersedia')

    @property
    def formatted_stock(self):
        """Menampilkan kuantitas stok yang rapi tanpa trailing zero berlebih."""
        val = self.stock_available
        if val % 1 == 0:
            val_str = f"{int(val):,}".replace(",", ".")
        else:
            val_str = f"{val:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
        return f"{val_str} {self.base_unit}"

    @property
    def formatted_minimum_stock(self):
        val = self.minimum_stock
        if val % 1 == 0:
            val_str = f"{int(val):,}".replace(",", ".")
        else:
            val_str = f"{val:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
        return f"{val_str} {self.base_unit}"


class ConsumableTransaction(models.Model):
    """Buku Besar Transaksi Consumable (Stock Ledger) yang bersifat audit-proof / append-only.
    Mencatat mutasi masuk, pemakaian teknisi, penyesuaian stock opname, dan pembalikan transaksi.
    """
    TYPE_CHOICES = [
        ('in', 'Barang Masuk'),
        ('out', 'Barang Keluar (Pemakaian)'),
        ('adjustment', 'Penyesuaian (Stock Opname)'),
        ('reversal', 'Pembalikan Transaksi (Reversal)'),
    ]

    transaction_code = models.CharField(max_length=60, unique=True, verbose_name="Kode Transaksi", db_index=True)
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Jenis Transaksi")
    item = models.ForeignKey(ConsumableItem, on_delete=models.PROTECT, related_name='transactions', verbose_name="Item Consumable")

    # Kuantitas & Konversi
    quantity = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Jumlah Transaksi")
    unit = models.CharField(max_length=30, verbose_name="Satuan Transaksi")
    conversion_rate = models.DecimalField(max_digits=10, decimal_places=2, default=1.00, verbose_name="Faktor Konversi ke Satuan Dasar")
    quantity_base = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Jumlah Efektif (Satuan Dasar)")

    # Snapshot Saldo (Audit Trail)
    stock_before = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Saldo Sebelum")
    stock_after = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Saldo Sesudah")

    # Integrasi & Referensi
    source_destination = models.CharField(max_length=150, blank=True, null=True, verbose_name="Sumber / Tujuan / Area Penggunaan")
    recipient_employee = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='consumable_usages', verbose_name="Teknisi / Karyawan Penerima"
    )
    related_unit = models.ForeignKey(
        AssetUnit, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='consumable_usages', verbose_name="Unit Aset Terkait"
    )
    ticket_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="No. Tiket / Work Order")
    supplier = models.CharField(max_length=150, blank=True, null=True, verbose_name="Vendor / Supplier")
    reference_no = models.CharField(max_length=100, blank=True, null=True, verbose_name="No. Referensi (PO/BAST/Faktur)")
    batch_lot = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nomor Batch / Lot")
    expiry_date = models.DateField(blank=True, null=True, verbose_name="Tanggal Kedaluwarsa")

    # Aktor & Timestamp
    performed_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Dicatat Oleh"
    )
    transaction_date = models.DateField(verbose_name="Tanggal Transaksi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Waktu Sistem")
    notes = models.TextField(blank=True, null=True, verbose_name="Catatan")

    # Reversal Mechanism
    is_reversed = models.BooleanField(default=False, verbose_name="Telah Dibalik")
    reversed_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reversal_target', verbose_name="Dibalik Oleh Transaksi"
    )

    class Meta:
        ordering = ['-transaction_date', '-created_at', '-id']
        verbose_name = "Transaksi Consumable"
        verbose_name_plural = "Transaksi Consumable"
        indexes = [
            models.Index(fields=['transaction_code']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['transaction_date']),
            models.Index(fields=['ticket_number']),
        ]

    def __str__(self):
        return f"{self.transaction_code} - {self.get_transaction_type_display()} ({self.item.name})"


