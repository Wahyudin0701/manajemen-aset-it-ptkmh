# 09 — Test Strategy & Test Plan

**Tanggal Analisis:** 26 Oktober 2026  
**Kondisi Eksisting:** 0% Automated Test (`assets/tests.py` hanya 4 baris template default)  
**Status Verifikasi:** Terverifikasi via code audit statis  

---

## 1. Analisis Kesenjangan Pengujian (Testing Gap Analysis)

Repository saat ini **sama sekali tidak memiliki pengujian otomatis (automated test)**.
Bukti langsung pada `assets/tests.py`:
```python
from django.test import TestCase

# Create your tests here.
```

Ketiadaan test suite ini menimbulkan risiko regresi yang sangat tinggi, terutama karena sistem mengelola:
1. Siklus hidup unit aset (status change logic).
2. Perubahan kode aset induk yang mentranslasikan suffix ke ratusan unit turunan (`Asset.save()`).
3. Transaksi distribusi serah terima, mutasi antar-karyawan, dan pengembalian unit.
4. Parsing riwayat penghapusan data karyawan berbasis Regular Expression.

---

## 2. Strategi Pengujian yang Direkomendasikan (Test Strategy)

Pengujian harus dibagi menjadi 3 piramida pengujian:

```
          / \
         / E2E \       (Playwright / Cypress untuk UI Flow Kritis)
        /-------\
       / Integr- \     (View & Request-Response Tests, Transaction Rollback)
      /   ation   \
     /-------------\
    /  Unit Testing \  (Model validations, logic helpers, formatters, export builders)
   /-----------------\
```

### 2.1 Framework dan Tools
- **Test Runner:** `pytest` + `pytest-django` (lebih ekspresif dan cepat dibanding default `unittest/TestCase`).
- **Mocking & Factory:** `factory_boy` untuk pembuatan data dummy model yang terisolasi tanpa bergantung pada fixture statis.
- **Coverage Tool:** `pytest-cov` dengan ambang batas target minimum 80% line coverage.
- **Database:** Gunakan database SQLite in-memory untuk eksekusi test cepat pada CI, atau MySQL test container khusus.

---

## 3. Matriks Test Case Prioritas Tinggi (Critical Test Cases)

Berikut daftar skenario pengujian yang **wajib dibuat sebelum memulai perubahan atau penambahan fitur**:

### 3.1 Modul Autentikasi & Kontrol Akses (Security & Auth)
| Test ID | Skenario Pengujian | Input / Kondisi | Ekspektasi Hasil |
|---|---|---|---|
| TC-AUTH-01 | Login pengguna valid | Username & password terdaftar | Status code 302 redirect ke `/`, session auth terisi |
| TC-AUTH-02 | Login dengan Email | Format email terdaftar di User | Berhasil login dan redirect ke dashboard |
| TC-AUTH-03 | Login kredensial salah | Password salah | Status 200, pesan error muncul di context |
| TC-AUTH-04 | Proteksi URL anonim | Mengakses `/aset/` tanpa login | Redirect 302 ke `/login/?next=/aset/` |
| TC-AUTH-05 | **Bug Verification: `asset_add`** | Mengirim POST ke `/aset/add/` tanpa session login | **Harus ditolak (401/302). Saat ini lolos (Bug SEC-001)!** |
| TC-AUTH-06 | Akses Backup Database | User biasa (bukan superuser) akses `/backup/` | Mengembalikan status 403 Forbidden |
| TC-AUTH-07 | Detail Publik QR Code | Mengakses `/public/unit/<uuid>/` tanpa login | Status 200 OK (Akses publik diizinkan) |

### 3.2 Modul Master Aset & Siklus Unit Fisik
| Test ID | Skenario Pengujian | Input / Kondisi | Ekspektasi Hasil |
|---|---|---|---|
| TC-AST-01 | Pembuatan jenis aset unik | Kode aset baru `"CCTV-EXT"` | Record tersimpan, status 200/JsonResponse success |
| TC-AST-02 | Validasi duplikasi kode aset | Kode aset yang sudah ada | Ditolak dengan pesan error validasi |
| TC-AST-03 | Pembuatan unit fisik | Suffix `"001"` pada aset `"CCTV-EXT"` | Terbentuk unit `"CCTV-EXT-001"` dengan status `"tersedia"`, `UnitLog` `"created"` otomatis tercipta |
| TC-AST-04 | Sinkronisasi perubahan kode aset induk | Ubah kode aset `"LAPTOP"` jadi `"NB"` | Seluruh unit turunan `"LAPTOP-001"` otomatis berubah menjadi `"NB-001"` via atomic transaction |
| TC-AST-05 | Resolusi benturan kode unit anak | Update kode induk yang unit tujuannya sudah ada | Penambahan counter otomatis `002`, `003` tanpa duplicate key error |

