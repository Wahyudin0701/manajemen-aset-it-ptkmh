# 07 — Security Audit Report

**Tanggal Analisis:** 26 Oktober 2026  
**Tipe Audit:** Code-level Static Analysis — BUKAN penetration testing aktif  
**Reviewer:** Automated via AI  
**Confidence Level:** Analisis statis — temuan belum diverifikasi secara runtime

> [!CAUTION]
> Dokumen ini mengandung informasi kerentanan. Simpan dengan aman dan batasi distribusinya.

---

## Ringkasan Temuan

| Severity | Confirmed | Suspected | Not Verified | Total |
|---|---|---|---|---|
| Critical | 0 | 0 | 0 | 0 |
| High | 2 | 1 | 0 | 3 |
| Medium | 4 | 2 | 1 | 7 |
| Low | 5 | 1 | 0 | 6 |
| Informational | 4 | 0 | 0 | 4 |
| **Total** | **15** | **4** | **1** | **20** |

---

## CONFIRMED FINDINGS

---

### SEC-001 — Broken Access Control: `asset_add` Tanpa Autentikasi

**Severity:** High  
**Confidence:** High  
**Status:** Confirmed

**File:** `assets/views.py` L192-212  
**URL:** `POST /aset/add/`

**Bukti teknis:**
```python
# L192 — tidak ada @login_required sebelum def
def asset_add(request):
    if request.method == 'POST':
        ...
        Asset.objects.create(...)
```

**Kondisi eksploitasi:** Siapapun yang mengetahui URL `POST /aset/add/` dengan payload yang benar dapat menambahkan data aset tanpa perlu login.

**Dampak:** Penyerang atau pengguna tidak sah dapat mengotori database dengan data sampah, menggunakan kode aset yang valid untuk keperluan jahat, atau mengganggu integritas data inventaris.

**Rekomendasi:**
```python
@login_required  # Tambahkan ini
def asset_add(request):
```

---

### SEC-002 — Broken Feature: `unit_delete` Tidak Dapat Diakses

**Severity:** High (Integrity risk)  
**Confidence:** High  
**Status:** Confirmed

**File:** `assets/views.py` L410, `itam_core/urls.py`

**Bukti teknis:**
```python
# views.py L410 — view ada
@login_required
def unit_delete(request, unit_id):
    ...

# urls.py — URL TIDAK TERDAFTAR
# Tidak ada: path('unit/<int:unit_id>/delete/', unit_delete, name='unit_delete')
```

**Dampak:** Fungsi hapus unit tidak dapat digunakan sama sekali. Jika ada tombol atau link "hapus unit" di frontend, kliknya akan menghasilkan 404.

**Rekomendasi:** Tambahkan URL pattern atau hapus view jika tidak diperlukan.

---

### SEC-003 — Double Decorator Anomali pada `asset_export_excel`

**Severity:** Medium  
**Confidence:** High  
**Status:** Confirmed

**File:** `assets/views.py` L84-91

**Bukti teknis:**
```python
@login_required        # L84 — dekorator kosong tanpa fungsi
                       # L85 — baris kosong
@login_required        # L86 — dekorator untuk asset_export_excel
def asset_export_excel(request):
```

**Dampak:** Fungsi tetap terlindungi (karena ada `@login_required` di L86), tapi `@login_required` di L84 tidak memiliki fungsi yang didekorasi — ini adalah kode yang tidak valid secara semantik. Dapat menimbulkan kebingungan developer.

---

### SEC-004 — File Upload Tanpa Validasi pada Distribusi Awal

**Severity:** Medium  
**Confidence:** High  
**Status:** Confirmed

**File:** `assets/views.py` L584-596, L619-633, L659-672

**Bukti teknis:**
```python
def distribusi_handover(request):
    ...
    document = request.FILES.get('document')
    AssetAssignment.objects.create(
        ...
        document=document  # Tidak ada validasi tipe/ukuran!
    )
```

