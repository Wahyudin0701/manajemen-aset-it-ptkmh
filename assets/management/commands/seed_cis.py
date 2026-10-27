from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from assets.models import ConfigurationItem, CIHistory, AssetUnit, Employee
from datetime import date, timedelta
from decimal import Decimal


class Command(BaseCommand):
    help = 'Mengisi sampel data dummy Configuration Item (CI) dan riwayatnya untuk IT Asset Management'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Memeriksa dan mengisi data dummy Configuration Item (CI)..."))

        admin_user = User.objects.filter(is_superuser=True).first()
        today = date.today()

        # Dapatkan referensi unit dan karyawan yang ada di sistem
        unit_thinkpad = AssetUnit.objects.filter(unit_code='LNV-GEN12-001').first()
        unit_router = AssetUnit.objects.filter(unit_code='TPL-01-001').first()
        unit_acer2 = AssetUnit.objects.filter(unit_code='ACR-GEN11-002').first()
        unit_acer3 = AssetUnit.objects.filter(unit_code='ACR-GEN11-003').first()

        emp_rayyan = Employee.objects.filter(name__icontains='Rayyan').first()
        emp_budi = Employee.objects.filter(name__icontains='Budi').first()
        emp_fallback = Employee.objects.first()

        sample_cis = [
            # 1. STORAGE
            {
                'ci_code': 'CI-SSD-001',
                'name': 'Samsung SSD 980 PRO 1TB NVMe M.2 PCIe 4.0',
                'category': 'storage',
                'brand': 'Samsung',
                'model_series': '980 PRO 1TB (MZ-V8P1T0BW)',
                'serial_number': 'S6B1NF0R102938A',
                'specifications': 'Read up to 7,000 MB/s, Write up to 5,000 MB/s, V-NAND 3-bit MLC, PCIe Gen 4.0 x4',
                'status': 'in_use',
                'condition': 'good',
                'installed_on': unit_thinkpad,
                'assigned_to': None,
                'location': 'Terpasang di Laptop Rayyan Adam',
                'purchase_date': today - timedelta(days=240),
                'warranty_expiry': today + timedelta(days=850),
                'price': Decimal('2150000.00'),
                'notes': 'Upgrade storage utama workstation dev.',
                'history_action': 'installed',
                'history_notes': 'Dipasang sebagai upgrade SSD internal ThinkPad LNV-GEN12-001.'
            },
            {
                'ci_code': 'CI-SSD-002',
                'name': 'Kingston NV2 SSD 500GB NVMe PCIe 4.0 M.2',
                'category': 'storage',
                'brand': 'Kingston',
                'model_series': 'NV2 500G (SNV2S/500G)',
                'serial_number': '50026B7685930211',
                'specifications': 'Read 3,500 MB/s, Write 2,100 MB/s, Form Factor M.2 2280',
                'status': 'available',
                'condition': 'new',
                'installed_on': None,
                'assigned_to': None,
                'location': 'Gudang IT - Lemari Sparepart Rak 2',
                'purchase_date': today - timedelta(days=45),
                'warranty_expiry': today + timedelta(days=1050),
                'price': Decimal('620000.00'),
                'notes': 'Stok cadangan untuk penggantian darurat laptop operasional.',
                'history_action': 'created',
                'history_notes': 'Penerimaan barang pengadaan sparepart Q4.'
            },
            {
                'ci_code': 'CI-HDD-001',
                'name': 'Seagate IronWolf 4TB NAS Internal Hard Drive 3.5"',
                'category': 'storage',
                'brand': 'Seagate',
                'model_series': 'IronWolf ST4000VN006',
                'serial_number': 'WSD389102377',
                'specifications': '5400 RPM, 256MB Cache, SATA 6.0Gb/s 3.5", AgileArray Technology',
                'status': 'available',
                'condition': 'good',
                'installed_on': None,
                'assigned_to': None,
                'location': 'Ruang Server - Rak Storage Backup',
                'purchase_date': today - timedelta(days=180),
                'warranty_expiry': today + timedelta(days=550),
                'price': Decimal('1750000.00'),
                'notes': 'HDD spare untuk array Synology NAS Ruang Server.',
                'history_action': 'created',
                'history_notes': 'Penyimpanan cadangan cold spare NAS server.'
            },
            {
                'ci_code': 'CI-SSD-003',
                'name': 'Western Digital Blue 2.5" SATA SSD 500GB',
                'category': 'storage',
                'brand': 'Western Digital',
                'model_series': 'WD Blue SA510',
                'serial_number': 'WD-WCC4N728190',
                'specifications': 'SATA III 6 Gb/s 2.5 Inch 7mm, Read up to 560 MB/s',
                'status': 'under_inspection',
                'condition': 'fair',
                'installed_on': None,
                'assigned_to': None,
                'location': 'Workshop IT - Meja Diagnostic',
                'purchase_date': today - timedelta(days=400),
                'warranty_expiry': today + timedelta(days=300),
                'price': Decimal('750000.00'),
                'notes': 'Dilepas dari PC Administrasi karena ada laporan I/O error sporadis.',
                'history_action': 'status_change',
                'history_notes': 'Sedang dilakukan health test SMART diagnostic sektor.'
            },
            {
                'ci_code': 'CI-HDD-002',
                'name': 'WD Black 1TB 2.5" HDD SATA 7200 RPM',
                'category': 'storage',
                'brand': 'Western Digital',
                'model_series': 'WD10SPSX',
                'serial_number': 'WX31A6729012',
                'specifications': '7200 RPM, 64MB Cache, SATA 6Gb/s',
                'status': 'retired',
                'condition': 'damaged',
                'installed_on': None,
                'assigned_to': None,
                'location': 'Gudang Limbah IT - Kotak Scrap',
                'purchase_date': today - timedelta(days=1200),
                'warranty_expiry': today - timedelta(days=100),
                'price': Decimal('950000.00'),
                'notes': 'Mengalami bad sector parah dan unrecoverable read error. Selesai diaudit scrap.',
                'history_action': 'retired',
                'history_notes': 'Dipensiunkan dan didekripsikan untuk dimusnahkan sesuai SOP IT security.'
            },

            # 2. MEMORY (RAM)
            {
                'ci_code': 'CI-RAM-001',
                'name': 'Corsair Vengeance SODIMM DDR4 16GB 3200MHz',
                'category': 'memory',
                'brand': 'Corsair',
                'model_series': 'CMSX16GX4M1A3200C22',
                'serial_number': 'CRS-16GB-829103',
                'specifications': '16GB DDR4 SODIMM 3200MHz CL22 1.2V Non-ECC',
                'status': 'in_use',
                'condition': 'good',
                'installed_on': unit_acer2,
                'assigned_to': None,
                'location': 'Terpasang di Laptop Acer Legion ACR-GEN11-002',
                'purchase_date': today - timedelta(days=190),
                'warranty_expiry': today + timedelta(days=900),
                'price': Decimal('750000.00'),
                'notes': 'Penambahan RAM laptop grafis Rayyan Adam.',
                'history_action': 'installed',
                'history_notes': 'Pemasangan ekspansi RAM di slot kedua laptop.'
            },
            {
                'ci_code': 'CI-RAM-002',
                'name': 'Kingston Fury Beast DDR4 16GB (2x8GB) 3200MHz',
                'category': 'memory',
                'brand': 'Kingston',
                'model_series': 'KF432C16BBK2/16',
                'serial_number': 'KF-DDR4-992101',
                'specifications': 'Dual Channel Kit 2x8GB DDR4-3200 CL16-18-18 1.35V Black Heatsink',
                'status': 'available',
                'condition': 'new',
                'installed_on': None,
                'assigned_to': None,
                'location': 'Gudang IT - Laci RAM & Storage',
                'purchase_date': today - timedelta(days=30),
                'warranty_expiry': today + timedelta(days=1400),
                'price': Decimal('890000.00'),
                'notes': 'Stok cadangan untuk PC engineering GIS.',
                'history_action': 'created',
                'history_notes': 'Registrasi item komponen baru di gudang.'
            },
            {
                'ci_code': 'CI-RAM-003',
                'name': 'Samsung DDR4 8GB 2666MHz SODIMM Original',
                'category': 'memory',
                'brand': 'Samsung',
                'model_series': 'M471A1K43CB1-CTD',
                'serial_number': 'SAM-D4-738192',
                'specifications': '8GB DDR4 2666V SODIMM 1Rx8 CL19 1.2V',
                'status': 'available',
                'condition': 'fair',
                'installed_on': None,
                'assigned_to': None,
                'location': 'Gudang IT - Laci RAM Bekas Pakai',
                'purchase_date': today - timedelta(days=500),
                'warranty_expiry': today + timedelta(days=200),
                'price': Decimal('420000.00'),
                'notes': 'RAM copotan laptop Lenovo lama, kondisi normal 100% lulus MemTest86.',
                'history_action': 'returned',
                'history_notes': 'Dikembalikan ke inventaris gudang setelah laptop donor diganti.'
            },

            # 3. PROCESSOR & MOTHERBOARD
            {
                'ci_code': 'CI-CPU-001',
                'name': 'Intel Core i7-12700K Processor 25M Cache up to 5.00 GHz',
                'category': 'processor',
                'brand': 'Intel',
                'model_series': 'Core i7 12th Gen (BX8071512700K)',
                'serial_number': 'V219B82918231',
                'specifications': '12 Cores (8P + 4E), 20 Threads, LGA1700, Intel UHD Graphics 770',
                'status': 'available',
                'condition': 'good',
                'installed_on': None,
                'assigned_to': None,
                'location': 'Ruang Server - Brankas Sparepart IT',
                'purchase_date': today - timedelta(days=150),
                'warranty_expiry': today + timedelta(days=950),
                'price': Decimal('5200000.00'),
                'notes': 'CPU cadangan workstation server SCADA monitoring.',
                'history_action': 'created',
                'history_notes': 'Barang pengadaan darurat server SCADA.'
            },
            {
                'ci_code': 'CI-MBD-001',
                'name': 'ASUS TUF GAMING B660M-PLUS WIFI D4',
                'category': 'motherboard',
                'brand': 'ASUS',
                'model_series': 'TUF B660M-PLUS D4',
                'serial_number': 'M5N0CX1928371',
                'specifications': 'LGA 1700, 4x DDR4, 2x M.2 PCIe 4.0, Realtek 2.5Gb LAN, Intel WiFi 6',
                'status': 'available',
                'condition': 'good',
                'installed_on': None,
                'assigned_to': None,
                'location': 'Gudang IT - Rak Motherboard',
                'purchase_date': today - timedelta(days=150),
                'warranty_expiry': today + timedelta(days=950),
                'price': Decimal('2650000.00'),
                'notes': 'Pasangan sparepart motherboard untuk workstation SCADA.',
                'history_action': 'created',
                'history_notes': 'Disimpan sebagai unit hot-swap motherboard.'
            },

            # 4. GPU & GRAPHIC CARD
            {
                'ci_code': 'CI-GPU-001',
                'name': 'ASUS Dual GeForce RTX 3060 V2 OC Edition 12GB GDDR6',
                'category': 'gpu',
                'brand': 'ASUS',
                'model_series': 'DUAL-RTX3060-O12G-V2',
                'serial_number': '21098471029381',
                'specifications': '12GB GDDR6, 192-bit, PCIe 4.0, 3x DisplayPort 1.4a, 1x HDMI 2.1',
                'status': 'available',
                'condition': 'good',
                'installed_on': None,
                'assigned_to': None,
                'location': 'Ruang Server - Rak Sparepart Hardware',
                'purchase_date': today - timedelta(days=220),
                'warranty_expiry': today + timedelta(days=500),
                'price': Decimal('4850000.00'),
                'notes': 'GPU untuk kebutuhan rendering 3D model DAM & Turbin Hydro.',
                'history_action': 'created',
                'history_notes': 'Disiapkan untuk workstation sipil engineering.'
            },

            # 5. PERIPHERALS (Monitor, Keyboard, Mouse, Scanner, etc.)
            {
                'ci_code': 'CI-PER-001',
                'name': 'Monitor Dell 24" P2422H FHD IPS Ultra-Thin Bezel',
                'category': 'peripheral',
                'brand': 'Dell',
                'model_series': 'P2422H',
                'serial_number': 'CN-08W91-72872-91A',
                'specifications': '23.8" IPS 1920x1080 @60Hz, Pivot/Tilt/Swivel Height-Adjustable, VGA, HDMI, DP, USB Hub',
                'status': 'in_use',
                'condition': 'good',
                'installed_on': None,
                'assigned_to': emp_rayyan or emp_fallback,
                'location': 'Ruang IT Development / Workstation Rayyan',
                'purchase_date': today - timedelta(days=320),
                'warranty_expiry': today + timedelta(days=750),
                'price': Decimal('2850000.00'),
                'notes': 'Monitor sekunder dual-display untuk pemantauan sistem dan coding.',
                'history_action': 'assigned',
                'history_notes': 'Dialokasikan langsung ke Rayyan Adam sebagai monitor sekunder.'
            },
            {
                'ci_code': 'CI-PER-002',
                'name': 'Logitech MK270 Wireless Keyboard & Mouse Combo',
                'category': 'peripheral',
                'brand': 'Logitech',
                'model_series': 'MK270 Wireless Combo',
                'serial_number': '2142LZ028190',
                'specifications': '2.4GHz Wireless with Nano USB Receiver, Spill-resistant keyboard, 3-button optical mouse',
                'status': 'in_use',
                'condition': 'good',
                'installed_on': None,
                'assigned_to': emp_budi or emp_fallback,
                'location': 'Ruang Finance & Accounting',
                'purchase_date': today - timedelta(days=120),
                'warranty_expiry': today + timedelta(days=240),
                'price': Decimal('325000.00'),
                'notes': 'Perangkat input wireless operasional.',
                'history_action': 'assigned',
                'history_notes': 'Dialokasikan kepada Budi Santoso untuk laptop kerja.'
            },
            {
                'ci_code': 'CI-PER-003',
                'name': 'Monitor LG 27" UltraGear 27GP850-B Nano IPS QHD 165Hz',
                'category': 'peripheral',
                'brand': 'LG',
                'model_series': '27GP850-B',
                'serial_number': '208NTPW928173',
                'specifications': '27" Nano IPS 2560x1440 165Hz (O/C 180Hz) 1ms GtG, HDR400, G-Sync Compatible',
                'status': 'available',
                'condition': 'new',
                'installed_on': None,
                'assigned_to': None,
                'location': 'Gudang IT - Rak Monitor Box Original',
                'purchase_date': today - timedelta(days=14),
                'warranty_expiry': today + timedelta(days=1080),
                'price': Decimal('5400000.00'),
                'notes': 'Monitor baru untuk workstation simulator dispatch PLTA Kerinci.',
                'history_action': 'created',
                'history_notes': 'Penerimaan unit monitor baru dari vendor LG.'
            },
            {
                'ci_code': 'CI-PER-004',
                'name': 'Headset Jabra Evolve 20 Stereo USB & 3.5mm Noise Cancelling',
                'category': 'peripheral',
                'brand': 'Jabra',
                'model_series': 'Evolve 20 MS Stereo',
                'serial_number': 'JBR-EV20-19284',
                'specifications': 'Noise-cancelling microphone, USB-A and 3.5mm jack connectivity, In-line call controller',
                'status': 'available',
                'condition': 'new',
                'installed_on': None,
                'assigned_to': None,
                'location': 'Gudang IT - Lemari Aksesori & Audio',
                'purchase_date': today - timedelta(days=40),
                'warranty_expiry': today + timedelta(days=690),
                'price': Decimal('680000.00'),
                'notes': 'Headset standar untuk video conference manajemen.',
                'history_action': 'created',
                'history_notes': 'Stok baru pengadaan fasilitas meeting online.'
            },
            {
                'ci_code': 'CI-PER-005',
                'name': 'Honeywell Voyager 1472g Wireless 2D Barcode Scanner',
                'category': 'peripheral',
                'brand': 'Honeywell',
                'model_series': 'Voyager 1472g 2D',
                'serial_number': '21289B00192',
                'specifications': 'Area Image 2D (QR Code & Barcode), Bluetooth Range up to 30m, Cradle USB Base',
                'status': 'under_inspection',
                'condition': 'good',
                'installed_on': None,
                'assigned_to': None,
                'location': 'Workshop IT - Meja Service',
                'purchase_date': today - timedelta(days=360),
                'warranty_expiry': today + timedelta(days=370),
                'price': Decimal('3200000.00'),
                'notes': 'Scanner barcode gudang logistik, sedang diuji sinkronisasi Bluetooth dan daya baterai.',
                'history_action': 'status_change',
                'history_notes': 'Pemeriksaan performa baterai dan pembacaan barcode damaged.'
            },

            # 6. NETWORK COMPONENTS (SFP, NIC, Adapter)
            {
                'ci_code': 'CI-NET-001',
                'name': 'Cisco 10GBASE-SR SFP+ Transceiver Module',
                'category': 'network',
                'brand': 'Cisco',
                'model_series': 'SFP-10G-SR',
                'serial_number': 'FNS22190A2B',
                'specifications': '10GBASE-SR 850nm Multimode Fiber LC Duplex up to 300m DOM support',
                'status': 'available',
                'condition': 'new',
                'installed_on': None,
                'assigned_to': None,
                'location': 'Ruang Server - Laci Fiber Transceiver',
                'purchase_date': today - timedelta(days=90),
                'warranty_expiry': today + timedelta(days=1000),
                'price': Decimal('1450000.00'),
                'notes': 'Modul SFP+ 10Gbps untuk interkoneksi switch core Cisco Catalyst.',
                'history_action': 'created',
                'history_notes': 'Stok modul optik cadangan link switch backbone.'
            },
            {
                'ci_code': 'CI-NET-002',
                'name': 'TP-Link UE300 USB 3.0 to Gigabit Ethernet Adapter',
                'category': 'network',
                'brand': 'TP-Link',
                'model_series': 'UE300 Foldable',
                'serial_number': '221B8910293',
                'specifications': 'USB 3.0 to RJ45 Gigabit Ethernet 10/100/1000Mbps, Plug and Play Windows/macOS',
                'status': 'available',
                'condition': 'good',
                'installed_on': None,
                'assigned_to': None,
                'location': 'Gudang IT - Laci Adapter & Converter',
                'purchase_date': today - timedelta(days=60),
                'warranty_expiry': today + timedelta(days=300),
                'price': Decimal('165000.00'),
                'notes': 'Adapter LAN eksternal untuk laptop tipis yang tidak memiliki port RJ45 bawaan.',
                'history_action': 'created',
                'history_notes': 'Penerimaan inventaris toolkit teknisi.'
            },
            {
                'ci_code': 'CI-NET-003',
                'name': 'MikroTik S-85DLC05D SFP Transceiver 1.25G 850nm MultiMode',
                'category': 'network',
                'brand': 'MikroTik',
                'model_series': 'S-85DLC05D',
                'serial_number': 'MT-SFP-091823',
                'specifications': '1.25G SFP, 850nm Dual LC connector, up to 550m, DDM',
                'status': 'in_use',
                'condition': 'good',
                'installed_on': unit_router,
                'assigned_to': None,
                'location': 'Terpasang pada Router TPL-01-001',
                'purchase_date': today - timedelta(days=210),
                'warranty_expiry': today + timedelta(days=155),
                'price': Decimal('320000.00'),
                'notes': 'Modul uplink fiber optik menuju switch intake.',
                'history_action': 'installed',
                'history_notes': 'Dipasang pada port SFP router jaringan.'
            },

            # 7. POWER & UPS
            {
                'ci_code': 'CI-PWR-001',
                'name': 'UPS APC Back-UPS Pro BR1500GI 1500VA / 865W AVR LCD',
                'category': 'power',
                'brand': 'APC / Schneider Electric',
                'model_series': 'BR1500GI',
                'serial_number': '3B1928X01928',
                'specifications': '1500VA/865Watts, Line Interactive, AVR, LCD Interface, 6x IEC Battery Backup, Data line surge protection',
                'status': 'in_use',
                'condition': 'good',
                'installed_on': None,
                'assigned_to': emp_rayyan or emp_fallback,
                'location': 'Ruang Control Room & SCADA IT',
                'purchase_date': today - timedelta(days=300),
                'warranty_expiry': today + timedelta(days=430),
                'price': Decimal('5650000.00'),
                'notes': 'Pencatu daya darurat workstation monitor utama PLTA.',
                'history_action': 'assigned',
                'history_notes': 'Ditempatkan di workstation SCADA untuk backup listrik darurat.'
            },
            {
                'ci_code': 'CI-PWR-002',
                'name': 'Corsair RM750e 750W 80 Plus Gold Fully Modular Power Supply',
                'category': 'power',
                'brand': 'Corsair',
                'model_series': 'CP-9020262-NA (RMe Series)',
                'serial_number': 'CRS-PSU-750E-9102',
                'specifications': '750 Watt, 80 PLUS Gold Certified, ATX 3.0 & PCIe 5.0 Ready, Zero RPM Fan Mode, 105°C Capacitors',
                'status': 'available',
                'condition': 'new',
                'installed_on': None,
                'assigned_to': None,
                'location': 'Gudang IT - Rak Power Supply',
                'purchase_date': today - timedelta(days=50),
                'warranty_expiry': today + timedelta(days=1770),
                'price': Decimal('1850000.00'),
                'notes': 'PSU cadangan untuk PC rendering teknik dan PC server lokal.',
                'history_action': 'created',
                'history_notes': 'Penerimaan stok unit PSU high-efficiency.'
            },
            {
                'ci_code': 'CI-PWR-003',
                'name': 'APC Replacement Battery Cartridge RBC17 12V 9Ah',
                'category': 'power',
                'brand': 'APC',
                'model_series': 'APCRBC17',
                'serial_number': 'RBC17-202610-098',
                'specifications': '12V 9Ah VRLA Maintenance-Free Sealed Lead-Acid battery with suspended electrolyte',
                'status': 'under_repair',
                'condition': 'fair',
                'installed_on': None,
                'assigned_to': None,
                'location': 'Workshop IT - Lemari Charger & Baterai',
                'purchase_date': today - timedelta(days=420),
                'warranty_expiry': today - timedelta(days=55),
                'price': Decimal('650000.00'),
                'notes': 'Sedang dilakukan conditioning & re-charging cycle sebelum dipasang kembali.',
                'history_action': 'repair_in',
                'history_notes': 'Baterai mengalami penurunan kapasitas retensi daya; dalam perbaikan uji voltase.'
            },
        ]

        created_count = 0
        updated_count = 0

        for item_data in sample_cis:
            history_action = item_data.pop('history_action')
            history_notes = item_data.pop('history_notes')

            ci, created = ConfigurationItem.objects.get_or_create(
                ci_code=item_data['ci_code'],
                defaults=item_data
            )

            if not created:
                # Perbarui data jika sudah ada agar tetap up-to-date
                for key, val in item_data.items():
                    setattr(ci, key, val)
                ci.save()
                updated_count += 1
                self.stdout.write(f"[DIPERBARUI] CI: {ci.ci_code} - {ci.name}")
            else:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"[BARU] CI: {ci.ci_code} - {ci.name}"))

            # Buat entri riwayat jika belum ada riwayat untuk aksi ini
            if not ci.history.filter(action=history_action).exists():
                CIHistory.objects.create(
                    ci=ci,
                    action=history_action,
                    related_unit=ci.installed_on,
                    related_employee=ci.assigned_to,
                    performed_by=admin_user,
                    notes=history_notes
                )

        self.stdout.write(self.style.SUCCESS(
            f"\nSelesai! Berhasil memproses Configuration Items: {created_count} baru, {updated_count} diperbarui."
        ))
