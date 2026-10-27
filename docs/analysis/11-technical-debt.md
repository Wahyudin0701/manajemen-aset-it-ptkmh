# 11 — Technical Debt Register

**Tanggal Analisis:** 26 Oktober 2026  
**Status Verifikasi:** Terverifikasi via code inspection komprehensif  

---

## 1. Skala Penilaian

- **Prioritas:**
  - **P0:** Kerusakan integritas data atau risiko keamanan mendesak.
  - **P1:** Penghambat langsung terhadap pengembangan fitur baru dan reliabilitas.
  - **P2:** Penurunan kualitas kode, pemeliharaan (*maintainability*), dan performa.
  - **P3:** Refactoring estetika, optimasi jangka panjang.
- **Estimasi Effort:**
  - **S (Small):** < 4 jam kerja.
  - **M (Medium):** 1 – 3 hari kerja.
  - **L (Large):** 1 – 2 minggu kerja.
  - **XL (Extra Large):** > 2 minggu kerja (perlu perombakan arsitektural).

---

## 2. Register Technical Debt Terperinci

| Debt ID | Deskripsi Masalah | Bukti Lokasi di Repo | Dampak Teknis | Prioritas | Effort | Ketergantungan (Dependencies) | Rekomendasi Solusi | Risiko Jika Ditunda |
|---|---|---|---|---|---|---|---|---|
| **TD-001** | `asset_add` tidak dilindungi autentikasi | `assets/views.py:192` | Pengguna anonim dapat memasukkan data aset ilegal via POST | **P0** | S | Tidak ada | Tambahkan dekorator `@login_required` di atas `asset_add` | Serangan data injection / spamming master aset |
| **TD-002** | View `unit_delete` tidak didaftarkan pada URL router | `assets/views.py:410` vs `itam_core/urls.py` | Fitur penghapusan unit aset fisik tidak bisa diakses sama sekali (broken/dead code) | **P0** | S | Konfirmasi bisnis flow penghapusan unit | Daftarkan rute `path('unit/<int:unit_id>/delete/', unit_delete, name='unit_delete')` atau hapus fungsinya jika unit tidak boleh dihapus | Admin tidak dapat membersihkan data unit yang salah input |
| **TD-003** | File dump database SQL development tersimpan di repository git | `database_lokal.sql`, `seed_karyawan.sql` | Potensi bocornya data identitas karyawan (NIK & Nama) jika repo dibagikan | **P0** | S | Tidak ada | Hapus kedua file dari git tracking dan daftarkan ekstensi `*.sql` ke `.gitignore` | Pelanggaran privasi data dan kebocoran struktur data internal |
| **TD-004** | Ketiadaan automated test suite (0% Coverage) | `assets/tests.py` | Tidak ada safety net saat melakukan upgrade dependensi atau refactor | **P1** | L | TD-005 (pemecahan views mempermudah testing) | Tulis unit test model, form, dan view menggunakan pytest-django | Risiko regresi sangat tinggi setiap kali ada kode yang disentuh |
| **TD-005** | God file pada `assets/views.py` (3.056 baris) | `assets/views.py` | Sulit dipelihara, conflict-prone, mencampuradukkan controller, reporting, dan logic | **P1** | L | TD-004 (buat baseline test sebelum split) | Pecah file menjadi package modul `views/` per domain | Melambatnya kecepatan development dan tingginya potensi conflict |
| **TD-006** | File upload BAST pada serah terima awal tidak divalidasi | `assets/views.py:584, 619, 659` | Pengguna dapat mengunggah file berbahaya (skrip/executable) atau file raksasa | **P1** | S | Tidak ada | Samakan validasi ekstensi (`.pdf, .doc, .jpg`) dan batas 5MB seperti di `distribusi_upload_doc` | Server kehabisan storage atau tersimpan file berbahaya |
| **TD-007** | Encoding anomali pada `requirements.txt` baris 15 | `requirements.txt:15` | Teks `o p e n p y x l = = 3 . 1 . 2` mengandung spasi/null byte UTF-16 | **P1** | S | Tidak ada | Format ulang baris menjadi `openpyxl==3.1.2` standar UTF-8 | `pip install -r requirements.txt` bisa gagal di environment build CI Linux |
| **TD-008** | Inkonsistensi update kolom `returned_date` dan `status` pada `AssetAssignment` | `assets/views.py:654-686` | Record transaksi distribusi tidak menandai bahwa masa pinjam telah berakhir | **P1** | S | Tidak ada | Update `assignment.returned_date = assigned_date` dan `assignment.status = 'dikembalikan'` pada transaksi return | Data riwayat distribusi tidak akurat dalam laporan audit penugasan |
| **TD-009** | Ketiadaan pagination di seluruh halaman tabel utama | `assets/views.py` (semua fungsi `*_list`) | Query memuat seluruh baris database ke memori sekaligus | **P2** | M | Modifikasi template HTML untuk kontrol pagination | Terapkan `django.core.paginator.Paginator` per 25-50 baris data | Server mengalami memory spike dan browser lambat saat data mencapai ribuan unit |
| **TD-010** | Duplikasi layouting PDF ReportLab secara repetitif | `assets/views.py:857-2440` (~1.500 baris duplikasi) | Setiap perubahan header/logo harus diedit manual pada 7 fungsi terpisah | **P2** | M | TD-005 | Buat utility builder class PDF Report terpusat | Inkonsistensi format laporan antar modul jika ada update |
| **TD-011** | Mekanisme parsing nama karyawan yang dihapus menggunakan Regex | `assets/views.py:428-438, 792-796` | Fragile: nama dengan karakter tanda kurung dapat merusak parsing riwayat log | **P2** | M | Skema migrasi model Employee | Terapkan soft delete (`is_active=False`) pada tabel `Employee` daripada hard delete | Catatan riwayat mutasi aset menjadi korup atau hilang keterhubungannya |
| **TD-012** | Inkonsistensi nilai status `'rusak'` dengan display label `'Diperbaiki'` | `assets/models.py:89` | Membingungkan pengguna: apakah unit sedang rusak, atau sudah selesai diperbaiki? | **P2** | S | Migrasi data nilai status | Ubah value choice menjadi `'maintenance'` dengan label `'Dalam Pemeliharaan'` | Kesalahpahaman operasional teknisi lapangan |
| **TD-013** | Field mati/legacy pada model `Asset` (`sum_qty`, `price`, `total_price`) | `assets/models.py:27-31` | Kolom ada di tabel namun tidak pernah dihitung, diinput, ataupun divalidasi | **P2** | M | Analisis kebutuhan financial tracking | Putuskan apakah akan diaktifkan fitur valuasi aset finansial atau dibersihkan via migrasi | Kebingungan arsitektur data bagi developer penerus |
| **TD-014** | Filtering kategori berbasis string `icontains='Network'` | `assets/views.py` (berbagai baris) | Sangat rentan error jika nama kategori diubah di database | **P2** | S | Skema Category model | Tambahkan kolom `Category.code` atau `Category.category_type` (Enum) | Fitur filter kategori rusak jika nama kategori diedit user |
| **TD-015** | Password database terekspos di argumen proses `mysqldump` | `assets/views.py:2566` | Password database dapat dibaca via `ps aux` pada server Linux | **P2** | S | Tidak ada | Gunakan opsi environment `MYSQL_PWD` atau file konfigurasi `--defaults-extra-file` | Kredensial database bocor ke pengguna non-root lokal |
| **TD-016** | Ketiadaan mekanisme Role-Based Access Control (RBAC) | `assets/views.py` | Setiap user yang login memiliki otoritas yang sama persis (Full Admin) | **P3** | L | Kebutuhan bisnis aktor | Implementasikan Django Groups & Permissions (misal: Admin IT, Staff Teknisi, Auditor Read-Only) | Penyalahgunaan wewenang atau ketidaksengajaan edit/hapus data oleh staff biasa |
| **TD-017** | Tidak adanya Containerization (Docker) dan CI/CD | Root repository | Setup environment baru bergantung pada panduan manual dan rentan perbedaan OS | **P3** | M | TD-007, TD-010 | Buat `Dockerfile`, `docker-compose.yml`, dan pipeline GitHub Actions | Waktu onboarding lambat dan potensi masalah "it works on my machine" |

---

## 3. Matriks Kuadran Dampak vs Effort

```
   TINGGI ▲ 
          │  [TD-001] Fix asset_add Auth      [TD-005] Split God File views.py
   D      │  [TD-002] Fix unit_delete Router   [TD-004] Tulis Unit Test Suite
   A      │  [TD-003] Bersihkan SQL Repo      [TD-009] Pagination Implementation
   M      │  [TD-006] Validasi File Upload    [TD-010] PDF Builder Refactor
   P      │  [TD-008] Fix Return Status
   A      │-----------------------------------------------------------------
   K      │  [TD-007] Fix requirements.txt    [TD-011] Soft Delete Employee
          │  [TD-012] Fix Status Label        [TD-013] Bersihkan Field Legacy
   RENDAH │  [TD-014] Category Code Enum      [TD-016] RBAC Implementation
          │  [TD-015] Hardening mysqldump     [TD-017] Docker & CI/CD Pipeline
          └─────────────────────────────────────────────────────────────────►
                     RENDAH (S)                         TINGGI (M - XL)
                                   E F F O R T
```