**Kondisi eksploitasi:** Pengguna yang login dapat mengupload file jenis apapun (termasuk executable atau script) saat melakukan distribusi aset.

**Dampak:** Potensial untuk menyimpan file berbahaya di server. Tidak ada eksekusi otomatis, tapi file tersimpan di `media/bast_documents/`.

**Rekomendasi:** Terapkan validasi yang sama dengan `distribusi_upload_doc` (L696-702) ke semua distribusi views.

---

### SEC-005 — Tidak Ada Rate Limiting pada Login

**Severity:** Medium  
**Confidence:** High  
**Status:** Confirmed

**File:** `assets/views.py` L2442-2471

**Detail:** Tidak ada mekanisme pembatasan percobaan login (rate limiting, CAPTCHA, atau account lockout). Brute force attack terhadap akun admin tidak dicegah di level aplikasi.

**Rekomendasi:** Implementasikan `django-axes` atau custom rate limiting middleware.

---

### SEC-006 — Informasi Error Stacktrace di Response HTTP 500

**Severity:** Medium  
**Confidence:** High  
**Status:** Confirmed

**File:** `itam_core/settings.py` L30

**Detail:** `DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'yes')`. Jika `DJANGO_DEBUG=True` di production, Django akan menampilkan stacktrace penuh ke browser — mengekspos path file, konfigurasi, dan potensi informasi sensitif.

**Rekomendasi:** Pastikan `DJANGO_DEBUG=False` di environment production. Verifikasi dengan mengecek file `.env` di server.

---

### SEC-007 — File SQL Database di Repository

**Severity:** High  
**Confidence:** High  
**Status:** Confirmed

**File:** `database_lokal.sql`, `seed_karyawan.sql`

**Detail:** File SQL dump ada di root repository. `seed_karyawan.sql` kemungkinan berisi data karyawan (NIK, nama). File tidak dibuka untuk analisis.

**Dampak:** Jika repository bersifat publik (GitHub public), data karyawan terekspos. Bahkan jika private, tetap merupakan risiko jika ada yang mendapat akses ke repo.

**Rekomendasi:**
1. Pindahkan atau hapus file dari repository
2. Tambahkan ke `.gitignore`: `*.sql`, `database_lokal.sql`, `seed_karyawan.sql`
3. Jika sudah di git history, gunakan `git filter-repo` untuk membersihkan

---

### SEC-008 — Backup SQL via subprocess (Command Injection Risk)

**Severity:** Medium  
**Confidence:** Medium  
**Status:** Confirmed (implementasi ditemukan, exploitation condition perlu verifikasi)

**File:** `assets/views.py` L2551-2581

**Bukti teknis:**
```python
cmd = ['mysqldump', f'--user={db_user}', f'--host={db_host}', 
       f'--port={db_port}']
if db_pass:
    cmd.append(f'--password={db_pass}')
cmd.append(db_name)

result = subprocess.run(cmd, ...)
```

**Detail:** Menggunakan list form (tidak string interpolation langsung) → command injection via `subprocess` sangat kecil kemungkinannya. NAMUN nilai `db_user`, `db_host`, `db_port`, `db_name` datang dari environment variables — jika env variables bisa dimanipulasi, ada risiko. Lebih besar risikonya: password database terekspos di command line (dapat terlihat oleh `ps aux`).

**Rekomendasi:** Gunakan `~/.my.cnf` atau `--defaults-file` untuk credentials, bukan command line arguments.

---

### SEC-009 — Django Admin Terdaftar tapi URL Dinonaktifkan

**Severity:** Low  
**Confidence:** High  
**Status:** Confirmed — Informational

**File:** `urls.py` L20, `admin.py`

**Detail:** Django Admin masih terdaftar di `INSTALLED_APPS` dan semua model sudah terdaftar di `admin.py`. URL dikomentari. Risiko: jika seseorang uncomment URL admin tanpa mengatur akses, admin panel menjadi tersedia.

