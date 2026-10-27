# 06 — API & URL Documentation

**Tanggal Analisis:** 26 Oktober 2026  
**Sumber:** `itam_core/urls.py`, `assets/views.py`  
**Status:** Terverifikasi dari source code

> [!NOTE]
> Aplikasi ini **tidak memiliki REST API**. Semua endpoint adalah traditional Django views yang menghasilkan HTML response atau file download (PDF/Excel/Image). HTMX digunakan untuk partial page updates, bukan REST API JSON.

---

## 1. Katalog URL Lengkap

| # | Method | URL Pattern | View Function | Auth | Output | Keterangan |
|---|---|---|---|---|---|---|
| 1 | GET | `/` | `dashboard` | Login | HTML | Dashboard utama |
| 2 | GET/POST | `/login/` | `login_view` | Public | HTML/Redirect | Login page |
| 3 | POST | `/logout/` | `logout_view` | Login | Redirect | Logout |
| 4 | GET/POST | `/profil/` | `profile_view` | Login | HTML/Redirect | Edit profil & password |
| 5 | GET/POST | `/backup/` | `backup_database_view` | Superuser | HTML/File | Backup database |
| 6 | GET | `/404/` | `custom_404_view` | Public | HTML | Test 404 |
| 7 | GET | `/aset/` | `asset_list` | Login | HTML | Daftar aset (tab Karyawan/Network) |
| 8 | GET | `/aset/export/` | `asset_export_pdf` | Login | PDF | Export PDF daftar aset |
| 9 | GET | `/aset/export-excel/` | `asset_export_excel` | Login | XLSX | Export Excel daftar aset |
| 10 | GET/POST | `/aset/add/` | `asset_add` | **❌ No Auth!** | JSON/Redirect | Tambah aset baru |
| 11 | GET/POST | `/aset/<int:asset_id>/edit/` | `asset_edit` | Login | JSON/Redirect | Edit aset |
| 12 | GET/POST | `/aset/<int:asset_id>/delete/` | `asset_delete` | Login | Redirect | Hapus aset |
| 13 | GET | `/aset/<int:asset_id>/units/` | `asset_units` | Login | HTML | Daftar unit per aset |
| 14 | GET | `/aset/<int:asset_id>/units/export/` | `asset_units_export_pdf` | Login | PDF | Export PDF unit |
| 15 | GET | `/aset/<int:asset_id>/units/export-excel/` | `asset_units_export_excel` | Login | XLSX | Export Excel unit |
| 16 | POST | `/aset/<int:asset_id>/units/add/` | `unit_add` | Login | JSON/Redirect | Tambah unit fisik |
| 17 | POST | `/unit/<int:unit_id>/edit/` | `unit_edit` | Login | JSON/Redirect | Edit unit |
| 18 | POST | `/unit/<int:unit_id>/status/` | `unit_update_status` | Login | Redirect | Update status unit |
| 19 | GET | `/unit/<int:unit_id>/history/` | `unit_history` | Login | HTML | Riwayat/history unit |
| 20 | GET | `/unit/<int:unit_id>/history/export/` | `unit_history_export_pdf` | Login | PDF | Export PDF riwayat |
| 21 | GET | `/unit/<int:unit_id>/history/export-excel/` | `unit_history_export_excel` | Login | XLSX | Export Excel riwayat |
| 22 | GET | `/status-aset/` | `status_aset_list` | Login | HTML | Status semua unit |
| 23 | GET | `/status-aset/export/` | `status_aset_export_pdf` | Login | PDF | Export PDF status |
| 24 | GET | `/status-aset/export-excel/` | `status_aset_export_excel` | Login | XLSX | Export Excel status |
| 25 | GET | `/distribusi/` | `distribusi_list` | Login | HTML | Daftar distribusi |
| 26 | GET | `/distribusi/export/` | `distribusi_export_pdf` | Login | PDF | Export PDF distribusi |
| 27 | GET | `/distribusi/export-excel/` | `distribusi_export_excel` | Login | XLSX | Export Excel distribusi |
| 28 | POST | `/distribusi/handover/` | `distribusi_handover` | Login | Redirect | Serah terima aset |
| 29 | POST | `/distribusi/mutation/` | `distribusi_mutation` | Login | Redirect | Mutasi aset |
| 30 | POST | `/distribusi/return/` | `distribusi_return` | Login | Redirect | Pengembalian aset |
| 31 | POST | `/distribusi/<int:assignment_id>/upload/` | `distribusi_upload_doc` | Login | Redirect | Upload dokumen BAST |
| 32 | GET | `/karyawan/` | `employee_list` | Login | HTML | Daftar karyawan |
| 33 | GET | `/karyawan/export/` | `employee_export_pdf` | Login | PDF | Export PDF karyawan |
| 34 | GET | `/karyawan/export-excel/` | `employee_export_excel` | Login | XLSX | Export Excel karyawan |
| 35 | GET/POST | `/karyawan/buat/` | `employee_create` | Login | JSON/Redirect | Tambah karyawan |
| 36 | GET | `/karyawan/<int:emp_id>/` | `employee_detail` | Login | HTML | Detail karyawan |
| 37 | GET | `/karyawan/<int:emp_id>/export/` | `employee_detail_export_pdf` | Login | PDF | Export PDF detail karyawan |
| 38 | GET | `/karyawan/<int:emp_id>/export-excel/` | `employee_detail_export_excel` | Login | XLSX | Export Excel detail karyawan |
| 39 | POST | `/karyawan/<int:emp_id>/edit/` | `employee_edit` | Login | JSON/Redirect | Edit karyawan |
| 40 | POST | `/karyawan/<int:emp_id>/delete/` | `employee_delete` | Login | Redirect | Hapus karyawan |
| 41 | GET | `/qr/<uuid:uuid>/` | `unit_qr_code` | Public | PNG Image | Generate QR code unit |
| 42 | GET | `/public/unit/<uuid:uuid>/` | `unit_public_detail` | Public | HTML | Detail unit publik |

