# 15 — Glossary & Domain Terminology

**Tanggal Analisis:** 26 Oktober 2026  
**Status Verifikasi:** Istilah diekstraksi dari kode sumber, label template, dan model bisnis PT KMH.  

---

## 1. Terminologi Domain Bisnis & Pengelolaan Aset (ITAM)

| Istilah | Definisi Konseptual | Konteks Penerapan dalam Aplikasi | Status Verifikasi |
|---|---|---|---|
| **Aset (SKU Level)** | Definisi tipe atau model perangkat keras/lunak secara umum tanpa nomor identitas fisik unik. Contoh: "Monitor Dell 24 inch", "Wireless Access Point Ruijie". | Direpresentasikan oleh model `Asset` di `assets/models.py:18`. Berisi informasi kode kelompok (`asset_code`), merek, dan kategori. | Terverifikasi |
| **Unit Aset (Unit Fisik)** | Perangkat fisik individual nyata yang memiliki serial number, stiker inventaris, atau kode pelacak mandiri. Satu jenis aset dapat memiliki puluhan unit fisik. | Direpresentasikan oleh model `AssetUnit` di `assets/models.py:84`. Memiliki `unit_code` unik (misal: `NB-001`, `NB-002`) dan status operasional. | Terverifikasi |
| **Kode Aset (`asset_code`)** | Pengidentifikasi unik untuk tipe/model aset induk, biasanya ditulis dalam format huruf kapital singkat. | Kolom `Asset.asset_code` (unique constraint aktif). Jika kode ini diubah, sistem otomatis memperbarui awalan seluruh kode unit di bawahnya. | Terverifikasi |
| **Kode Unit (`unit_code`)** | Pengidentifikasi unik untuk setiap unit fisik barang, terbentuk dari kombinasi kode aset induk dan suffix nomor urut (contoh: `PC-OFFICE-015`). | Kolom `AssetUnit.unit_code` (unique constraint aktif). Digunakan pada pencetakan label stiker dan pencarian cepat. | Terverifikasi |
| **Distribusi Aset** | Seluruh proses sirkulasi pemindahan fisik dan tanggung jawab pemeliharaan aset dari gudang IT ke pengguna, antar-pengguna, atau kembali ke gudang. | Dikelola melalui model `AssetAssignment` dan antarmuka `/distribusi/`. | Terverifikasi |
| **Serah Terima (*Handover*)** | Transaksi penyerahan unit aset yang berstatus `"tersedia"` dari gudang IT kepada seorang karyawan untuk keperluan kedinasan. | `AssetAssignment.TYPE_CHOICES = 'handover'`. Mengubah status unit menjadi `"digunakan"` dan menetapkan kolom `assigned_to`. | Terverifikasi |
| **Mutasi (*Mutation*)** | Transaksi pemindahan tanggung jawab pemegang unit aset dari karyawan lama (`from_employee`) langsung ke karyawan baru (`employee`). | `AssetAssignment.TYPE_CHOICES = 'mutation'`. Mencatat 2 jejak log riwayat sekaligus (pengembalian pemegang lama & serah terima pemegang baru). | Terverifikasi |
| **Pengembalian (*Return*)** | Transaksi pengembalian unit aset dari karyawan pemegang ke gudang IT karena selesai masa tugas, mutasi keluar, atau kerusakan unit. | `AssetAssignment.TYPE_CHOICES = 'return'`. Mengubah status unit kembali menjadi `"tersedia"` dan mengosongkan `assigned_to`. | Terverifikasi |
| **BAST (Berita Acara Serah Terima)** | Dokumen legal fisik/surat tanda terima penyerahan inventaris perusahaan yang ditandatangani kedua belah pihak. | Kolom `AssetAssignment.document`, disimpan pada direktori server `media/bast_documents/`. | Terverifikasi |
| **PIC (*Person in Charge*) / Pemegang** | Karyawan aktif yang tercatat secara sah sebagai penanggung jawab unit aset saat ini. | Foreign Key `AssetUnit.assigned_to` yang terhubung ke model `Employee`. | Terverifikasi |
| **Area Pemasangan** | Lokasi zona geografis penempatan perangkat infrastruktur jaringan pada fasilitas PLTA Kerinci Hydropower. | Pilihan statis pada `AssetUnit.AREA_CHOICES` (seperti: RW, DAM, Adit 1/2/3, Power House, Vertical Shaft). | Terverifikasi |
| **Lokasi Spesifik** | Keterangan detail letak fisik perangkat di dalam area tertentu (contoh: "Ruang Server Lt. 2 Rack A", "Pos Satpam Pintu 3"). | Kolom teks bebas `AssetUnit.location`. | Terverifikasi |
| **Status Unit: Tersedia** | Unit berada di ruang penyimpanan/gudang IT, dalam kondisi prima, dan siap diserahterimakan. | Nilai database `'tersedia'`. | Terverifikasi |
| **Status Unit: Digunakan** | Unit sedang aktif dipakai oleh karyawan tertentu atau terpasang aktif di area jaringan. | Nilai database `'digunakan'`. | Terverifikasi |
| **Status Unit: Rusak / Maintenance** | Unit mengalami kendala teknis dan sedang berada di lab IT/vendor untuk perbaikan. | Nilai database `'rusak'`, dengan display label antarmuka `'Diperbaiki'`. | Terverifikasi |
| **Status Unit: Dipensiunkan** | Unit telah melewati masa manfaat ekonomis/teknis, rusak permanen, atau dihapuskan dari pembukuan perusahaan (*disposed*). | Nilai database `'pensiun'`. | Terverifikasi |
| **Unit Log / Timeline** | Catatan buku besar (*audit trail ledger*) yang merekam setiap peristiwa perubahan status, mutasi, atau perbaikan pada unit sejak pertama kali didaftarkan. | Model `UnitLog`. Bersifat append-only dan diurutkan dari peristiwa paling baru (`-timestamp`). | Terverifikasi |