**Rekomendasi:** Jika admin tidak digunakan, hapus registrasi di `admin.py` dan hapus dari `INSTALLED_APPS`. Jika akan digunakan, pastikan HTTPS dan pastikan hanya diakses dari IP terbatas.

---

### SEC-010 — Fallback Secret Key Tidak Aman

**Severity:** Low  
**Confidence:** High  
**Status:** Confirmed

**File:** `itam_core/settings.py` L27

**Bukti teknis:**
```python
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-dev-key-change-in-production')
```

**Detail:** Ada fallback secret key hardcoded. Jika environment variable `DJANGO_SECRET_KEY` tidak diset di production (lupa konfigurasi), aplikasi akan berjalan dengan key insecure yang sama di semua instance.

**Rekomendasi:** Ganti fallback dengan raise `ValueError` agar deployment gagal daripada berjalan dengan key tidak aman:
```python
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY environment variable tidak diset!")
```

---

### SEC-011 — `ALLOWED_HOSTS` Default Kosong

**Severity:** Low  
**Confidence:** High  
**Status:** Confirmed

**File:** `itam_core/settings.py` L32

**Bukti teknis:**
```python
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',')
```

**Detail:** Jika `DJANGO_ALLOWED_HOSTS` tidak diset, `ALLOWED_HOSTS` akan menjadi `['']`. Pada Django dengan `DEBUG=False`, ini akan menyebabkan semua request ditolak. Dengan `DEBUG=True`, Django mengizinkan semua host.

**Rekomendasi:** Pastikan `DJANGO_ALLOWED_HOSTS` selalu diset di production `.env`.

---

### SEC-012 — Media Files Hanya Tersedia di DEBUG Mode

**Severity:** Low  
**Confidence:** High  
**Status:** Confirmed

**File:** `itam_core/urls.py` L60-61

