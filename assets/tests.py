import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from assets.models import (
    Employee, Category, Asset, AssetUnit, UnitLog, AssetAssignment,
    ConfigurationItem, CIHistory, ConsumableItem, ConsumableTransaction
)
from assets.views import validate_uploaded_document


class ModelConstraintTests(TestCase):
    """Pengujian aturan model dasar dan constraint data."""

    def setUp(self):
        self.category = Category.objects.create(name="Aset Karyawan")
        self.employee = Employee.objects.create(nik="EMP001", name="Budi Santoso", position="IT Support")

    def test_employee_creation_and_str(self):
        self.assertEqual(str(self.employee), "EMP001 - Budi Santoso")
        self.assertEqual(self.employee.position, "IT Support")

    def test_category_creation_and_str(self):
        self.assertEqual(str(self.category), "Aset Karyawan")

    def test_asset_and_unit_creation(self):
        asset = Asset.objects.create(
            category=self.category,
            asset_code="NB-LENOVO",
            name="ThinkPad T14",
            brand="Lenovo",
            uom="Unit",
            qty=1
        )
        unit = AssetUnit.objects.create(
            asset=asset,
            unit_code="NB-LENOVO-001",
            status="tersedia"
        )
        self.assertEqual(str(asset), "NB-LENOVO - ThinkPad T14")
        self.assertEqual(str(unit), "NB-LENOVO-001")
        self.assertIsNotNone(unit.id_uuid)


class AssetSyncLogicTests(TestCase):
    """Pengujian logika otomatis sinkronisasi kode unit saat kode aset induk diubah."""

    def setUp(self):
        self.category = Category.objects.create(name="Aset Network")
        self.asset = Asset.objects.create(
            category=self.category,
            asset_code="SW-CISCO",
            name="Switch Cisco 24 Port"
        )
        self.unit1 = AssetUnit.objects.create(asset=self.asset, unit_code="SW-CISCO-001")
        self.unit2 = AssetUnit.objects.create(asset=self.asset, unit_code="SW-CISCO-002")

    def test_asset_code_update_propagates_to_units(self):
        # Mengubah kode aset induk dari SW-CISCO menjadi SW-CORE
        self.asset.asset_code = "SW-CORE"
        self.asset.save()

        self.unit1.refresh_from_db()
        self.unit2.refresh_from_db()

        self.assertEqual(self.unit1.unit_code, "SW-CORE-001")
        self.assertEqual(self.unit2.unit_code, "SW-CORE-002")

        # Memastikan UnitLog tercatat untuk pembaruan kode otomatis
        logs = UnitLog.objects.filter(unit=self.unit1)
        self.assertTrue(logs.filter(notes__contains="diperbarui otomatis").exists())