### 3.3 Modul Distribusi Aset (Handover, Mutasi, Return)
| Test ID | Skenario Pengujian | Input / Kondisi | Ekspektasi Hasil |
|---|---|---|---|
| TC-DIST-01 | Serah terima unit tersedia | Unit status `"tersedia"`, Karyawan A | Unit status menjadi `"digunakan"`, `assigned_to` = Karyawan A, `AssetAssignment` type `"handover"`, `UnitLog` `"assigned"` terbuat |
| TC-DIST-02 | Mutasi aset antar karyawan | Unit dipegang Karyawan A, dimutasi ke Karyawan B | Unit `assigned_to` berganti ke Karyawan B, `AssetAssignment` type `"mutation"` (from A to B), 2 baris `UnitLog` terbuat (returned & assigned) |
| TC-DIST-03 | Pengembalian unit ke gudang | Unit dipegang Karyawan B dikembalikan | Unit status kembali `"tersedia"`, `assigned_to` = `None`, `AssetAssignment` type `"return"`, `UnitLog` `"returned"` terbuat |
| TC-DIST-04 | Atomic Rollback saat gagal distribusi | Error di tengah proses penyimpanan | State database tidak berubah (unit tidak menggantung pada status yang salah) |

### 3.4 Modul Karyawan & Integritas Relasi
| Test ID | Skenario Pengujian | Input / Kondisi | Ekspektasi Hasil |
|---|---|---|---|
| TC-EMP-01 | Hapus karyawan yang memegang aset | Karyawan dengan `held_units.count() > 0` | Ditolak, karyawan tidak boleh terhapus |
| TC-EMP-02 | Hapus karyawan bebas tanggungan | Karyawan tanpa unit yang dipegang | Karyawan terhapus, log riwayat masa lalunya diperbarui dengan prefix teks nama & NIK |
| TC-EMP-03 | Validasi keunikan NIK | Input karyawan baru dengan NIK sama | Ditolak dengan response error NIK sudah terdaftar |

### 3.5 Modul Laporan & File Upload
| Test ID | Skenario Pengujian | Input / Kondisi | Ekspektasi Hasil |
|---|---|---|---|
| TC-DOC-01 | Validasi format file BAST | Upload file `.exe` atau `.sh` | Ditolak dengan pesan format tidak diizinkan |
| TC-DOC-02 | Validasi ukuran file BAST | Upload dokumen > 5MB | Ditolak dengan pesan ukuran maksimal 5MB |
| TC-REP-01 | Export PDF Aset | Request GET `/aset/export/?tab=karyawan` | Response `content_type='application/pdf'`, header attachment valid |
| TC-REP-02 | Export Excel Aset | Request GET `/aset/export-excel/` | Response `content_type='application/vnd.openxmlformats...'`, struktur spreadsheet valid |

---

## 4. Rencana Implementasi Test Suite (Test Execution Plan)

### Struktur Direktori Pengujian yang Disarankan:
```
assets/
└── tests/
    ├── __init__.py
    ├── factories.py           # Factory boy definitions
    ├── test_auth.py           # Login, logout, permission checks
    ├── test_models.py         # Model constraints & save() methods
    ├── test_views_asset.py    # CRUD Asset & AssetUnit
    ├── test_views_distribusi.py # Handover, mutation, return
    ├── test_views_employee.py # CRUD Employee & deletion guard
    ├── test_exports.py        # PDF & Excel response headers
    └── test_security.py       # Vulnerability regression tests
```

---

## 5. Kriteria Penerimaan Pengujian (Acceptance Gate)

Sebelum kode hasil upgrade atau bug fixing di-deploy ke environment staging/production:
1. **Zero Failing Tests:** 100% test case lulus (`pytest` returncode 0).
2. **Security Regression Pass:** Tidak ada view yang bisa diakses anonim tanpa dekorator resmi.
3. **Migration Check:** Perintah `python manage.py makemigrations --check --dry-run` menyatakan tidak ada migrasi yang tertinggal.
4. **Flake8 / Linter Clean:** Kode baru mematuhi standar formatting tanpa unresolved lint errors.