**Bukti teknis:**
```python
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**Detail:** Ini adalah behavior yang benar — di production, media files harus dilayani oleh webserver (Nginx/Apache). Tapi jika webserver tidak dikonfigurasi dengan benar, dokumen BAST yang diupload tidak akan bisa diakses.

**Rekomendasi:** Pastikan deployment guide mendokumentasikan konfigurasi Nginx/Apache untuk serve `media/` directory.

---

### SEC-013 — Nama File Download Mengandung User Input

**Severity:** Low  
**Confidence:** Medium  
**Status:** Confirmed

**File:** `assets/views.py` (multiple export views)

**Contoh:**
```python
# L2062
response['Content-Disposition'] = f'inline; filename="Laporan_Aset_{employee.name.replace(" ", "_")}_{now.strftime("%Y%m%d")}.pdf"'
```

**Detail:** `employee.name` berasal dari database — bukan langsung dari user input, tapi jika ada karakter khusus di nama, bisa berpotensi header injection. Risiko rendah karena nama diambil dari database yang sudah tervalidasi saat insert.

---

### SEC-014 — Password di Command Line untuk mysqldump

**Severity:** Medium  
**Confidence:** High  
**Status:** Confirmed

**File:** `assets/views.py` L2566

**Bukti teknis:**
```python
cmd.append(f'--password={db_pass}')
```

**Detail:** Password database terekspos sebagai argumen command line. Pada sistem Linux/Unix, argumen proses dapat dilihat oleh user lain via `ps aux` atau `/proc/[pid]/cmdline`.

**Rekomendasi:** Gunakan environment variable `MYSQL_PWD` atau `--defaults-file` pointing ke file konfigurasi MySQL yang dibatasi aksesnya.

---

### SEC-015 — Tidak Ada CORS Configuration

**Severity:** Informational  
**Confidence:** High  
**Status:** Confirmed — Not Applicable

**Detail:** Aplikasi tidak menggunakan CORS karena tidak ada REST API. Semua request adalah same-origin. Tidak diperlukan konfigurasi CORS.

---

## SUSPECTED FINDINGS (Perlu Verifikasi)

---

### SEC-016 — Potensial N+1 Query di Dashboard

**Severity:** Medium  
**Confidence:** Medium  
**Status:** Suspected

**File:** `assets/views.py` L17-42

**Detail:** Dashboard menggunakan beberapa query terpisah. Akses ke `log.unit.asset.name` dan `log.employee` dalam loop template bisa menghasilkan N+1 queries jika `select_related` tidak mencakup semua relasi.

---

### SEC-017 — `CSRF_TRUSTED_ORIGINS` Default Kosong

**Severity:** Medium  
**Confidence:** Medium  
**Status:** Suspected

**File:** `itam_core/settings.py` L162

**Bukti teknis:**
```python
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')
```

**Detail:** Jika tidak diset, aplikasi di balik reverse proxy mungkin menolak request POST karena CSRF validation. Aplikasi mungkin tidak berjalan dengan baik di production jika ini tidak dikonfigurasi.

---

### SEC-018 — Halaman Publik Unit Mengekspos Riwayat Internal

**Severity:** Low  
**Confidence:** Medium  
**Status:** Suspected (tergantung kebijakan bisnis)

**File:** `assets/views.py` L847-854, `templates/unit_public_detail.html`

**Detail:** `unit_public_detail` menampilkan UnitLog kepada siapapun yang punya UUID. UnitLog bisa mengandung nama karyawan (meski yang sudah dihapus dalam format tertentu) dan catatan internal. Apakah ini disengaja?

**Pertanyaan untuk stakeholder:** Apakah riwayat lengkap unit harus terlihat publik, atau cukup info dasar?

---

### SEC-019 — File Scratch di Repository Mengekspos Path Development

**Severity:** Low  
**Confidence:** High  
**Status:** Confirmed

**File:** `scratch_urls_all.py` L3

**Bukti teknis:**
```python
with open('c:/laragon/www/Manajemen-Aset-IT/itam_core/urls.py', 'r', ...) as f:
```

**Detail:** Mengekspos path lengkap development environment di Windows. Tidak berisiko secara langsung, tapi mengekspos struktur sistem developer.

**Rekomendasi:** Hapus file scratch dari repository.

---

## NOT VERIFIED

---

### SEC-020 — Dependency Vulnerabilities

**Severity:** Varies  
**Confidence:** Low  
**Status:** Not Verified

**Detail:** Beberapa dependensi memiliki versi spesifik di `requirements.txt`. Perlu dijalankan `pip audit` atau `safety check` untuk memverifikasi apakah ada CVE yang diketahui.

**Langkah verifikasi:**
```bash
pip install pip-audit
pip-audit -r requirements.txt
```

---

## Ringkasan Rekomendasi Priority

| Priority | Finding ID | Tindakan |
|---|---|---|
| P0 (Segera) | SEC-001 | Tambahkan `@login_required` ke `asset_add` |
| P0 (Segera) | SEC-007 | Hapus file SQL dari repository |
| P1 | SEC-004 | Validasi upload di semua distribusi views |
| P1 | SEC-005 | Implementasikan rate limiting login |
| P1 | SEC-008 | Gunakan `~/.my.cnf` untuk mysqldump credentials |
| P2 | SEC-010 | Hilangkan fallback secret key |
| P2 | SEC-014 | Pindah password dari command line |
| P3 | SEC-020 | Audit dependency vulnerabilities |

---

## Pernyataan Pembatasan

> Audit ini bersifat analisis statis berdasarkan source code. Tidak ada eksploitasi aktif, penetration testing terhadap server, atau pengujian runtime yang dilakukan. Temuan yang diberi label "Suspected" atau "Not Verified" memerlukan verifikasi tambahan sebelum dikonfirmasi sebagai kerentanan.