class SecurityAndAccessControlTests(TestCase):
    """Pengujian kontrol akses dan proteksi autentikasi."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testadmin", password="password123")
        self.category = Category.objects.create(name="Aset Karyawan")
        self.asset = Asset.objects.create(category=self.category, asset_code="PC-DELL", name="OptiPlex 7090")
        self.unit = AssetUnit.objects.create(asset=self.asset, unit_code="PC-DELL-001")

    def test_anonymous_access_to_dashboard_redirects_to_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_anonymous_access_to_asset_list_redirects_to_login(self):
        response = self.client.get(reverse('asset_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_asset_add_anonymous_access_is_blocked(self):
        """Verifikasi bahwa bug SEC-001 / TD-001 tertutup: POST /aset/add/ tanpa login wajib ditolak."""
        payload = {
            'category': self.category.id,
            'asset_code': 'MOU-LOGI',
            'name': 'Mouse Logitech B100',
            'brand': 'Logitech',
            'uom': 'Pcs'
        }
        response = self.client.post(reverse('asset_add'), data=payload)
        # Wajib di-redirect ke login (302) dan data TIDAK boleh tersimpan
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
        self.assertFalse(Asset.objects.filter(asset_code="MOU-LOGI").exists())

    def test_authenticated_user_can_access_dashboard(self):
        self.client.login(username="testadmin", password="password123")
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_public_qr_and_public_unit_detail_accessible_anonymously(self):
        """Halaman publik dan gambar QR code memang dirancang untuk scan publik."""
        qr_url = reverse('unit_qr_code', kwargs={'uuid': self.unit.id_uuid})
        detail_url = reverse('unit_public_detail', kwargs={'uuid': self.unit.id_uuid})

        res_qr = self.client.get(qr_url)
        self.assertEqual(res_qr.status_code, 200)
        self.assertEqual(res_qr['Content-Type'], 'image/png')

        res_detail = self.client.get(detail_url)
        self.assertEqual(res_detail.status_code, 200)


class DistributionWorkflowTests(TestCase):
    """Pengujian siklus distribusi serah terima, mutasi, dan pengembalian aset."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testadmin", password="password123")
        self.client.login(username="testadmin", password="password123")

        self.category = Category.objects.create(name="Aset Karyawan")
        self.asset = Asset.objects.create(category=self.category, asset_code="NB-DELL", name="Dell Latitude 5420")
        self.unit = AssetUnit.objects.create(asset=self.asset, unit_code="NB-DELL-001", status="tersedia")

        self.emp1 = Employee.objects.create(nik="K001", name="Ahmad")
        self.emp2 = Employee.objects.create(nik="K002", name="Bambang")

    def test_handover_flow(self):
        """Serah terima unit tersedia kepada karyawan."""
        response = self.client.post(reverse('distribusi_handover'), data={
            'unit': self.unit.id,
            'employee': self.emp1.id,
            'assigned_date': '2026-10-26',
            'notes': 'Penyerahan laptop kerja baru'
        })
        self.assertEqual(response.status_code, 302)

        self.unit.refresh_from_db()
        self.assertEqual(self.unit.status, 'digunakan')
        self.assertEqual(self.unit.assigned_to, self.emp1)

        assignment = AssetAssignment.objects.filter(unit=self.unit, type='handover').first()
        self.assertIsNotNone(assignment)
        self.assertEqual(assignment.employee, self.emp1)
        self.assertEqual(assignment.status, 'aktif')

        # UnitLog harus tercatat
        log = UnitLog.objects.filter(unit=self.unit, action='assigned').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.employee, self.emp1)

    def test_mutation_flow(self):
        """Mutasi unit dari karyawan 1 ke karyawan 2."""
        # Setup handover awal
        self.unit.status = 'digunakan'
        self.unit.assigned_to = self.emp1
        self.unit.save()
        AssetAssignment.objects.create(
            type='handover',
            unit=self.unit,
            employee=self.emp1,
            assigned_date='2026-10-01',
            status='aktif'
        )

        response = self.client.post(reverse('distribusi_mutation'), data={
            'unit': self.unit.id,
            'employee': self.emp2.id,
            'assigned_date': '2026-10-26',
            'notes': 'Mutasi departemen'
        })
        self.assertEqual(response.status_code, 302)

        self.unit.refresh_from_db()
        self.assertEqual(self.unit.assigned_to, self.emp2)

        # Assignment lama harus tertutup
        old_assignment = AssetAssignment.objects.filter(unit=self.unit, type='handover').first()
        self.assertEqual(old_assignment.status, 'dikembalikan')
        self.assertIsNotNone(old_assignment.returned_date)

        # Assignment mutasi baru harus aktif
        new_assignment = AssetAssignment.objects.filter(unit=self.unit, type='mutation').first()
        self.assertEqual(new_assignment.from_employee, self.emp1)
        self.assertEqual(new_assignment.employee, self.emp2)
        self.assertEqual(new_assignment.status, 'aktif')

    def test_return_flow(self):
        """Pengembalian unit ke gudang dan pembaruan status transaksi."""
        self.unit.status = 'digunakan'
        self.unit.assigned_to = self.emp1
        self.unit.save()
        active_assignment = AssetAssignment.objects.create(
            type='handover',
            unit=self.unit,
            employee=self.emp1,
            assigned_date='2026-10-01',
            status='aktif'
        )

        response = self.client.post(reverse('distribusi_return'), data={
            'unit': self.unit.id,
            'assigned_date': '2026-10-26',
            'notes': 'Resign'
        })
        self.assertEqual(response.status_code, 302)

        self.unit.refresh_from_db()
        self.assertEqual(self.unit.status, 'tersedia')
        self.assertIsNone(self.unit.assigned_to)

        # Assignment aktif harus tertutup
        active_assignment.refresh_from_db()
        self.assertEqual(active_assignment.status, 'dikembalikan')
        self.assertEqual(str(active_assignment.returned_date), '2026-10-26')

        # Transaksi return harus berstatus dikembalikan
        return_assignment = AssetAssignment.objects.filter(unit=self.unit, type='return').first()
        self.assertEqual(return_assignment.status, 'dikembalikan')
        self.assertEqual(str(return_assignment.returned_date), '2026-10-26')


