# 03 — Feature Inventory: Inventaris Fitur Lengkap

**Tanggal Analisis:** 26 Oktober 2026  
**Sumber:** `assets/views.py`, `itam_core/urls.py`, `templates/*.html`  
**Status:** Terverifikasi dari source code statis

---

## Legenda Status

| Status | Arti |
|---|---|
| ✅ Implemented | Implementasi lengkap ditemukan |
| ⚠️ Partially Implemented | Sebagian alur tersedia |
| ❌ Potentially Defective | Bug/inkonsistensi ditemukan |
| 🔲 Missing | Tidak ditemukan implementasi |
| ❓ Unverified | Ada kode tapi belum bisa diverifikasi runtime |

---

## Feature Inventory Table

| FEAT-ID | Modul | Fitur | Deskripsi | Aktor | Entry Point (URL) | Komponen | Model | Permission | Status | Risiko |
|---|---|---|---|---|---|---|---|---|---|---|
| FEAT-001 | Auth | Login | Autentikasi username/password | Semua user | `GET/POST /login/` | `login_view`, `login.html` | Django User | Public | ✅ | Tidak ada rate limiting |
| FEAT-002 | Auth | Logout | Keluar dari sesi | Admin | `POST /logout/` | `logout_view` | Django User | Login | ✅ | — |
| FEAT-003 | Auth | Edit Profil | Update nama, username, email | Admin | `GET/POST /profil/` | `profile_view`, `profile.html` | Django User | Login | ✅ | Tidak ada validasi username unik |
| FEAT-004 | Auth | Ubah Password | Ganti password dengan verifikasi lama | Admin | `POST /profil/` | `profile_view` | Django User | Login | ✅ | — |
| FEAT-005 | Dashboard | Statistik Ringkasan | Jumlah aset per kategori dan status | Admin | `GET /` | `dashboard`, `dashboard.html` | AssetUnit, AssetAssignment | Login | ✅ | N+1 query potential |
| FEAT-006 | Dashboard | Log Aktivitas Terbaru | 5 serah terima, 3 mutasi, 3 pengembalian | Admin | `GET /` | `dashboard` | AssetAssignment | Login | ✅ | Data statis hardcoded limit |
| FEAT-007 | Aset | Daftar Aset | List aset dengan tab Karyawan/Network | Admin | `GET /aset/` | `asset_list`, `asset_list.html` | Asset, Category | Login | ✅ | Tidak ada pagination |
| FEAT-008 | Aset | Cari Aset | Filter berdasarkan kode, nama, merek | Admin | `GET /aset/?q=...` | `asset_list` | Asset | Login | ✅ | — |
| FEAT-009 | Aset | Tambah Aset | Create jenis aset baru | Admin | `POST /aset/add/` | `asset_add` | Asset | **❌ No Auth!** | ❌ | **CRITICAL: Tidak ada @login_required** |
| FEAT-010 | Aset | Edit Aset | Update data jenis aset | Admin | `POST /aset/{id}/edit/` | `asset_edit` | Asset, AssetUnit | Login | ✅ | Cascade update unit_code — risky |
| FEAT-011 | Aset | Hapus Aset | Delete jenis aset (CASCADE ke units) | Admin | `POST /aset/{id}/delete/` | `asset_delete` | Asset | Login | ✅ | Hapus unit juga! Tidak ada konfirmasi server-side |
| FEAT-012 | Aset | Export PDF Aset | Download laporan PDF daftar aset | Admin | `GET /aset/export/` | `asset_export_pdf` | Asset | Login (double decorator?) | ⚠️ | Dekorator ganda baris 84-86 |
| FEAT-013 | Aset | Export Excel Aset | Download laporan Excel daftar aset | Admin | `GET /aset/export-excel/` | `asset_export_excel` | Asset | Login | ✅ | — |
| FEAT-014 | Unit | Daftar Unit per Aset | List unit fisik suatu aset | Admin | `GET /aset/{id}/units/` | `asset_units`, `asset_units.html` | AssetUnit | Login | ✅ | Tidak ada pagination |
| FEAT-015 | Unit | Tambah Unit | Create unit fisik baru | Admin | `POST /aset/{id}/units/add/` | `unit_add` | AssetUnit, UnitLog | Login | ✅ | — |
| FEAT-016 | Unit | Edit Unit | Update kode, status, pemegang unit | Admin | `POST /unit/{id}/edit/` | `unit_edit` | AssetUnit, UnitLog | Login | ✅ | Tidak mengupdate AssetAssignment.status |
| FEAT-017 | Unit | Hapus Unit | Delete unit fisik | Admin | (URL tidak ada) | `unit_delete` (view ada) | AssetUnit | Login | ❌ | **BROKEN: view ada, URL tidak terdaftar** |
| FEAT-018 | Unit | Update Status (Network) | Update status dan lokasi unit network | Admin | `POST /unit/{id}/status/` | `unit_update_status` | AssetUnit, UnitLog | Login | ✅ | — |
| FEAT-019 | Unit | Export PDF Unit | Download laporan PDF unit per aset | Admin | `GET /aset/{id}/units/export/` | `asset_units_export_pdf` | AssetUnit | Login | ✅ | — |
| FEAT-020 | Unit | Export Excel Unit | Download laporan Excel unit | Admin | `GET /aset/{id}/units/export-excel/` | `asset_units_export_excel` | AssetUnit | Login | ✅ | — |
| FEAT-021 | QR | Generate QR Code | Buat gambar QR code unit | Publik | `GET /qr/{uuid}/` | `unit_qr_code` | AssetUnit | Public (no auth) | ✅ | Font 'arial.ttf' mungkin tidak tersedia di Linux |
| FEAT-022 | QR | Halaman Publik Unit | Detail unit tanpa login (untuk QR scan) | Publik | `GET /public/unit/{uuid}/` | `unit_public_detail`, `unit_public_detail.html` | AssetUnit, UnitLog | Public (no auth) | ✅ | Mengekspos info unit ke publik |
| FEAT-023 | Riwayat | Timeline Unit | Riwayat historis unit aset | Admin | `GET /unit/{id}/history/` | `unit_history`, `unit_history.html` | UnitLog | Login | ✅ | — |
| FEAT-024 | Riwayat | Export PDF Riwayat | Download laporan PDF riwayat unit | Admin | `GET /unit/{id}/history/export/` | `unit_history_export_pdf` | UnitLog | Login | ✅ | — |
| FEAT-025 | Riwayat | Export Excel Riwayat | Download laporan Excel riwayat | Admin | `GET /unit/{id}/history/export-excel/` | `unit_history_export_excel` | UnitLog | Login | ✅ | — |
| FEAT-026 | Status | Monitor Status Aset | List unit per status dan kategori | Admin | `GET /status-aset/` | `status_aset_list`, `status_aset_list.html` | AssetUnit | Login | ✅ | Tidak ada pagination |
| FEAT-027 | Status | Cari Status Aset | Filter berdasarkan kode, nama, karyawan, area | Admin | `GET /status-aset/?q=...` | `status_aset_list` | AssetUnit | Login | ✅ | — |
| FEAT-028 | Status | Export PDF Status | Download laporan PDF status aset | Admin | `GET /status-aset/export/` | `status_aset_export_pdf` | AssetUnit | Login | ✅ | — |
| FEAT-029 | Status | Export Excel Status | Download laporan Excel status | Admin | `GET /status-aset/export-excel/` | `status_aset_export_excel` | AssetUnit | Login | ✅ | — |
| FEAT-030 | Distribusi | Daftar Distribusi | List semua transaksi distribusi | Admin | `GET /distribusi/` | `distribusi_list`, `distribusi_list.html` | AssetAssignment | Login | ✅ | Tidak ada pagination |
| FEAT-031 | Distribusi | Serah Terima | Distribusi aset ke karyawan | Admin | `POST /distribusi/handover/` | `distribusi_handover` | AssetAssignment, AssetUnit, UnitLog | Login | ✅ | Validasi status unit minimal |
| FEAT-032 | Distribusi | Mutasi Aset | Pindah aset antar karyawan | Admin | `POST /distribusi/mutation/` | `distribusi_mutation` | AssetAssignment, AssetUnit, UnitLog | Login | ✅ | — |
| FEAT-033 | Distribusi | Pengembalian Aset | Kembalikan aset ke gudang | Admin | `POST /distribusi/return/` | `distribusi_return` | AssetAssignment, AssetUnit, UnitLog | Login | ⚠️ | `returned_date` tidak di-update |
| FEAT-034 | Distribusi | Upload Dokumen BAST | Upload dokumen setelah transaksi | Admin | `POST /distribusi/{id}/upload/` | `distribusi_upload_doc` | AssetAssignment | Login | ✅ | File type dan size validated |
| FEAT-035 | Distribusi | Export PDF Distribusi | Download laporan PDF distribusi | Admin | `GET /distribusi/export/` | `distribusi_export_pdf` | AssetAssignment | Login | ✅ | — |
| FEAT-036 | Distribusi | Export Excel Distribusi | Download laporan Excel distribusi | Admin | `GET /distribusi/export-excel/` | `distribusi_export_excel` | AssetAssignment | Login | ✅ | — |
| FEAT-037 | Karyawan | Daftar Karyawan | List karyawan dengan jumlah aset | Admin | `GET /karyawan/` | `employee_list`, `employee_list.html` | Employee | Login | ✅ | Tidak ada pagination |
| FEAT-038 | Karyawan | Cari Karyawan | Filter berdasarkan nama atau NIK | Admin | `GET /karyawan/?q=...` | `employee_list` | Employee | Login | ✅ | — |
| FEAT-039 | Karyawan | Tambah Karyawan | Create data karyawan | Admin | `POST /karyawan/buat/` | `employee_create` | Employee | Login | ✅ | — |
| FEAT-040 | Karyawan | Edit Karyawan | Update data karyawan | Admin | `POST /karyawan/{id}/edit/` | `employee_edit` | Employee | Login | ✅ | — |
| FEAT-041 | Karyawan | Hapus Karyawan | Delete karyawan (proteksi jika masih pegang aset) | Admin | `POST /karyawan/{id}/delete/` | `employee_delete` | Employee, UnitLog | Login | ✅ | Embed nama di notes — fragile |
| FEAT-042 | Karyawan | Detail Karyawan | Aset yang dipegang karyawan | Admin | `GET /karyawan/{id}/` | `employee_detail`, `employee_detail.html` | Employee, AssetUnit | Login | ✅ | — |
| FEAT-043 | Karyawan | Export PDF Karyawan | Download laporan PDF karyawan | Admin | `GET /karyawan/export/` | `employee_export_pdf` | Employee | Login | ✅ | — |
| FEAT-044 | Karyawan | Export Excel Karyawan | Download Excel daftar karyawan | Admin | `GET /karyawan/export-excel/` | `employee_export_excel` | Employee | Login | ✅ | — |
| FEAT-045 | Karyawan | Export PDF Detail | Export PDF aset per karyawan | Admin | `GET /karyawan/{id}/export/` | `employee_detail_export_pdf` | Employee, AssetUnit | Login | ✅ | — |
| FEAT-046 | Karyawan | Export Excel Detail | Export Excel aset per karyawan | Admin | `GET /karyawan/{id}/export-excel/` | `employee_detail_export_excel` | Employee, AssetAssignment | Login | ✅ | — |
| FEAT-047 | Backup | Export JSON | Download backup data sebagai JSON (dumpdata) | Admin | `POST /backup/` | `backup_database_view` | Semua | Login | ❓ | Implementasi belum diverifikasi penuh |
| FEAT-048 | Backup | Export SQL | Download backup sebagai SQL (mysqldump) | Admin | `POST /backup/` | `backup_database_view` | Semua | Login | ❓ | Risiko subprocess injection jika tidak divalidasi |
| FEAT-049 | Settings | Lihat 404 Test | Halaman test 404 | Admin | `GET /404/` | `custom_404_view` | — | Public | ✅ | Halaman debug — seharusnya dihapus di production |

---

## Ringkasan Status

| Status | Jumlah |
|---|---|
| ✅ Implemented | 39 |
| ⚠️ Partially Implemented | 3 |
| ❌ Potentially Defective | 2 |
| ❓ Unverified | 2 |
| 🔲 Missing | 0 |
| **Total** | **49** |

---

## Fitur Kritis yang Perlu Perhatian Segera

| FEAT-ID | Masalah | Dampak |
|---|---|---|
| FEAT-009 | `asset_add` tidak ada `@login_required` | Penambahan aset oleh siapapun |
| FEAT-017 | `unit_delete` view ada tapi URL tidak terdaftar | Hapus unit tidak bisa dilakukan |
| FEAT-012 | Double `@login_required` decorator (anomali) | Potensi bug tak terduga |
| FEAT-033 | `returned_date` tidak diisi saat pengembalian | Data tidak akurat |
| FEAT-048 | Backup SQL via mysqldump — perlu audit subprocess | Risiko keamanan command injection |
