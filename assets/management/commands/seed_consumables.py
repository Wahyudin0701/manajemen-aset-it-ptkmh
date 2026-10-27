from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from assets.models import ConsumableItem, ConsumableTransaction
from datetime import date


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
                'conversion_rate': 305.00,
                'initial_stock': 610.00,  # 2 roll
                'minimum_stock': 100.00,
                'location': 'Gudang Induk (GI)',
                'last_purchase_price': 1850000,
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
                'conversion_rate': 1000.00,
                'initial_stock': 1000.00,  # 1 roll
                'minimum_stock': 200.00,
                'location': 'Gudang Induk (GI)',
                'last_purchase_price': 1200000,
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
                'conversion_rate': 100.00,
                'initial_stock': 150.00,
                'minimum_stock': 30.00,
                'location': 'Ruang Server / IT',
                'last_purchase_price': 250000,
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
                'conversion_rate': 50.00,
                'initial_stock': 50.00,
                'minimum_stock': 15.00,
                'location': 'Ruang Server / IT',
                'last_purchase_price': 175000,
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
                'conversion_rate': 1.00,
                'initial_stock': 8.00,
                'minimum_stock': 2.00,
                'location': 'Workshop IT',
                'last_purchase_price': 115000,
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
                'conversion_rate': 100.00,
                'initial_stock': 400.00,  # 4 pack
                'minimum_stock': 100.00,
                'location': 'Ruang Server / IT',
                'last_purchase_price': 35000,
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
                'conversion_rate': 50.00,
                'initial_stock': 100.00,  # 2 pack
                'minimum_stock': 20.00,
                'location': 'Ruang Server / IT',
                'last_purchase_price': 90000,
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
                'conversion_rate': 1.00,
                'initial_stock': 12.00,
                'minimum_stock': 3.00,
                'location': 'Workshop IT',
                'last_purchase_price': 45000,
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
                'conversion_rate': 1.00,
                'initial_stock': 25.00,
                'minimum_stock': 10.00,
                'location': 'Ruang Server / IT',
                'last_purchase_price': 35000,
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
                'conversion_rate': 1.00,
                'initial_stock': 6.00,
                'minimum_stock': 2.00,
                'location': 'Ruang Server / IT',
                'last_purchase_price': 85000,
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
                'conversion_rate': 1.00,
                'initial_stock': 4.00,
                'minimum_stock': 2.00,
                'location': 'Workshop IT',
                'last_purchase_price': 95000,
                'notes': 'Kimia pembersih maintenance hardware'
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
                        conversion_rate=1.00,
                        quantity_base=data['initial_stock'],
                        stock_before=0.00,
                        stock_after=data['initial_stock'],
                        source_destination='Stok Awal Terotorisasi',
                        performed_by=admin_user,
                        transaction_date=date.today(),
                        notes=f"Inisialisasi stok awal sistem: {data['initial_stock']} {data['base_unit']}."
                    )
                self.stdout.write(self.style.SUCCESS(f"[BARU] Consumable Item: {item.item_code} - {item.name}"))
            else:
                self.stdout.write(f"[ADA] Consumable Item: {item.item_code} - {item.name}")

        self.stdout.write(self.style.SUCCESS(f"Selesai! Berhasil menambahkan {created_count} item consumable baru."))