class EmployeeManagementTests(TestCase):
    """Pengujian master karyawan dan proteksi penghapusan."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testadmin", password="password123")
        self.client.login(username="testadmin", password="password123")

        self.category = Category.objects.create(name="Aset Karyawan")
        self.asset = Asset.objects.create(category=self.category, asset_code="NB-HP", name="HP ProBook")
        self.unit = AssetUnit.objects.create(asset=self.asset, unit_code="NB-HP-001", status="digunakan")
        self.emp = Employee.objects.create(nik="NIK100", name="Doni")
        self.unit.assigned_to = self.emp
        self.unit.save()

    def test_delete_employee_with_held_assets_is_prevented(self):
        """Karyawan yang masih memegang unit tidak boleh terhapus."""
        response = self.client.post(reverse('employee_delete', kwargs={'emp_id': self.emp.id}))
        self.assertEqual(response.status_code, 302)
        # Karyawan harus tetap ada
        self.assertTrue(Employee.objects.filter(id=self.emp.id).exists())

    def test_delete_employee_without_assets_succeeds(self):
        """Karyawan bebas tanggungan aset dinonaktifkan secara aman (soft delete)."""
        self.unit.assigned_to = None
        self.unit.status = 'tersedia'
        self.unit.save()

        response = self.client.post(reverse('employee_delete', kwargs={'emp_id': self.emp.id}))
        self.assertEqual(response.status_code, 302)
        self.emp.refresh_from_db()
        # Karyawan tetap ada di database untuk menjaga integritas transaksi masa lalu
        self.assertTrue(Employee.objects.filter(id=self.emp.id).exists())
        self.assertFalse(self.emp.is_active)

    def test_reactivate_employee(self):
        """Karyawan yang dinonaktifkan dapat diaktifkan kembali."""
        self.emp.is_active = False
        self.emp.save()

        response = self.client.post(reverse('employee_activate', kwargs={'emp_id': self.emp.id}))
        self.assertEqual(response.status_code, 302)
        self.emp.refresh_from_db()
        self.assertTrue(self.emp.is_active)


class DocumentValidationTests(TestCase):
    """Pengujian validasi berkas upload BAST."""

    def test_valid_document_extension_and_size(self):
        doc = SimpleUploadedFile("bast.pdf", b"dummy content", content_type="application/pdf")
        is_valid, err = validate_uploaded_document(doc)
        self.assertTrue(is_valid)
        self.assertIsNone(err)

    def test_invalid_document_extension(self):
        doc = SimpleUploadedFile("script.sh", b"echo evil", content_type="application/x-sh")
        is_valid, err = validate_uploaded_document(doc)
        self.assertFalse(is_valid)
        self.assertIn("Format file tidak diizinkan", err)

    def test_oversized_document(self):
        big_content = b"0" * (6 * 1024 * 1024)  # 6 MB
        doc = SimpleUploadedFile("large_bast.pdf", big_content, content_type="application/pdf")
        is_valid, err = validate_uploaded_document(doc)
        self.assertFalse(is_valid)
        self.assertIn("Ukuran file maksimal 5MB", err)


class UnitDeleteRouteTests(TestCase):
    """Pengujian fungsionalitas dan rute unit_delete yang baru didaftarkan."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testadmin", password="password123")
        self.client.login(username="testadmin", password="password123")

        self.category = Category.objects.create(name="Aset Network")
        self.asset = Asset.objects.create(category=self.category, asset_code="AP-ARUBA", name="AP Aruba", qty=1)
        self.unit = AssetUnit.objects.create(asset=self.asset, unit_code="AP-ARUBA-001")

    def test_unit_delete_view_executes_successfully(self):
        """Verifikasi bahwa rute /unit/<id>/delete/ kini aktif dan berfungsi mengurangi asset.qty."""
        delete_url = reverse('unit_delete', kwargs={'unit_id': self.unit.id})
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 302)

        self.assertFalse(AssetUnit.objects.filter(id=self.unit.id).exists())
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.qty, 0)