---

## 2. Terminologi Teknis Arsitektur & Rekayasa Perangkat Lunak

| Istilah | Definisi & Peran dalam Sistem |
|---|---|
| **Django Monolith** | Pola arsitektur di mana logika bisnis, routing, model data, dan antarmuka HTML digabungkan dalam satu repositori terpusat. |
| **HTMX** | Library JavaScript deklaratif yang memungkinkan pembaruan bagian halaman HTML secara dinamis via AJAX tanpa menulis JavaScript manual. |
| **TailwindCSS** | Framework CSS utility-first yang digunakan untuk styling modern, responsif, dan konsisten di seluruh antarmuka web. |
| **WhiteNoise** | Middleware Django yang mengoptimalkan penyajian file statis (CSS/JS/Gambar) secara langsung dari server aplikasi Python tanpa memberatkan WSGI server. |
| **ReportLab** | Library Python untuk mengonversi data dinamis menjadi dokumen PDF berstandar cetak dengan tata letak koordinat presisi. |
| **openpyxl** | Library Python untuk membaca dan menulis file spreadsheet format Microsoft Excel (.xlsx) dengan styling border dan warna sel. |
| **PyMySQL** | Driver Python murni untuk menghubungkan aplikasi Django ke database MySQL / MariaDB tanpa kompilasi native C extension. |
| **UUID (Universally Unique Identifier)** | 128-bit identifier acak yang digunakan pada `AssetUnit.id_uuid` agar URL publik tidak dapat ditebak secara berurutan (*anti-enumeration attack*). |
| **Atomic Transaction** | Blok eksekusi database di mana serangkaian operasi query harus berhasil seluruhnya; jika satu query gagal, seluruh operasi dibatalkan (*rollback*). Digunakan pada `@transaction.atomic` di alur distribusi. |
| **God File** | Anti-pattern di mana sebuah file modul menampung terlalu banyak tanggung jawab dan baris kode (`assets/views.py` dengan 3.056 baris). |
| **Soft Delete** | Pola penghapusan data di mana baris database tidak benar-benar dihapus (DELETE), melainkan hanya ditandai nonaktif melalui kolom flag boolean atau timestamp. |
| **RBAC (Role-Based Access Control)** | Mekanisme kontrol akses yang membatasi wewenang tindakan pengguna berdasarkan peran atau grup yang diberikan kepadanya. |
