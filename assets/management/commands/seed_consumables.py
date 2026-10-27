from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from assets.models import ConsumableItem, ConsumableTransaction, Employee, AssetUnit
from datetime import date
from decimal import Decimal


class Command(BaseCommand):
    help = 'Mengisi sampel data awal master Consumable Item untuk tim IT Network & Security serta Technical Support'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Memeriksa data awal consumable item..."))

        admin_user = User.objects.filter(is_superuser=True).first()

        sample_items = [
            {
                'item_code': 'CNS-CAB-001',
                'name': 'Kabel UTP Cat6 Belden Pure Copper',
                'category': 'cable',
                'brand': 'Belden',
                'specification': 'Cat6 UTP 24 AWG Solid Copper 4-Pair 550MHz',
                'description': 'Kabel jaringan utama untuk instalasi backbone dan drop point lokal.',
                'base_unit': 'meter',
                'purchase_unit': 'roll',
                'conversion_rate': Decimal('305.00'),
                'initial_stock': Decimal('610.00'),  # 2 roll
                'minimum_stock': Decimal('100.00'),
                'location': 'Gudang Induk (GI)',
                'last_purchase_price': Decimal('1850000.00'),
                'notes': 'Stok pengadaan proyek Q3'
            },
            {
                'item_code': 'CNS-CAB-002',
                'name': 'Kabel Fiber Optik Drop Core 1 Core 3 Steel',
                'category': 'cable',
                'brand': 'Fiberhome / Netviel',
                'specification': 'Single Mode G657A1 1 Core Outdoor',
                'description': 'Kabel fiber optik outdoor untuk interkoneksi bangunan dan intake.',
                'base_unit': 'meter',
                'purchase_unit': 'roll',
                'conversion_rate': Decimal('1000.00'),
                'initial_stock': Decimal('1000.00'),  # 1 roll
                'minimum_stock': Decimal('200.00'),
                'location': 'Gudang Induk (GI)',
                'last_purchase_price': Decimal('1200000.00'),
                'notes': 'Jalur fiber optik area DAM & Power House'
            },
            {
                'item_code': 'CNS-CON-001',
                'name': 'Konektor RJ45 Cat6 Modular Plug',
                'category': 'connector',
                'brand': 'CommScope / AMP',
                'specification': 'Cat6 8P8C UTP Gold Plated Contacts',
                'description': 'Konektor RJ45 crimping untuk terminasi kabel LAN.',
                'base_unit': 'pcs',
                'purchase_unit': 'box',
                'conversion_rate': Decimal('100.00'),
                'initial_stock': Decimal('150.00'),
                'minimum_stock': Decimal('30.00'),
                'location': 'Ruang Server / IT',
                'last_purchase_price': Decimal('250000.00'),
                'notes': 'Sering digunakan teknisi lapangan'
            },
            {
                'item_code': 'CNS-CON-002',
                'name': 'Fast Connector Fiber Optic SC/UPC',
                'category': 'connector',
                'brand': 'Ilsintech / Huawei Compatible',
                'specification': 'SC/UPC Single Mode Pre-embedded Field Assembly',
                'description': 'Konektor cepat fiber optik tanpa splicing fusion.',
                'base_unit': 'pcs',
                'purchase_unit': 'pack',
                'conversion_rate': Decimal('50.00'),
                'initial_stock': Decimal('50.00'),
                'minimum_stock': Decimal('15.00'),
                'location': 'Ruang Server / IT',
                'last_purchase_price': Decimal('175000.00'),
                'notes': 'Untuk terminasi kabel drop optik'
            },
            {
                'item_code': 'CNS-MNT-001',
                'name': 'Thermal Paste Arctic MX-4 4g',
                'category': 'maintenance',
                'brand': 'Arctic',
                'specification': 'Carbon-based thermal compound 4 Gram (8.5 W/mK)',
                'description': 'Pasta pendingin CPU/GPU server, PC workstation, dan laptop.',
                'base_unit': 'tube',
                'purchase_unit': None,
                'conversion_rate': Decimal('1.00'),
                'initial_stock': Decimal('8.00'),
                'minimum_stock': Decimal('2.00'),
                'location': 'Workshop IT',
                'last_purchase_price': Decimal('115000.00'),
                'notes': 'Pemakaian preventive maintenance PC berkala'
            },
            {
                'item_code': 'CNS-FST-001',
                'name': 'Cable Ties 200mm x 3.6mm Nylon Black',
                'category': 'fastener',
                'brand': 'KSS / Insulok',
                'specification': 'UV Resistant Nylon 66, Panjang 20 cm, Lebar 3.6 mm',
                'description': 'Pengikat kabel manajemen pada rak server dan jalur kabel tray.',
                'base_unit': 'pcs',
                'purchase_unit': 'pack',
                'conversion_rate': Decimal('100.00'),
                'initial_stock': Decimal('400.00'),  # 4 pack
                'minimum_stock': Decimal('100.00'),
                'location': 'Ruang Server / IT',
                'last_purchase_price': Decimal('35000.00'),
                'notes': 'Manajemen kabel rak & instalasi'
            },
            {
                'item_code': 'CNS-FST-002',
                'name': 'Sekrup & Cage Nut Rak Server M6',
                'category': 'fastener',
                'brand': 'Indorack / Fortuna',
                'specification': 'Baut Rack M6 + Mur Cakar (Cage Nut) + Ring Plastik',
                'description': 'Baut pemasangan switch, router, server, dan patch panel pada rak 19 inci.',
                'base_unit': 'set',
                'purchase_unit': 'pack',
                'conversion_rate': Decimal('50.00'),
                'initial_stock': Decimal('100.00'),  # 2 pack
                'minimum_stock': Decimal('20.00'),
                'location': 'Ruang Server / IT',
                'last_purchase_price': Decimal('90000.00'),
                'notes': 'Mounting rack unit'
            },
            {
                'item_code': 'CNS-ELC-001',
                'name': 'Isolasi Listrik PVC Vinyl 3M Scotch Super 33+',
                'category': 'electrical',
                'brand': '3M',
                'specification': 'Black Vinyl Electrical Tape 3/4 in x 66 ft (19mm x 20.1m)',
                'description': 'Isolasi listrik tahan panas dan cuaca untuk penyambungan kabel.',
                'base_unit': 'roll',
                'purchase_unit': None,
                'conversion_rate': Decimal('1.00'),
                'initial_stock': Decimal('12.00'),
                'minimum_stock': Decimal('3.00'),
                'location': 'Workshop IT',
                'last_purchase_price': Decimal('45000.00'),
                'notes': 'Keperluan isolasi kabel listrik dan jaringan outdoor'
            },
            {
                'item_code': 'CNS-CAB-003',
                'name': 'Patch Cord UTP Cat6 1.5 Meter Factory Molded',
                'category': 'cable',
                'brand': 'Schneider / APC',
                'specification': 'Cat6 RJ45 to RJ45 Patch Cable 1.5m Blue Molded Boot',
                'description': 'Kabel patch cord pabrikan untuk koneksi dari patch panel ke switch.',
                'base_unit': 'pcs',
                'purchase_unit': None,
                'conversion_rate': Decimal('1.00'),
                'initial_stock': Decimal('25.00'),
                'minimum_stock': Decimal('10.00'),
                'location': 'Ruang Server / IT',
                'last_purchase_price': Decimal('35000.00'),
                'notes': 'Kabel patching rak distribusi'
            },
            {
                'item_code': 'CNS-CAB-004',
                'name': 'Kabel HDMI 2.0 High Speed 3 Meter',
                'category': 'cable',
                'brand': 'Vention',
                'specification': 'HDMI 2.0 4K@60Hz Nylon Braided Cable 3m',
                'description': 'Kabel display HDMI untuk ruang meeting, CCTV monitor, dan presentasi.',
                'base_unit': 'pcs',
                'purchase_unit': None,
                'conversion_rate': Decimal('1.00'),
                'initial_stock': Decimal('6.00'),
                'minimum_stock': Decimal('2.00'),
                'location': 'Ruang Server / IT',
                'last_purchase_price': Decimal('85000.00'),
                'notes': 'Kabel display operasional kantor & meeting'
            },
            {
                'item_code': 'CNS-CLN-001',
                'name': 'Precision Electronic Contact Cleaner 400ml',
                'category': 'cleaning',
                'brand': 'Philips / WD-40 Specialist',
                'specification': 'Fast Drying Non-Conductive Electronic Cleaner Spray',
                'description': 'Pembersih kontak soket RAM, PCIe, port switch, dan PCB.',
                'base_unit': 'can',
                'purchase_unit': None,
                'conversion_rate': Decimal('1.00'),
                'initial_stock': Decimal('4.00'),
                'minimum_stock': Decimal('2.00'),
                'location': 'Workshop IT',
                'last_purchase_price': Decimal('95000.00'),
                'notes': 'Kimia pembersih maintenance hardware'
            },
            # Item Stok Menipis (Low Stock)
            {
                'item_code': 'CNS-CAB-005',
                'name': 'Kabel Power AC C13 Heavy Duty 1.8m 3x1.5mm',
                'category': 'cable',
                'brand': 'APC / Schneider',
                'specification': 'AC Power Cord C13 to Schuko Plug 250V 16A 1.8 Meter',
                'description': 'Kabel power standar untuk server, switch, PDU, dan monitor kerja.',
                'base_unit': 'pcs',
                'purchase_unit': None,
                'conversion_rate': Decimal('1.00'),
                'initial_stock': Decimal('2.00'),
                'minimum_stock': Decimal('5.00'),
                'location': 'Ruang Server / IT',
                'last_purchase_price': Decimal('45000.00'),
                'notes': 'Stok menipis, perlu pengadaan ulang untuk rak server.'
            },
            {
                'item_code': 'CNS-BAT-001',
                'name': 'Baterai Kancing CMOS CR2032 3V Lithium Coin',
                'category': 'tools_acc',
                'brand': 'Panasonic',
                'specification': 'Lithium Coin Cell 3V CR2032 DL2032 225mAh',
                'description': 'Baterai backup BIOS/CMOS motherboard PC, laptop, dan kontroler PLC.',
                'base_unit': 'pcs',
                'purchase_unit': 'strip',
                'conversion_rate': Decimal('5.00'),
                'initial_stock': Decimal('3.00'),
                'minimum_stock': Decimal('10.00'),
                'location': 'Workshop IT - Laci Baterai',
                'last_purchase_price': Decimal('15000.00'),
                'notes': 'Sering digunakan untuk pergantian baterai motherboard lama.'
            },
            # Item Stok Habis (Out of Stock)
            {
                'item_code': 'CNS-CON-003',
                'name': 'RJ45 Modular Inline Coupler Barrel Female-to-Female Cat6',
                'category': 'connector',
                'brand': 'D-Link / Vention',
                'specification': 'Cat6 Shielded RJ45 Female to Female Keystone Coupler Adapter',
                'description': 'Penyambung barrel darurat untuk ekstensi kabel LAN tanpa crimping ulang.',
                'base_unit': 'pcs',
                'purchase_unit': 'pack',
                'conversion_rate': Decimal('10.00'),
                'initial_stock': Decimal('0.00'),
                'minimum_stock': Decimal('5.00'),
                'location': 'Workshop IT',
                'last_purchase_price': Decimal('25000.00'),
                'notes': 'Stok habis total, sedang diajukan pembelian ke vendor.'
            },
            {
                'item_code': 'CNS-CLN-002',
                'name': 'Compressed Air Duster Cleaner Can 400ml',
                'category': 'cleaning',
                'brand': 'Falcon Dust-Off',
                'specification': 'Gas aerosol pembersih debu bertekanan tinggi 400ml non-CFC',
                'description': 'Pembersih debu kipas heatsink, power supply, dan kisi-kisi radiator server.',
                'base_unit': 'can',
                'purchase_unit': None,
                'conversion_rate': Decimal('1.00'),
                'initial_stock': Decimal('0.00'),
                'minimum_stock': Decimal('4.00'),
                'location': 'Workshop IT',
                'last_purchase_price': Decimal('75000.00'),
                'notes': 'Stok habis, pending approval pengadaan logistik.'
            },
        ]

        created_count = 0
        for data in sample_items:
            item, created = ConsumableItem.objects.get_or_create(
                item_code=data['item_code'],
                defaults={
                    'name': data['name'],
                    'category': data['category'],
                    'brand': data['brand'],
                    'specification': data['specification'],
                    'description': data['description'],
                    'base_unit': data['base_unit'],
                    'purchase_unit': data['purchase_unit'],
                    'conversion_rate': data['conversion_rate'],
                    'stock_available': data['initial_stock'],
                    'minimum_stock': data['minimum_stock'],
                    'location': data['location'],
                    'last_purchase_price': data['last_purchase_price'],
                    'notes': data['notes'],
                }
            )

            if created:
                created_count += 1
                # Rekam mutasi awal di buku besar
                if data['initial_stock'] > 0:
                    ConsumableTransaction.objects.create(
                        transaction_code=f"TRX-IN-{data['item_code']}-INIT",
                        transaction_type='in',
                        item=item,
                        quantity=data['initial_stock'],
                        unit=data['base_unit'],
                        conversion_rate=Decimal('1.00'),
                        quantity_base=data['initial_stock'],
                        stock_before=Decimal('0.00'),
                        stock_after=data['initial_stock'],
                        source_destination='Stok Awal Terotorisasi',
                        performed_by=admin_user,
                        transaction_date=date.today(),
                        notes=f"Inisialisasi stok awal sistem: {data['initial_stock']} {data['base_unit']}."
                    )
                self.stdout.write(self.style.SUCCESS(f"[BARU] Consumable Item: {item.item_code} - {item.name}"))
            else:
                self.stdout.write(f"[ADA] Consumable Item: {item.item_code} - {item.name}")

        # Tambahkan transaksi mutasi keluar (pemakaian teknisi) sebagai sampel realistis
        emp_rayyan = Employee.objects.filter(name__icontains='Rayyan').first()
        unit_thinkpad = AssetUnit.objects.filter(unit_code='LNV-GEN12-001').first()

        # 1. Transaksi keluar Kabel Belden
        item_kabel = ConsumableItem.objects.filter(item_code='CNS-CAB-001').first()
        if item_kabel and not ConsumableTransaction.objects.filter(transaction_code='TRX-OUT-CNS-CAB-001-DEMO').exists():
            qty_out = Decimal('35.00')
            stock_before = item_kabel.stock_available
            stock_after = max(Decimal('0.00'), stock_before - qty_out)
            item_kabel.stock_available = stock_after
            item_kabel.save()

            ConsumableTransaction.objects.create(
                transaction_code='TRX-OUT-CNS-CAB-001-DEMO',
                transaction_type='out',
                item=item_kabel,
                quantity=qty_out,
                unit=item_kabel.base_unit,
                conversion_rate=Decimal('1.00'),
                quantity_base=qty_out,
                stock_before=stock_before,
                stock_after=stock_after,
                source_destination='Lantai 2 Kantor Administrasi & Finance',
                recipient_employee=emp_rayyan,
                ticket_number='WO-NET-202610-014',
                performed_by=admin_user,
                transaction_date=date.today(),
                notes='Penarikan kabel LAN drop point baru ruang meeting dan finance.'
            )
            self.stdout.write(self.style.SUCCESS("[BARU] Transaksi Keluar: 35 meter Kabel Cat6 Belden."))

        # 2. Transaksi keluar Konektor RJ45
        item_rj45 = ConsumableItem.objects.filter(item_code='CNS-CON-001').first()
        if item_rj45 and not ConsumableTransaction.objects.filter(transaction_code='TRX-OUT-CNS-CON-001-DEMO').exists():
            qty_out = Decimal('12.00')
            stock_before = item_rj45.stock_available
            stock_after = max(Decimal('0.00'), stock_before - qty_out)
            item_rj45.stock_available = stock_after
            item_rj45.save()

            ConsumableTransaction.objects.create(
                transaction_code='TRX-OUT-CNS-CON-001-DEMO',
                transaction_type='out',
                item=item_rj45,
                quantity=qty_out,
                unit=item_rj45.base_unit,
                conversion_rate=Decimal('1.00'),
                quantity_base=qty_out,
                stock_before=stock_before,
                stock_after=stock_after,
                source_destination='Workshop IT - Crimping Patch Cable',
                recipient_employee=emp_rayyan,
                ticket_number='WO-NET-202610-015',
                performed_by=admin_user,
                transaction_date=date.today(),
                notes='Crimping 6 buah patch cord custom untuk rack distribution switch.'
            )
            self.stdout.write(self.style.SUCCESS("[BARU] Transaksi Keluar: 12 pcs RJ45 Cat6."))

        # 3. Transaksi keluar Thermal Paste
        item_pasta = ConsumableItem.objects.filter(item_code='CNS-MNT-001').first()
        if item_pasta and not ConsumableTransaction.objects.filter(transaction_code='TRX-OUT-CNS-MNT-001-DEMO').exists():
            qty_out = Decimal('1.00')
            stock_before = item_pasta.stock_available
            stock_after = max(Decimal('0.00'), stock_before - qty_out)
            item_pasta.stock_available = stock_after
            item_pasta.save()

            ConsumableTransaction.objects.create(
                transaction_code='TRX-OUT-CNS-MNT-001-DEMO',
                transaction_type='out',
                item=item_pasta,
                quantity=qty_out,
                unit=item_pasta.base_unit,
                conversion_rate=Decimal('1.00'),
                quantity_base=qty_out,
                stock_before=stock_before,
                stock_after=stock_after,
                source_destination='Maintenance Laptop Karyawan',
                recipient_employee=emp_rayyan,
                related_unit=unit_thinkpad,
                ticket_number='WO-HW-202610-008',
                performed_by=admin_user,
                transaction_date=date.today(),
                notes='Repasting CPU dan GPU laptop operasional ThinkPad T14.'
            )
            self.stdout.write(self.style.SUCCESS("[BARU] Transaksi Keluar: 1 tube Thermal Paste MX-4."))

        self.stdout.write(self.style.SUCCESS(f"Selesai! Berhasil menambahkan {created_count} item consumable baru."))