class PaginationIntegrationTests(TestCase):
    """Pengujian pagination 25 item per halaman pada tabel data besar."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testadmin", password="password123")
        self.client.login(username="testadmin", password="password123")

        self.category = Category.objects.create(name="Aset Karyawan")
        # Buat 30 aset untuk menguji pagination (> 25)
        for i in range(1, 31):
            Asset.objects.create(
                category=self.category,
                asset_code=f"AST-{i:03d}",
                name=f"Laptop Seri {i}"
            )

    def test_asset_list_pagination(self):
        """Memastikan asset_list membatasi 25 item di halaman 1 dan 5 item di halaman 2."""
        response = self.client.get(reverse('asset_list') + '?tab=karyawan')
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        page1 = response.context['page_obj']
        self.assertEqual(len(page1), 25)
        self.assertTrue(page1.has_next())

        # Halaman 2
        response2 = self.client.get(reverse('asset_list') + '?tab=karyawan&page=2')
        self.assertEqual(response2.status_code, 200)
        page2 = response2.context['page_obj']
        self.assertEqual(len(page2), 5)
        self.assertFalse(page2.has_next())


class RoleBasedAccessControlTests(TestCase):
    """Pengujian hak akses dan restriksi peran pengguna (RBAC)."""

    def setUp(self):
        from django.contrib.auth.models import Group
        self.client = Client()

        # Groups
        self.grp_operator, _ = Group.objects.get_or_create(name='Teknisi IT')
        self.grp_auditor, _ = Group.objects.get_or_create(name='Auditor')

        # Users
        self.admin_user = User.objects.create_superuser(username="superadmin", password="password123")
        self.operator_user = User.objects.create_user(username="teknisi1", password="password123")
        self.operator_user.groups.add(self.grp_operator)

        self.auditor_user = User.objects.create_user(username="auditor1", password="password123")
        self.auditor_user.groups.add(self.grp_auditor)

        self.category = Category.objects.create(name="Aset Kantor")

    def test_superadmin_can_access_backup(self):
        """Superadmin berhak mengakses halaman backup database."""
        self.client.login(username="superadmin", password="password123")
        response = self.client.get(reverse('backup_database'))
        self.assertEqual(response.status_code, 200)

    def test_operator_blocked_from_backup(self):
        """Teknisi / Operator dilarang mengakses halaman backup database (403 Forbidden)."""
        self.client.login(username="teknisi1", password="password123")
        response = self.client.get(reverse('backup_database'))
        self.assertEqual(response.status_code, 403)

    def test_auditor_can_view_but_cannot_mutate(self):
        """Auditor dapat melihat daftar aset tetapi dilarang menambah aset (403 Forbidden)."""
        self.client.login(username="auditor1", password="password123")

        # Melihat daftar: diizinkan (200 OK)
        view_response = self.client.get(reverse('asset_list'))
        self.assertEqual(view_response.status_code, 200)

        # Mencoba menambah aset: ditolak (403 Forbidden)
        post_response = self.client.post(reverse('asset_add'), data={
            'category': self.category.id,
            'asset_code': 'PC-AUDIT',
            'name': 'Komputer Audit'
        })
        self.assertEqual(post_response.status_code, 403)


class ConfigurationItemWorkflowTests(TestCase):
    """Pengujian fungsional dan integritas modul Configuration Item (CMDB)."""

    def setUp(self):
        from django.contrib.auth.models import Group
        self.client = Client()

        # Admin user
        self.admin = User.objects.create_superuser(username="ci_admin", password="password123")
        self.client.login(username="ci_admin", password="password123")

        # Master Aset & Karyawan
        self.category = Category.objects.create(name="Aset Karyawan")
        self.asset = Asset.objects.create(category=self.category, asset_code="PC-HP", name="HP EliteDesk")
        self.unit = AssetUnit.objects.create(asset=self.asset, unit_code="PC-HP-001", status="tersedia")
        self.emp = Employee.objects.create(nik="NIK-CI-01", name="Rizky Pratama", is_active=True)

        # CI Contoh
        self.ci_ssd = ConfigurationItem.objects.create(
            ci_code="CI-STR-099",
            name="SSD Kingston NV2 1TB",
            category="storage",
            brand="Kingston",
            serial_number="SN-KNG-1234",
            status="available",
            location="Gudang IT"
        )
        self.ci_ram = ConfigurationItem.objects.create(
            ci_code="CI-MEM-099",
            name="RAM Kingston 16GB DDR4",
            category="memory",
            brand="Kingston",
            status="available",
            location="Gudang IT"
        )

    def test_create_ci_with_auto_code(self):
        """Memverifikasi penambahan CI dengan auto-generate kode CI."""
        response = self.client.post(reverse('ci_create'), data={
            'name': 'Monitor Dell 24 Inch',
            'category': 'peripheral',
            'brand': 'Dell',
            'model_series': 'P2419H',
            'serial_number': 'SN-DELL-P2419',
            'condition': 'new',
            'status': 'available',
            'location': 'Gudang IT'
        })
        self.assertEqual(response.status_code, 302)
        new_ci = ConfigurationItem.objects.filter(serial_number='SN-DELL-P2419').first()
        self.assertIsNotNone(new_ci)
        self.assertTrue(new_ci.ci_code.startswith('CI-PER-'))
        # Pastikan history created terbentuk
        self.assertTrue(CIHistory.objects.filter(ci=new_ci, action='created').exists())

    def test_ci_assign_to_asset_unit(self):
        """Memasang komponen ke unit perangkat PC/Laptop secara transaksional."""
        response = self.client.post(reverse('ci_assign', kwargs={'ci_id': self.ci_ssd.id}), data={
            'usage_type': 'asset',
            'target_id': self.unit.id,
            'notes': 'Pemasangan storage OS utama'
        })
        self.assertEqual(response.status_code, 302)

        self.ci_ssd.refresh_from_db()
        self.assertEqual(self.ci_ssd.status, 'in_use')
        self.assertEqual(self.ci_ssd.installed_on, self.unit)
        self.assertIsNone(self.ci_ssd.assigned_to)

        # Timeline CIHistory terekam
        last_history = self.ci_ssd.history.first()
        self.assertEqual(last_history.action, 'installed')
        self.assertEqual(last_history.related_unit, self.unit)

        # UnitLog pada unit induk juga merekam pemasangan komponen
        self.assertTrue(UnitLog.objects.filter(unit=self.unit, notes__contains=self.ci_ssd.ci_code).exists())

    def test_ci_assign_to_employee(self):
        """Mengalokasikan komponen peripheral langsung ke karyawan."""
        response = self.client.post(reverse('ci_assign', kwargs={'ci_id': self.ci_ram.id}), data={
            'usage_type': 'employee',
            'target_id': self.emp.id,
            'notes': 'Penyerahan langsung'
        })
        self.assertEqual(response.status_code, 302)

        self.ci_ram.refresh_from_db()
        self.assertEqual(self.ci_ram.status, 'in_use')
        self.assertEqual(self.ci_ram.assigned_to, self.emp)
        self.assertIsNone(self.ci_ram.installed_on)

    def test_ci_remove_from_unit(self):
        """Pelepasan komponen dari unit dan pengembalian ke gudang."""
        # Pasang terlebih dahulu
        self.ci_ssd.installed_on = self.unit
        self.ci_ssd.status = 'in_use'
        self.ci_ssd.save()

        response = self.client.post(reverse('ci_remove', kwargs={'ci_id': self.ci_ssd.id}), data={
            'new_status': 'available',
            'new_condition': 'good',
            'location': 'Rak A-1',
            'notes': 'Dilepas untuk backup data'
        })
        self.assertEqual(response.status_code, 302)

        self.ci_ssd.refresh_from_db()
        self.assertEqual(self.ci_ssd.status, 'available')
        self.assertIsNone(self.ci_ssd.installed_on)
        self.assertEqual(self.ci_ssd.location, 'Rak A-1')

        # Verifikasi log pelepasan
        last_history = self.ci_ssd.history.first()
        self.assertEqual(last_history.action, 'removed')

    def test_ci_replace_and_upgrade_flow(self):
        """Workflow penggantian / upgrade komponen pada suatu perangkat."""
        # Pasang SSD lama di unit
        self.ci_ssd.installed_on = self.unit
        self.ci_ssd.status = 'in_use'
        self.ci_ssd.save()

        # Siapkan SSD baru sebagai pengganti
        replacement_ssd = ConfigurationItem.objects.create(
            ci_code="CI-STR-100",
            name="SSD Samsung 990 Pro 2TB",
            category="storage",
            status="available",
            location="Gudang IT"
        )

        response = self.client.post(reverse('ci_replace', kwargs={'ci_id': self.ci_ssd.id}), data={
            'replacement_ci_id': replacement_ssd.id,
            'reason': 'Peningkatan Kapasitas / Performa',
            'old_ci_status': 'available',
            'old_ci_condition': 'good',
            'old_ci_location': 'Gudang IT',
            'notes': 'Upgrade storage ke 2TB'
        })
        self.assertEqual(response.status_code, 302)

        # Komponen lama lepas
        self.ci_ssd.refresh_from_db()
        self.assertIsNone(self.ci_ssd.installed_on)
        self.assertEqual(self.ci_ssd.status, 'available')

        # Komponen baru terpasang di unit
        replacement_ssd.refresh_from_db()
        self.assertEqual(replacement_ssd.installed_on, self.unit)
        self.assertEqual(replacement_ssd.status, 'in_use')

        # Riwayat tercatat pada kedua item
        self.assertTrue(CIHistory.objects.filter(ci=self.ci_ssd, action='replaced').exists())
        self.assertTrue(CIHistory.objects.filter(ci=replacement_ssd, action='installed').exists())

    def test_prevent_double_assignment(self):
        """Mencegah assignment ganda pada komponen yang sedang in_use."""
        self.ci_ssd.status = 'in_use'
        self.ci_ssd.installed_on = self.unit
        self.ci_ssd.save()

        response = self.client.post(reverse('ci_assign', kwargs={'ci_id': self.ci_ssd.id}), data={
            'usage_type': 'employee',
            'target_id': self.emp.id,
        })
        self.assertEqual(response.status_code, 302)
        self.ci_ssd.refresh_from_db()
        # Harus tetap terpasang pada unit, tidak pindah ke karyawan
        self.assertEqual(self.ci_ssd.installed_on, self.unit)

    def test_ci_report_damage(self):
        """Melaporkan keluhan kerusakan teknis pada komponen."""
        response = self.client.post(reverse('ci_report_damage', kwargs={'ci_id': self.ci_ssd.id}), data={
            'action_type': 'repair_in',
            'condition': 'damaged',
            'notes': 'Sektor bad sector terdeteksi pada SMART check'
        })
        self.assertEqual(response.status_code, 302)
        self.ci_ssd.refresh_from_db()
        self.assertEqual(self.ci_ssd.status, 'under_repair')
        self.assertEqual(self.ci_ssd.condition, 'damaged')
        self.assertTrue(CIHistory.objects.filter(ci=self.ci_ssd, action='repair_in').exists())


class ConsumableModuleTests(TestCase):
    """Pengujian komprehensif alur bisnis, integritas saldo, dan keamanan modul Consumable Item."""

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser('admin_test', 'admin@example.com', 'password123')
        self.operator_user = User.objects.create_user('tech_operator', 'tech@example.com', 'password123', is_staff=False)
        self.auditor_user = User.objects.create_user('auditor_user', 'audit@example.com', 'password123', is_staff=False)

        from django.contrib.auth.models import Group
        grp_op, _ = Group.objects.get_or_create(name='Teknisi IT')
        self.operator_user.groups.add(grp_op)
        grp_audit, _ = Group.objects.get_or_create(name='Auditor')
        self.auditor_user.groups.add(grp_audit)

        self.client.login(username='admin_test', password='password123')

        # Master data pendukung
        self.emp = Employee.objects.create(nik="EMP-NET-01", name="Rian Jaringan", position="Network Engineer")
        self.cat = Category.objects.create(name="Aset Network")
        self.asset = Asset.objects.create(category=self.cat, asset_code="SW-HP", name="Switch HP 24P")
        self.unit = AssetUnit.objects.create(asset=self.asset, unit_code="SW-HP-001", status="digunakan")

        # Item uji coba
        self.item_cable = ConsumableItem.objects.create(
            item_code="CNS-CAB-001",
            name="Kabel UTP Cat6 Belden",
            category="cable",
            brand="Belden",
            specification="UTP Cat6 24AWG Solid Copper",
            base_unit="meter",
            purchase_unit="roll",
            conversion_rate=305,
            stock_available=305,
            minimum_stock=50,
            location="Gudang Induk (GI)",
            last_purchase_price=1800000
        )

        self.item_rj45 = ConsumableItem.objects.create(
            item_code="CNS-CON-001",
            name="Konektor RJ45 Cat6",
            category="connector",
            brand="AMP / CommScope",
            base_unit="pcs",
            stock_available=10,
            minimum_stock=20,
            location="Ruang Server / IT"
        )

    def test_consumable_model_status_property(self):
        """Memverifikasi kalkulasi status stok: available, low_stock, dan out_of_stock."""
        # Stok kabel 305 > min 50 -> available
        self.assertEqual(self.item_cable.stock_status, 'available')
        self.assertEqual(self.item_cable.stock_status_display, 'Tersedia')

        # Stok RJ45 10 <= min 20 -> low_stock
        self.assertEqual(self.item_rj45.stock_status, 'low_stock')
        self.assertEqual(self.item_rj45.stock_status_display, 'Menipis')

        # Habiskan stok
        self.item_rj45.stock_available = 0
        self.item_rj45.save()
        self.assertEqual(self.item_rj45.stock_status, 'out_of_stock')
        self.assertEqual(self.item_rj45.stock_status_display, 'Habis')

    def test_consumable_list_view(self):
        """Halaman list dapat diakses, menghitung KPI summary, dan merender data aktual."""
        response = self.client.get(reverse('consumable_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kabel UTP Cat6 Belden")
        self.assertContains(response, "Konektor RJ45 Cat6")
        self.assertEqual(response.context['counts']['total'], 2)
        self.assertEqual(response.context['counts']['low_stock'], 1)

    def test_consumable_create_with_initial_stock(self):
        """Menambah item baru dengan stok awal > 0 wajib mencatat entri buku besar otomatis."""
        response = self.client.post(reverse('consumable_create'), data={
            'item_code': 'CNS-MNT-001',
            'name': 'Thermal Paste Arctic MX-4',
            'category': 'maintenance',
            'brand': 'Arctic',
            'specification': 'Thermal Compound 4g 8.5W/mK',
            'base_unit': 'tube',
            'initial_stock': '5',
            'minimum_stock': '2',
            'location': 'Workshop IT',
            'last_purchase_price': '125000',
        })
        self.assertEqual(response.status_code, 302)

        new_item = ConsumableItem.objects.filter(item_code='CNS-MNT-001').first()
        self.assertIsNotNone(new_item)
        self.assertEqual(new_item.stock_available, 5)

        # Cek ledger otomatis
        trx = ConsumableTransaction.objects.filter(item=new_item, transaction_type='in').first()
        self.assertIsNotNone(trx)
        self.assertEqual(trx.quantity_base, 5)
        self.assertEqual(trx.source_destination, 'Stok Awal Terotorisasi')

    def test_consumable_edit_preserves_stock_integrity(self):
        """Edit master item memperbarui metadata namun tidak mengubah saldo stok fisik sembarangan."""
        old_stock = self.item_cable.stock_available
        response = self.client.post(reverse('consumable_edit', kwargs={'item_id': self.item_cable.id}), data={
            'name': 'Kabel UTP Cat6 Belden High Performance',
            'category': 'cable',
            'brand': 'Belden USA',
            'specification': '24 AWG Solid Copper Pure',
            'base_unit': 'meter',
            'purchase_unit': 'roll',
            'conversion_rate': '305',
            'minimum_stock': '40',
            'location': 'Gudang Induk (GI)',
            'last_purchase_price': '1850000',
        })
        self.assertEqual(response.status_code, 302)
        self.item_cable.refresh_from_db()
        self.assertEqual(self.item_cable.name, 'Kabel UTP Cat6 Belden High Performance')
        self.assertEqual(self.item_cable.brand, 'Belden USA')
        self.assertEqual(self.item_cable.minimum_stock, 40)
        # Saldo stok tetap terjaga
        self.assertEqual(self.item_cable.stock_available, old_stock)

    def test_barang_masuk_purchase_unit_conversion(self):
        """Barang masuk dengan satuan pembelian dikonversi ke satuan dasar secara akurat."""
        # Stok awal kabel: 305 meter. Masuk 2 roll (2 * 305 = 610 meter).
        response = self.client.post(reverse('consumable_in'), data={
            'item_id': self.item_cable.id,
            'quantity': '2',
            'unit_type': 'purchase',
            'transaction_date': '2026-10-26',
            'source_destination': 'Pembelian PT. KMH',
            'supplier': 'PT. Trikom Mandiri',
            'reference_no': 'PO-IT-2026-101',
            'notes': 'Stok kabel tambahan untuk proyek Adit 2'
        })
        self.assertEqual(response.status_code, 302)

        self.item_cable.refresh_from_db()
        self.assertEqual(self.item_cable.stock_available, 305 + 610)

        # Verifikasi ledger
        trx = ConsumableTransaction.objects.filter(item=self.item_cable, transaction_type='in').first()
        self.assertIsNotNone(trx)
        self.assertEqual(trx.quantity, 2)
        self.assertEqual(trx.unit, 'roll')
        self.assertEqual(trx.quantity_base, 610)
        self.assertEqual(trx.stock_before, 305)
        self.assertEqual(trx.stock_after, 915)

    def test_barang_keluar_success_with_asset_and_ticket(self):
        """Barang keluar memotong stok secara atomik dan terintegrasi dengan tiket & unit aset."""
        response = self.client.post(reverse('consumable_out'), data={
            'item_id': self.item_cable.id,
            'quantity': '45',
            'unit_type': 'base',
            'transaction_date': '2026-10-26',
            'recipient_employee': self.emp.id,
            'related_unit': self.unit.id,
            'ticket_number': 'WO-NET-2026-088',
            'source_destination': 'Tarik kabel koneksi Switch HP-001 ke Ruang Kontrol',
            'notes': 'Patching jalur LAN'
        })
        self.assertEqual(response.status_code, 302)

        self.item_cable.refresh_from_db()
        self.assertEqual(self.item_cable.stock_available, 305 - 45)

        trx = ConsumableTransaction.objects.filter(item=self.item_cable, transaction_type='out').first()
        self.assertIsNotNone(trx)
        self.assertEqual(trx.quantity_base, 45)
        self.assertEqual(trx.recipient_employee, self.emp)
        self.assertEqual(trx.related_unit, self.unit)
        self.assertEqual(trx.ticket_number, 'WO-NET-2026-088')
        self.assertEqual(trx.stock_before, 305)
        self.assertEqual(trx.stock_after, 260)

    def test_barang_keluar_insufficient_stock_prevented(self):
        """Negative test: pengeluaran melebihi stok ditolak dan tidak boleh menghasilkan saldo negatif."""
        stock_awal = self.item_rj45.stock_available  # 10 pcs
        response = self.client.post(reverse('consumable_out'), data={
            'item_id': self.item_rj45.id,
            'quantity': '25',  # Minta 25 dari 10
            'unit_type': 'base',
            'transaction_date': '2026-10-26',
            'recipient_employee': self.emp.id,
            'source_destination': 'Terminasi kabel',
        })
        self.assertEqual(response.status_code, 302)

        # Saldo stok tidak berubah
        self.item_rj45.refresh_from_db()
        self.assertEqual(self.item_rj45.stock_available, stock_awal)
        # Tidak ada transaksi keluar yang tercatat
        self.assertFalse(ConsumableTransaction.objects.filter(item=self.item_rj45, transaction_type='out').exists())

    def test_stock_opname_adjustment(self):
        """Stock Opname menghitung selisih fisik vs sistem dan membukukan penyesuaian."""
        # Stok awal RJ45 sistem: 10. Hasil fisik lapangan: 8 (selisih -2).
        response = self.client.post(reverse('consumable_adjust'), data={
            'item_id': self.item_rj45.id,
            'actual_stock': '8',
            'transaction_date': '2026-10-26',
            'reason': 'Hasil audit fisik akhir bulan: 2 pcs rusak pecah pada pengunci'
        })
        self.assertEqual(response.status_code, 302)

        self.item_rj45.refresh_from_db()
        self.assertEqual(self.item_rj45.stock_available, 8)

        trx = ConsumableTransaction.objects.filter(item=self.item_rj45, transaction_type='adjustment').first()
        self.assertIsNotNone(trx)
        self.assertEqual(trx.stock_before, 10)
        self.assertEqual(trx.stock_after, 8)
        self.assertIn("Selisih -2", trx.notes)

    def test_transaction_reversal_workflow(self):
        """Mekanisme reversal membatalkan efek transaksi asal dan membuat entri pembalik yang dapat diaudit."""
        # Lakukan pengeluaran 5 pcs RJ45
        self.client.post(reverse('consumable_out'), data={
            'item_id': self.item_rj45.id,
            'quantity': '5',
            'unit_type': 'base',
            'transaction_date': '2026-10-26',
            'recipient_employee': self.emp.id,
            'source_destination': 'Uji coba terminasi',
        })
        self.item_rj45.refresh_from_db()
        self.assertEqual(self.item_rj45.stock_available, 5)

        out_trx = ConsumableTransaction.objects.filter(item=self.item_rj45, transaction_type='out').first()

        # Eksekusi Reversal
        response = self.client.post(reverse('consumable_transaction_reverse', kwargs={'trx_id': out_trx.id}), data={
            'reversal_reason': 'Salah input teknisi, barang batal dikeluarkan'
        })
        self.assertEqual(response.status_code, 302)

        # Stok kembali pulih ke 10
        self.item_rj45.refresh_from_db()
        self.assertEqual(self.item_rj45.stock_available, 10)

        # Transaksi asal ditandai reversed
        out_trx.refresh_from_db()
        self.assertTrue(out_trx.is_reversed)
        self.assertIsNotNone(out_trx.reversed_by)

        # Transaksi reversal tercatat di buku besar
        rev_trx = out_trx.reversed_by
        self.assertEqual(rev_trx.transaction_type, 'reversal')
        self.assertEqual(rev_trx.stock_before, 5)
        self.assertEqual(rev_trx.stock_after, 10)

    def test_auditor_permission_restriction(self):
        """Role Auditor (Read-Only) diblokir dari aksi penambahan atau pengubahan stok."""
        self.client.logout()
        self.client.login(username='auditor_user', password='password123')

        # Mencoba posting barang masuk
        response = self.client.post(reverse('consumable_in'), data={
            'item_id': self.item_cable.id,
            'quantity': '10',
            'unit_type': 'base',
        })
        # Harus ditolak dengan 403 Forbidden oleh @operator_required
        self.assertEqual(response.status_code, 403)

    def test_export_excel_and_pdf(self):
        """Endpoint export Excel dan PDF mengembalikan berkas dengan status 200 dan content type valid."""
        res_excel = self.client.get(reverse('consumable_export_excel'))
        self.assertEqual(res_excel.status_code, 200)
        self.assertIn('spreadsheetml', res_excel['Content-Type'])

        res_pdf = self.client.get(reverse('consumable_export_pdf'))
        self.assertEqual(res_pdf.status_code, 200)
        self.assertEqual(res_pdf['Content-Type'], 'application/pdf')