---

## 2. URL yang Ada di Views tapi TIDAK di URL Patterns

| View | Baris | Keterangan |
|---|---|---|
| `unit_delete` | L410 | View ada tapi tidak ada URL → fungsi tidak dapat diakses |

---

## 3. Query Parameters yang Digunakan

| URL | Parameter | Nilai | Efek |
|---|---|---|---|
| `/aset/` | `tab` | `karyawan` (default), `network` | Filter kategori aset |
| `/aset/` | `q` | string | Search kode/nama/merek |
| `/aset/export/` | `tab` | `karyawan`, `network` | Filter PDF export |
| `/aset/export-excel/` | `tab` | `karyawan`, `networking`, `all` | Filter Excel export |
| `/aset/export-excel/` | `q` | string | Search filter |
| `/aset/{id}/units/export-excel/` | `tab` | `semua`, `tersedia`, `digunakan`, `rusak` | Filter status unit |
| `/status-aset/` | `tab` | `tersedia` (default), `digunakan`, `rusak` | Filter status |
| `/status-aset/` | `cat` | `karyawan` (default), `network` | Filter kategori |
| `/status-aset/` | `q` | string | Search unit/aset/karyawan |
| `/distribusi/` | `tab` | `handover` (default), `mutation`, `return` | Filter tipe distribusi |
| `/distribusi/` | `q` | string | Search multi-field |
| `/distribusi/` | `sort` | `desc` (default), `asc` | Urutan tanggal |
| `/distribusi/export/` | `tab` | `handover`, `mutation`, `return` | Filter PDF export |
| `/karyawan/` | `q` | string | Search nama/NIK |

---

## 4. Response Pattern Views (HTMX/AJAX)

Beberapa views merespons secara berbeda berdasarkan header request:

```python
# Deteksi HTMX/AJAX request
if request.headers.get('Accept') == 'application/json' or 
   request.headers.get('x-requested-with') == 'XMLHttpRequest':
    return JsonResponse({'status': 'success'})  # atau {'success': True/False, 'error': '...'}
```

Views yang menggunakan pattern ini:
- `asset_add` → `JsonResponse({'success': True/False, 'error': '...'})`
- `asset_edit` → `JsonResponse({'success': True/False, 'error': '...'})`
- `unit_add` → `JsonResponse({'status': 'success'/'error', 'message': '...'})`
- `unit_edit` → `JsonResponse({'status': 'success'/'error', 'message': '...'})`
- `employee_create` → `JsonResponse({'status': 'success'/'error', 'message': '...'})`
- `employee_edit` → `JsonResponse({'status': 'success'/'error', 'message': '...'})`

> [!NOTE]
> Tidak ada konsistensi format response JSON. `asset_add/edit` menggunakan `{'success': True}` sementara `unit_add/edit` dan `employee_*` menggunakan `{'status': 'success'}`.

---

## 5. File Upload Endpoints

| URL | Field | Tipe Diizinkan | Ukuran Maks | Simpan Di |
|---|---|---|---|---|
| `POST /distribusi/handover/` | `document` | Tidak dibatasi di sini | Tidak dibatasi di sini | `media/bast_documents/` |
| `POST /distribusi/mutation/` | `document` | Tidak dibatasi di sini | Tidak dibatasi di sini | `media/bast_documents/` |
| `POST /distribusi/return/` | `document` | Tidak dibatasi di sini | Tidak dibatasi di sini | `media/bast_documents/` |
| `POST /distribusi/{id}/upload/` | `document` | PDF, DOC, DOCX, JPG, JPEG, PNG | 5 MB | `media/bast_documents/` |

> [!WARNING]
> Upload dokumen saat distribusi (handover/mutation/return) **tidak divalidasi** tipe dan ukurannya. Hanya `distribusi_upload_doc` yang memiliki validasi. Ini adalah inkonsistensi — handover/mutation/return dapat menerima file apa saja.

---

## 6. Catatan Keamanan URL

| Temuan | URL | Detail |
|---|---|---|
| Tidak ada rate limiting | `/login/` | Brute force tidak dicegah |
| Tidak ada `@login_required` | `POST /aset/add/` | Siapapun dapat POST tambah aset |
| Open redirect check ada | `/login/?next=...` | `url_has_allowed_host_and_scheme` digunakan |
| Media files hanya tersedia di DEBUG | `MEDIA_URL` | `if settings.DEBUG: urlpatterns += static(...)` — production perlu konfigurasi webserver |

---

## 7. Handler Error

```python
# itam_core/urls.py L64
handler404 = 'assets.views.custom_404_view'
```

- Handler 404 custom menggunakan template `404.html`
- Handler 500 tidak dikustomisasi — menggunakan default Django

---

## 8. Django Admin

```python
# itam_core/urls.py L20 — DIKOMENTARI
# path('admin/', admin.site.urls),  # Django Admin dinonaktifkan
```

- Django Admin **tidak dapat diakses** dari URL manapun
- Model tetap terdaftar di `admin.py` (Employee, Category, Asset, AssetUnit, AssetAssignment)
- Admin header dikustomisasi (L10-12 di urls.py):
  - `site_header = "Administrasi IT All Role PT. KMH"`
  - `site_title = "Admin Portal IT"`
  - `index_title = "Manajemen Database Inti"`

> [!NOTE]
> Mengaktifkan kembali Django Admin memerlukan uncomment baris L20 di `urls.py`. Semua model sudah terdaftar dan siap digunakan.
