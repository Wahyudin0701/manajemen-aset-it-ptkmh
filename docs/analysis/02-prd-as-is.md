# 02 — PRD As-Is: Product Requirements Document (Berdasarkan Implementasi)

**Tanggal Analisis:** 26 Oktober 2026  
**Tipe Dokumen:** PRD As-Is — requirement berdasarkan implementasi yang ditemukan, bukan requirement baru  
**Status:** Terverifikasi dari source code | **Confidence:** High untuk fitur terimplementasi

> [!IMPORTANT]
> PRD ini mendokumentasikan PERILAKU AKTUAL yang ditemukan di kode. Bukan requirement yang diusulkan. Setiap requirement memiliki status verifikasi.

---

## 1. Latar Belakang

PT. KMH (Kerinci Hydropower) adalah perusahaan pembangkit listrik tenaga air (PLTA) yang membutuhkan sistem untuk mengelola aset IT di berbagai area operasional (DAM, Power House, Adit, dll). Aset IT digunakan oleh karyawan dan dipasang di infrastruktur jaringan. Sistem ini menggantikan pengelolaan manual (spreadsheet) dengan aplikasi web terpusat.

*Sumber inferensi: AREA_CHOICES di models.py, judul halaman "Manajemen Aset IT - Kerinci Hydropower", logo dalam static/img/*

---

## 2. Tujuan Sistem (Terverifikasi)

| ID | Tujuan | Bukti | Status |
|---|---|---|---|
| OBJ-01 | Mencatat inventaris aset IT per jenis dan per unit fisik | `Asset`, `AssetUnit` models | Terverifikasi |
| OBJ-02 | Mengelola distribusi aset ke karyawan | `AssetAssignment` model, distribusi views | Terverifikasi |
| OBJ-03 | Menyimpan riwayat historis setiap unit | `UnitLog` model | Terverifikasi |
| OBJ-04 | Monitoring status aset real-time | `status_aset_list` view | Terverifikasi |
| OBJ-05 | Menghasilkan laporan dalam PDF dan Excel | Export views | Terverifikasi |
| OBJ-06 | Identifikasi unit via QR code yang dapat di-scan | `unit_qr_code`, `unit_public_detail` | Terverifikasi |
| OBJ-07 | Pengelolaan data karyawan terintegrasi | `Employee` model dan views | Terverifikasi |

---

## 3. Aktor/Pengguna

| Aktor | Deskripsi | Hak Akses | Status |
|---|---|---|---|
| **Administrator IT** | Pengguna sistem satu-satunya — staff IT yang mengelola semua aset | Akses penuh ke semua fitur | Terverifikasi |
| **Publik (tanpa login)** | Siapapun yang men-scan QR code | Hanya bisa melihat detail unit publik (`/public/unit/{uuid}/`) | Terverifikasi |

> [!NOTE]
> Tidak ada implementasi multi-role atau multi-user. Semua Django user yang login memiliki akses yang sama. Tidak ada pembedaan antara "read-only" dan "admin".

---

## 4. Daftar Modul

| ID | Modul | Deskripsi | Status |
|---|---|---|---|
| MOD-01 | Dashboard | Ringkasan statistik dan log aktivitas terbaru | Implemented |
| MOD-02 | Manajemen Aset | CRUD jenis aset (master data) | Implemented |
| MOD-03 | Unit Aset | CRUD unit fisik per aset | Implemented |
| MOD-04 | Distribusi Aset | Serah terima, mutasi, pengembalian | Implemented |
| MOD-05 | Status Aset | Monitor status per unit | Implemented |
| MOD-06 | Riwayat Unit | Timeline audit trail unit | Implemented |
| MOD-07 | Data Karyawan | CRUD karyawan | Implemented |
| MOD-08 | QR Code | Generate dan halaman publik | Implemented |
| MOD-09 | Export Laporan | PDF dan Excel untuk semua modul | Implemented |
| MOD-10 | Backup Data | Export JSON/SQL seluruh database | Implemented |
| MOD-11 | Profil Akun | Edit profil dan ubah password | Implemented |

---

## 5. Functional Requirements

### 5.1 Autentikasi (FR-AUTH)

| ID | Requirement | Status | Bukti |
|---|---|---|---|
| FR-AUTH-01 | Sistem menyediakan halaman login dengan username dan password | Implemented | `login_view`, `templates/login.html` |
| FR-AUTH-02 | Semua halaman utama memerlukan autentikasi — redirect ke login jika belum login | Implemented | `@login_required` decorator pada views |
| FR-AUTH-03 | Sistem menyediakan fungsi logout | Implemented | `logout_view`, form logout di `base.html` |
| FR-AUTH-04 | Administrator dapat mengubah profil (nama depan, nama belakang, username, email) | Implemented | `profile_view`, `templates/profile.html` |
| FR-AUTH-05 | Administrator dapat mengubah password (verifikasi password lama) | Implemented | `profile_view`, form update_password |
| FR-AUTH-06 | Django admin dapat dibuat via management command `setup_superuser` | Implemented | `assets/management/commands/setup_superuser.py` |

### 5.2 Dashboard (FR-DASH)

| ID | Requirement | Status | Bukti |
|---|---|---|---|
| FR-DASH-01 | Dashboard menampilkan jumlah unit aset karyawan | Implemented | `dashboard` view L19 |
| FR-DASH-02 | Dashboard menampilkan jumlah unit aset network | Implemented | `dashboard` view L20 |
| FR-DASH-03 | Dashboard menampilkan jumlah unit per status (tersedia, digunakan, maintenance) | Implemented | `dashboard` view L22-25 |
| FR-DASH-04 | Dashboard menampilkan 5 log serah terima terbaru | Implemented | `recent_handovers` L28 |
| FR-DASH-05 | Dashboard menampilkan 3 log mutasi terbaru | Implemented | `recent_mutations` L29 |
| FR-DASH-06 | Dashboard menampilkan 3 log pengembalian terbaru | Implemented | `recent_returns` L30 |
| FR-DASH-07 | Kartu statistik dapat diklik sebagai shortcut ke halaman detail | Implemented | Link di `dashboard.html` L18, 26, 34 |

### 5.3 Manajemen Aset / Asset (FR-ASSET)

| ID | Requirement | Status | Bukti |
|---|---|---|---|
| FR-ASSET-01 | Sistem menampilkan daftar aset dengan tab Karyawan dan Network | Implemented | `asset_list`, query filter L63-66 |
| FR-ASSET-02 | Pengguna dapat mencari aset berdasarkan kode, nama, atau merek | Implemented | `asset_list` L56-61 |
| FR-ASSET-03 | Daftar aset menampilkan jumlah unit tersedia dan digunakan (annotated count) | Implemented | `asset_list` L50-54 |
| FR-ASSET-04 | Pengguna dapat menambahkan jenis aset baru | Partially Implemented | `asset_add` view — **tidak ada `@login_required`** |
| FR-ASSET-05 | Pengguna dapat mengedit jenis aset | Implemented | `asset_edit` view |
| FR-ASSET-06 | Jika kode aset berubah, semua unit_code anak diperbarui otomatis | Implemented | `Asset.save()` custom method |
| FR-ASSET-07 | Pengguna dapat menghapus jenis aset | Implemented | `asset_delete` view |
| FR-ASSET-08 | Sistem dapat mengekspor daftar aset ke PDF | Implemented | `asset_export_pdf` |
| FR-ASSET-09 | Sistem dapat mengekspor daftar aset ke Excel | Implemented | `asset_export_excel` |

### 5.4 Unit Aset (FR-UNIT)

| ID | Requirement | Status | Bukti |
|---|---|---|---|
| FR-UNIT-01 | Setiap aset memiliki daftar unit fisik | Implemented | `asset_units` view |
| FR-UNIT-02 | Pengguna dapat menambah unit fisik baru dengan suffix kode | Implemented | `unit_add` |
| FR-UNIT-03 | Unit code diformat otomatis: `{asset_code}-{suffix}` | Implemented | `unit_add` L285 |
| FR-UNIT-04 | Unit code harus unik di seluruh sistem | Implemented | unique constraint + validasi di view |
| FR-UNIT-05 | Pengguna dapat mengedit unit (kode, status, assigned_to) | Implemented | `unit_edit` |
| FR-UNIT-06 | Edit unit mencatat log otomatis berdasarkan perubahan status | Implemented | `unit_edit` L326-346 |
| FR-UNIT-07 | Pengguna dapat menghapus unit | Potentially Defective | `unit_delete` view ada tapi **tidak ada URL pattern** |
| FR-UNIT-08 | Setiap unit memiliki UUID unik untuk QR code | Implemented | `AssetUnit.id_uuid` |
| FR-UNIT-09 | Sistem dapat mengekspor daftar unit ke PDF dan Excel | Implemented | `asset_units_export_pdf`, `asset_units_export_excel` |
| FR-UNIT-10 | Update status unit (tersedia/rusak) untuk aset network memperbarui area dan lokasi | Implemented | `unit_update_status` |

### 5.5 Distribusi Aset (FR-DIST)

| ID | Requirement | Status | Bukti |
|---|---|---|---|
| FR-DIST-01 | Pengguna dapat melakukan serah terima aset ke karyawan | Implemented | `distribusi_handover` |
| FR-DIST-02 | Serah terima mengubah status unit menjadi "digunakan" dan menetapkan assigned_to | Implemented | `distribusi_handover` L598-600 |
| FR-DIST-03 | Pengguna dapat melakukan mutasi aset antar karyawan | Implemented | `distribusi_mutation` |
| FR-DIST-04 | Pengguna dapat mencatat pengembalian aset | Implemented | `distribusi_return` |
| FR-DIST-05 | Setiap distribusi dapat dilampiri dokumen BAST | Implemented | `document` field di AssetAssignment |
| FR-DIST-06 | Dokumen BAST dapat diupload setelah transaksi dibuat | Implemented | `distribusi_upload_doc` |
| FR-DIST-07 | Upload dokumen dibatasi: PDF, DOC, DOCX, JPG, PNG, maksimal 5MB | Implemented | `distribusi_upload_doc` L696-702 |
| FR-DIST-08 | Daftar distribusi dapat difilter per tipe (serah terima/mutasi/pengembalian) | Implemented | `distribusi_list` tab filter |
| FR-DIST-09 | Daftar distribusi dapat dicari berdasarkan nama, kode unit, tanggal | Implemented | `distribusi_list` L507-549 |
| FR-DIST-10 | Setiap distribusi menghasilkan UnitLog otomatis | Implemented | UnitLog.create di setiap distribusi view |
| FR-DIST-11 | Distribusi menggunakan `@transaction.atomic` untuk konsistensi | Implemented | Semua distribusi views |
| FR-DIST-12 | Distribusi hanya tersedia untuk "Aset Karyawan" | Partially Implemented | `distribusi_list` L557-558 hardcoded filter |

### 5.6 Status Aset (FR-STATUS)

| ID | Requirement | Status | Bukti |
|---|---|---|---|
| FR-STATUS-01 | Sistem menampilkan semua unit berdasarkan status | Implemented | `status_aset_list` |
| FR-STATUS-02 | Filter berdasarkan kategori (Karyawan/Network) dan status | Implemented | cat_filter dan tab di `status_aset_list` |
| FR-STATUS-03 | Pencarian unit berdasarkan kode, nama aset, nama karyawan, area, lokasi | Implemented | `status_aset_list` L470-479 |
| FR-STATUS-04 | Sistem dapat mengekspor status aset ke PDF dan Excel | Implemented | export views |

### 5.7 Riwayat Unit (FR-HIST)

| ID | Requirement | Status | Bukti |
|---|---|---|---|
| FR-HIST-01 | Setiap unit memiliki halaman riwayat berupa timeline | Implemented | `unit_history` view |
| FR-HIST-02 | Riwayat menampilkan nama karyawan yang sudah dihapus | Implemented | Parsing regex di `unit_history` L428-438 |
| FR-HIST-03 | Riwayat dapat diekspor ke PDF dan Excel | Implemented | export views |

### 5.8 Data Karyawan (FR-EMP)

| ID | Requirement | Status | Bukti |
|---|---|---|---|
| FR-EMP-01 | Sistem menampilkan daftar karyawan dengan jumlah aset yang dipegang | Implemented | `employee_list` dengan annotate Count |
| FR-EMP-02 | Pencarian karyawan berdasarkan nama atau NIK | Implemented | `employee_list` L718-722 |
| FR-EMP-03 | Pengguna dapat menambah karyawan baru (NIK, nama, jabatan) | Implemented | `employee_create` |
| FR-EMP-04 | NIK harus unik per karyawan | Implemented | unique constraint + validasi view |
| FR-EMP-05 | Pengguna dapat mengedit data karyawan | Implemented | `employee_edit` |
| FR-EMP-06 | Pengguna tidak dapat menghapus karyawan yang masih memegang aset | Implemented | `employee_delete` L788-789 |
| FR-EMP-07 | Saat karyawan dihapus, nama-NIK diembed ke UnitLog notes | Implemented | `employee_delete` L792-796 |
| FR-EMP-08 | Halaman detail karyawan menampilkan aset yang sedang dipegang | Implemented | `employee_detail` |
| FR-EMP-09 | Laporan karyawan dapat diekspor ke PDF dan Excel | Implemented | export views |

### 5.9 QR Code & Halaman Publik (FR-QR)

| ID | Requirement | Status | Bukti |
|---|---|---|---|
| FR-QR-01 | Setiap unit dapat di-generate QR code-nya | Implemented | `unit_qr_code` view |
| FR-QR-02 | QR code berisi URL ke halaman publik unit | Implemented | URL `/public/unit/{uuid}/` |
| FR-QR-03 | QR code menampilkan nama aset dan kode unit sebagai teks | Implemented | `unit_qr_code` L813-814 |
| FR-QR-04 | Halaman publik dapat diakses tanpa login | Implemented | `unit_public_detail` tanpa `@login_required` |
| FR-QR-05 | Halaman publik menampilkan info unit dan riwayat log | Implemented | `unit_public_detail` L848-854 |

### 5.10 Backup (FR-BACKUP)

| ID | Requirement | Status | Bukti |
|---|---|---|---|
| FR-BACKUP-01 | Sistem menyediakan fitur backup data ke format JSON (Django dumpdata) | Unverified | Template backup.html menunjukkan opsi ini; implementasi view belum terbaca penuh |
| FR-BACKUP-02 | Sistem menyediakan backup ke format SQL (mysqldump) | Unverified | Template backup.html menunjukkan opsi SQL; implementasi belum diverifikasi |

---

## 6. Non-Functional Requirements (Terverifikasi)

| ID | Requirement | Status | Bukti |
|---|---|---|---|
| NFR-01 | Bahasa antarmuka: Bahasa Indonesia | Implemented | `LANGUAGE_CODE = 'id-id'`, semua label dalam Bahasa Indonesia |
| NFR-02 | Timezone: Asia/Jakarta | Implemented | `TIME_ZONE = 'Asia/Jakarta'` di settings.py |
| NFR-03 | Desain responsif (mobile dan desktop) | Implemented | TailwindCSS responsive classes di templates |
| NFR-04 | Keamanan: CSRF protection aktif | Implemented | `CsrfViewMiddleware`, CSRF token di semua form |
| NFR-05 | Keamanan: Security headers aktif di production | Implemented | Settings HSTS, NOSNIFF, cookie secure saat DEBUG=False |
| NFR-06 | Log error ke file `error.log` di root project | Implemented | LOGGING config di settings.py L175-179 |
| NFR-07 | Static files serving via WhiteNoise | Implemented | `whitenoise.middleware.WhiteNoiseMiddleware` |
| NFR-08 | Konfigurasi via environment variables | Implemented | `.env.example`, `python-dotenv` |

---

## 7. Business Rules

| ID | Aturan | Bukti | Status |
|---|---|---|---|
| BR-01 | Kode aset harus unik, uppercase | `Asset.asset_code unique=True`, `asset_code.upper()` di views | Terverifikasi |
| BR-02 | NIK karyawan harus unik | `Employee.nik unique=True` | Terverifikasi |
| BR-03 | Unit code harus unik di seluruh sistem | `AssetUnit.unit_code unique=True` | Terverifikasi |
| BR-04 | Karyawan yang masih memegang aset tidak dapat dihapus | `employee_delete` L788-789 | Terverifikasi |
| BR-05 | Setiap perubahan status unit menghasilkan UnitLog | Semua status-change views | Terverifikasi |
| BR-06 | Serah terima mengubah status unit menjadi "digunakan" | `distribusi_handover` L598-600 | Terverifikasi |
| BR-07 | Pengembalian aset mengubah status menjadi "tersedia" dan assigned_to menjadi null | `distribusi_return` L675-677 | Terverifikasi |
| BR-08 | Aset dengan kategori "Network" memerlukan area dan lokasi saat digunakan/rusak | `unit_update_status` L368-388 | Terverifikasi |
| BR-09 | Dokumen upload maksimal 5MB dan hanya tipe tertentu | `distribusi_upload_doc` L700-702 | Terverifikasi |
| BR-10 | Distribusi formal (serah terima) menggunakan transaction.atomic | `@transaction.atomic` decorator | Terverifikasi |
| BR-11 | Unit tidak dapat dihapus jika masih ada AssetAssignment (PROTECT) | `AssetAssignment.unit ON_DELETE=PROTECT` | Terverifikasi |
| BR-12 | QR code halaman publik dapat diakses siapapun tanpa login | `unit_public_detail` tanpa `@login_required` | Terverifikasi (by design) |

---

## 8. Alur Kerja Pengguna

### 8.1 Alur Tambah Aset Baru + Unit

```
1. Login sebagai Administrator
2. Navigasi ke "Daftar Aset"
3. Klik "Tambah Aset" → Isi kategori, kode, nama, merek, satuan
4. Sistem validasi kode unik → Simpan Asset
5. Klik pada aset → masuk ke halaman "Unit Aset"
6. Klik "Tambah Unit" → Isi suffix kode (misal: 001)
7. Sistem membuat unit dengan kode format "{asset_code}-001"
8. UnitLog dibuat: action='created'
9. Asset.qty diperbarui
```

### 8.2 Alur Serah Terima Aset ke Karyawan

```
1. Navigasi ke "Distribusi Aset" tab "Serah Terima"
2. Klik "Serah Terima Baru"
3. Pilih unit (dari dropdown unit tersedia)
4. Pilih karyawan penerima
5. Isi tanggal serah terima, catatan (opsional), dokumen BAST (opsional)
6. Submit → transaction.atomic:
   a. AssetAssignment dibuat (type='handover')
   b. AssetUnit.status → 'digunakan'
   c. AssetUnit.assigned_to → karyawan terpilih
   d. UnitLog dibuat (action='assigned')
7. Redirect ke daftar distribusi tab handover
```

### 8.3 Alur Mutasi Aset

```
1. Navigasi ke "Distribusi Aset" tab "Mutasi"
2. Klik "Mutasi Baru"
3. Pilih unit yang sedang digunakan
4. Sistem otomatis mengisi from_employee dari assigned_to unit
5. Pilih karyawan penerima baru
6. Submit → transaction.atomic:
   a. AssetAssignment dibuat (type='mutation', from_employee=pemegang lama)
   b. AssetUnit.assigned_to → karyawan baru
   c. UnitLog: action='returned' (pemegang lama)
   d. UnitLog: action='assigned' (pemegang baru)
```

### 8.4 Alur Pengembalian Aset

```
1. Navigasi ke "Distribusi Aset" tab "Pengembalian"
2. Pilih unit yang dikembalikan
3. Isi tanggal dan catatan
4. Submit → transaction.atomic:
   a. AssetAssignment dibuat (type='return')
   b. AssetUnit.status → 'tersedia'
   c. AssetUnit.assigned_to → None
   d. UnitLog: action='returned'
```

---

## 9. Batasan dan Asumsi

- **Satu pengguna admin:** Sistem tidak mendukung multi-user dengan role berbeda
- **Dua kategori aset:** "Aset Karyawan" dan "Aset Network" — hardcoded dalam logika bisnis
- **Area hardcoded:** Lokasi area (RW, DAM, PH, dll) adalah choices statis, bukan data master
- **Tidak ada notifikasi:** Tidak ada email, push notif, atau alert otomatis
- **Tidak ada pagination:** Semua list ditampilkan sekaligus tanpa paging
- **Distribusi hanya untuk aset Karyawan:** Logika distribusi di `distribusi_list` view memfilter hanya unit Karyawan
