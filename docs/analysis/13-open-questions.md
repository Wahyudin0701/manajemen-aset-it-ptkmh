# 13 — Open Questions & Stakeholder Clarifications

**Tanggal Analisis:** 26 Oktober 2026  
**Status Verifikasi:** Pertanyaan teknis dan bisnis yang dirumuskan berdasarkan temuan kode tidak lengkap atau ambigu.  

---

## 1. Domain Bisnis & Alur Pengelolaan Aset

| No | Pertanyaan untuk Stakeholder / Business Owner | Alasan Mengapa Informasi Ini Dibutuhkan | Keputusan Teknis/Bisnis yang Bergantung |
|---|---|---|---|
| **Q-BUS-01** | Apakah unit aset yang berstatus `"rusak"` (Maintenance) boleh diserahterimakan ke karyawan lain atau wajib dikembalikan ke status `"tersedia"` terlebih dahulu? | Saat ini di view `unit_edit`, admin dapat secara manual mengubah status dari `"rusak"` langsung menjadi `"digunakan"` ke karyawan baru tanpa validasi alur. | Pembuatan *State Machine* / validasi transisi status unit aset yang kaku pada backend. |
| **Q-BUS-02** | Apakah penghapusan unit aset fisik (`AssetUnit`) memang diizinkan dalam kebijakan operasional perusahaan? | Terdapat fungsi `unit_delete` di `views.py` namun rutenya tidak terdaftar di `urls.py`. | Apakah tombol hapus unit perlu diaktifkan, atau digantikan dengan status `"pensiun"` / `"disposed"`. |
| **Q-BUS-03** | Apakah ada perbedaan alur penugasan antara "Aset Karyawan" (laptop, mouse, monitor) dengan "Aset Network" (CCTV, switch, access point)? | Pada kode saat ini, dropdown distribusi hanya memfilter aset karyawan (`distribusi_list.html`), sedangkan penempatan aset network diatur terpisah melalui form `unit_update_status` (area dan lokasi). | Penyatuan atau pemisahan permanen alur mutasi perangkat infrastruktur jaringan dari perangkat individu karyawan. |
| **Q-BUS-04** | Apa maksud dan kegunaan kolom `sum_qty`, `price`, dan `total_price` pada model `Asset`? | Kolom-kolom ini ada di database sejak migrasi awal, tetapi tidak pernah ditampilkan atau diinput dalam antarmuka web saat ini. | Apakah perlu dibangun modul *Asset Financial Tracking & Valuation* (pembukuan harga perolehan), atau field ini sebaiknya di-drop agar skema lebih ringkas. |
| **Q-BUS-05** | Bagaimana kebijakan terkait dokumen fisik BAST? Apakah wajib diunggah sebelum aset diserahkan, atau boleh menyusul? | Pada `distribusi_handover`, field dokumen bersifat opsional (`blank=True, null=True`), dan disediakan view terpisah `distribusi_upload_doc`. | Menentukan apakah validasi form harus mewajibkan attachment dokumen atau tetap opsional. |

---

## 2. Kebutuhan Autentikasi & Hak Akses (User Roles)

| No | Pertanyaan untuk Stakeholder / Business Owner | Alasan Mengapa Informasi Ini Dibutuhkan | Keputusan Teknis/Bisnis yang Bergantung |
|---|---|---|---|
| **Q-SEC-01** | Berapa banyak orang yang akan mengoperasikan aplikasi ini, dan apa saja peran kerja mereka? | Saat ini aplikasi hanya memiliki satu level otorisasi: siapapun yang login dianggap sebagai Administrator penuh. | Perancangan skema Role-Based Access Control (RBAC): pemisahan antara Admin IT, Staff Teknisi Lapangan, dan Pimpinan/Auditor (View-Only). |
| **Q-SEC-02** | Mengapa antarmuka bawaan Django Admin (`/admin/`) dinonaktifkan di `urls.py`? | Konfigurasi `admin.site.site_header` sangat rapi diatur di `urls.py:10-12`, tetapi baris `path('admin/', ...)` dikomentari. | Menentukan apakah Django Admin ingin diaktifkan kembali sebagai emergency portal bagi superuser, atau memang dibuang permanen. |
| **Q-SEC-03** | Apakah informasi pada halaman publik QR Code (`/public/unit/<uuid>/`) aman dibaca oleh siapa saja tanpa login? | Siapapun yang men-scan QR code unit fisik dapat membaca riwayat seluruh mutasi karyawan dan status unit secara detail. | Apakah halaman publik perlu disederhanakan hanya menampilkan status "Milik PT KMH - Unit Aktif" tanpa membocorkan nama karyawan dan catatan internal. |

---

## 3. Infrastruktur & Operasional Server

| No | Pertanyaan untuk Tim Infrastruktur / DevOps | Alasan Mengapa Informasi Ini Dibutuhkan | Keputusan Teknis/Bisnis yang Bergantung |
|---|---|---|---|
| **Q-OPS-01** | Di lingkungan server mana aplikasi saat ini berjalan (atau akan dideploy)? (Windows Server vs Linux Ubuntu/Debian) | Terdapat dependensi font `arial.ttf` pada pembuatan stiker QR code (`PIL.ImageFont`) dan pemanggilan binary `mysqldump` pada fitur backup. | Penyiapan dependensi sistem operasi (paket `ttf-mscorefonts-installer` di Linux) dan konfigurasi environment path. |
| **Q-OPS-02** | Apakah server database MySQL saat ini sudah memiliki mekanisme scheduled backup otomatis di luar web aplikasi? | Fitur `/backup/` mengeksekusi `mysqldump` langsung dari request web HTTP, yang rentan timeout jika data database membesar. | Menonaktifkan backup via web untuk diganti dengan cron job sistem level OS yang jauh lebih stabil dan aman. |
| **Q-OPS-03** | Apakah file `database_lokal.sql` dan `seed_karyawan.sql` yang ada di root direktori berisi data riil operasional karyawan PT KMH? | File ini ter-commit di repository dan berpotensi melanggar privasi data jika repository diakses pihak luar. | Prosedur pembersihan commit history git (`git filter-repo`) dan penegasan kebijakan perlindungan data pribadi (PDP). |
| **Q-OPS-04** | Berapa kuota penyimpanan disk yang dialokasikan untuk folder `media/bast_documents/`? | Pengguna dapat mengunggah berkas BAST hingga batas 5MB per transaksi tanpa batasan kuota total. | Kebutuhan integrasi object storage (misal: MinIO / S3) jika penyimpanan server on-premise terbatas. |
