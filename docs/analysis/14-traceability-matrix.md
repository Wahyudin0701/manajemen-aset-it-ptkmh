# 14 — Traceability Matrix

**Tanggal Analisis:** 26 Oktober 2026  
**Status Verifikasi:** Terverifikasi via cross-referencing file models, views, templates, dan urls.  

---

## 1. Matriks Keterlacakan Komprehensif (End-to-End)

| Req ID | Deskripsi Kebutuhan | Feature ID | URL / Endpoint | View / Handler | Model Terkait | Aturan Permission | Cakupan Test Eksisting | Risiko & Technical Debt Terkait |
|---|---|---|---|---|---|---|---|---|
| **FR-AUTH-01** | Login pengguna berbasis kredensial | FEAT-001 | `/login/` (GET/POST) | `assets.views.login_view` | `django.contrib.auth.models.User` | Anonim / Public | ❌ 0% (Tidak ada test) | Brute-force risk (tanpa rate limiting) |
| **FR-AUTH-02** | Logout sesi pengguna | FEAT-002 | `/logout/` (POST) | `assets.views.logout_view` | `User`, `Session` | Login Required | ❌ 0% | - |
| **FR-AUTH-03** | Manajemen profil & password admin | FEAT-003, 004 | `/profil/` (GET/POST) | `assets.views.profile_view` | `User` | Login Required | ❌ 0% | Username clash exception handling |
| **FR-DASH-01** | Pemantauan metrik aset & log mutasi | FEAT-005, 006 | `/` (GET) | `assets.views.dashboard` | `AssetUnit`, `AssetAssignment` | Login Required | ❌ 0% | Potensi query N+1 pada recent log loops |
| **FR-ASSET-01** | Katalog master jenis aset (SKU level) | FEAT-007, 008 | `/aset/` (GET) | `assets.views.asset_list` | `Asset`, `Category` | Login Required | ❌ 0% | Ketiadaan pagination (`TD-009`) |
| **FR-ASSET-02** | Penambahan master jenis aset baru | FEAT-009 | `/aset/add/` (POST) | `assets.views.asset_add` | `Asset` | **❌ Anonim (Bug!)** | ❌ 0% | **`SEC-001` (Celah akses anonim)** |
| **FR-ASSET-03** | Perubahan data & kode master aset | FEAT-010 | `/aset/<id>/edit/` (POST) | `assets.views.asset_edit` | `Asset`, `AssetUnit` | Login Required | ❌ 0% | Konflik penomoran unit saat batch update |
| **FR-ASSET-04** | Penghapusan master aset (Cascade) | FEAT-011 | `/aset/<id>/delete/` (POST) | `assets.views.asset_delete` | `Asset`, `AssetUnit` | Login Required | ❌ 0% | Unit fisik terhapus cascade tanpa audit log |
| **FR-UNIT-01** | Pengelolaan unit fisik individual | FEAT-014 | `/aset/<id>/units/` (GET) | `assets.views.asset_units` | `AssetUnit`, `Employee` | Login Required | ❌ 0% | - |
| **FR-UNIT-02** | Registrasi unit fisik baru ber-suffix | FEAT-015 | `/aset/<id>/units/add/` (POST) | `assets.views.unit_add` | `AssetUnit`, `UnitLog` | Login Required | ❌ 0% | Inkonsistensi update `asset.qty` manual |
| **FR-UNIT-03** | Edit metadata & pemegang unit fisik | FEAT-016 | `/unit/<id>/edit/` (POST) | `assets.views.unit_edit` | `AssetUnit`, `UnitLog` | Login Required | ❌ 0% | Status assignment tidak tersinkronisasi |
| **FR-UNIT-04** | Penghapusan unit fisik individual | FEAT-017 | *(URL Missing!)* | `assets.views.unit_delete` | `AssetUnit` | Login Required | ❌ 0% | **`TD-002` (Fungsi tidak bisa diakses)** |
| **FR-UNIT-05** | Update status unit & lokasi network | FEAT-018 | `/unit/<id>/status/` (POST) | `assets.views.unit_update_status` | `AssetUnit`, `UnitLog` | Login Required | ❌ 0% | Hardcoded AREA choices |
| **FR-HIST-01** | Timeline riwayat perjalanan unit | FEAT-023 | `/unit/<id>/history/` (GET) | `assets.views.unit_history` | `UnitLog`, `Employee` | Login Required | ❌ 0% | Regex parsing nama employee (`TD-011`) |
| **FR-STAT-01** | Monitoring status aset (Tersedia/Pakai/Rusak) | FEAT-026, 027 | `/status-aset/` (GET) | `assets.views.status_aset_list` | `AssetUnit`, `Category` | Login Required | ❌ 0% | Filter string `Network` hardcoded |
| **FR-DIST-01** | Distribusi serah terima unit ke user | FEAT-031 | `/distribusi/handover/` (POST) | `assets.views.distribusi_handover` | `AssetAssignment`, `AssetUnit`, `UnitLog` | Login Required | ❌ 0% | Validasi file upload BAST nihil (`TD-006`) |
| **FR-DIST-02** | Mutasi kepemilikan aset antar user | FEAT-032 | `/distribusi/mutation/` (POST) | `assets.views.distribusi_mutation` | `AssetAssignment`, `AssetUnit`, `UnitLog` | Login Required | ❌ 0% | Validasi file upload BAST nihil (`TD-006`) |
| **FR-DIST-03** | Pengembalian unit aset ke gudang | FEAT-033 | `/distribusi/return/` (POST) | `assets.views.distribusi_return` | `AssetAssignment`, `AssetUnit`, `UnitLog` | Login Required | ❌ 0% | Kolom `returned_date` tidak terisi (`TD-008`) |
| **FR-DIST-04** | Susulan unggah berkas fisik BAST | FEAT-034 | `/distribusi/<id>/upload/` (POST) | `assets.views.distribusi_upload_doc` | `AssetAssignment` | Login Required | ❌ 0% | - |
| **FR-EMP-01** | Pengelolaan master data karyawan | FEAT-037..042 | `/karyawan/` (All Methods) | `assets.views.employee_*` | `Employee`, `AssetUnit` | Login Required | ❌ 0% | Ketiadaan soft delete pada master employee |
| **FR-QR-01** | Generate gambar stiker QR Code | FEAT-021 | `/qr/<uuid>/` (GET) | `assets.views.unit_qr_code` | `AssetUnit` | Anonim / Public | ❌ 0% | Dependensi font OS (`arial.ttf`) |
| **FR-QR-02** | Halaman publik info & histori unit | FEAT-022 | `/public/unit/<uuid>/` (GET) | `assets.views.unit_public_detail` | `AssetUnit`, `UnitLog` | Anonim / Public | ❌ 0% | Ekposur data histori internal ke publik |
| **FR-EXP-01** | Cetak Laporan PDF Seluruh Modul | FEAT-012, 019, 024, 028, 035, 043, 045 | `*/*/export/` (GET) | `assets.views.*_export_pdf` | Semua Model | Login Required | ❌ 0% | Duplikasi kode ReportLab ~1.500 baris |
| **FR-EXP-02** | Unduh Spreadsheet Excel Seluruh Modul | FEAT-013, 020, 025, 029, 036, 044, 046 | `*/*/export-excel/` (GET) | `assets.views.*_export_excel` | Semua Model | Login Required | ❌ 0% | Duplikasi kode openpyxl ~600 baris |
| **FR-OPS-01** | Pencadangan database (JSON / SQL) | FEAT-047, 048 | `/backup/` (GET/POST) | `assets.views.backup_database_view` | Seluruh DB | Superuser Only | ❌ 0% | Password terekspos di CLI `mysqldump` |
