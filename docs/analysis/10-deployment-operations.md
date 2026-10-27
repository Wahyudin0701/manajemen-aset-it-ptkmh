# 10 — Deployment & Operational Runbook

**Tanggal Analisis:** 26 Oktober 2026  
**Status Verifikasi:** Disusun berdasarkan bukti repository (`settings.py`, `package.json`, `manage.py`, `.env.example`, `scratch_urls_all.py`)  
**Lingkungan Target Terdeteksi:** Windows Server / Linux Server, Laragon / Apache / Nginx, MySQL / MariaDB  

---

## 1. Analisis Arsitektur Deployment Eksisting

Berdasarkan bukti di file repository:
1. **WSGI & ASGI Entry Point:**
   - `itam_core/wsgi.py` (tersedia untuk WSGI Server seperti Gunicorn/uWSGI/mod_wsgi).
   - `itam_core/asgi.py` (tersedia, namun saat ini tidak ada fitur asynchronous/websocket).
2. **Environment Path Clues:**
   - File `scratch_urls_all.py` baris 3 menunjukkan path development awal: `c:/laragon/www/Manajemen-Aset-IT/...` (Environment Laragon berbasis Windows).
3. **Frontend Build Pipeline:**
   - Proyek menggunakan Vite + TailwindCSS + PostCSS (`package.json`).
   - File output CSS final dikompilasi ke `static/dist/style.css` (sudah di-commit di git).
   - `django-vite` dan `WhiteNoise` dikonfigurasi di `settings.py` untuk menyajikan static files di mode production.
4. **Media Storage:**
   - Direktori `media/bast_documents/` digunakan untuk menyimpan file BAST yang diunggah pengguna.

---

## 2. Kebutuhan Lingkungan & Dependensi Sistem (Prerequisites)

| Komponen | Spesifikasi Rekomendasi | Keterangan |
|---|---|---|
| **OS** | Linux (Ubuntu 22.04 LTS / Debian 12) atau Windows Server | Linux sangat direkomendasikan untuk stabilitas produksi |
| **Python** | Python 3.10 atau 3.11 | Wajib untuk kompatibilitas Django 5.2 |
| **Node.js** | Node.js v18.x atau v20.x + npm | Hanya diperlukan saat build aset CSS/JS |
| **Database** | MySQL 8.0+ atau MariaDB 10.6+ | Karakter set `utf8mb4` wajib aktif |
| **Utilitas Sistem** | `mysqldump` | Wajib ada di PATH sistem agar fitur backup SQL berjalan |
| **Web Server** | Nginx (Reverse Proxy) + Gunicorn | Menangani HTTPS termination & media serving |

---

## 3. Variabel Lingkungan (Environment Variables)

File `.env` wajib dibuat di root direktori dengan parameter berikut:

```ini
# ==========================================
# KONFIGURASI INTI DJANGO
# ==========================================
DJANGO_SECRET_KEY=isi-dengan-string-acak-panjang-dan-unik-50-karakter
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=aset.ptkmh.co.id,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://aset.ptkmh.co.id

# ==========================================
# KONFIGURASI DATABASE MYSQL
# ==========================================
DB_NAME=manajemen_aset_it
DB_USER=db_user_it
DB_PASSWORD=password_database_kuat
DB_HOST=127.0.0.1
DB_PORT=3306

# ==========================================
# KEAMANAN HTTPS (PRODUCTION)
# ==========================================
SECURE_SSL_REDIRECT=True

# ==========================================
# INISIALISASI SUPERUSER (Opsional, untuk setup awal)
# ==========================================
SUPERUSER_USERNAME=admin
SUPERUSER_EMAIL=it.admin@ptkmh.co.id
SUPERUSER_PASSWORD=password_admin_sangat_rahasia
```

---

## 4. Prosedur Instalasi & Deployment Langkah-demi-Langkah

### Tahap 1: Persiapan Repository & Virtual Environment
```bash
# Masuk ke direktori aplikasi
cd /var/www/manajemen-aset-it

# Buat virtual environment Python
python3 -m venv venv
source venv/bin/activate

# Upgrade pip & install dependensi
pip install --upgrade pip
pip install -r requirements.txt
```

### Tahap 2: Build Frontend Assets (TailwindCSS)
```bash
# Instal node modules & build aset produksi
npm ci
npm run build
```

### Tahap 3: Konfigurasi Database & Migrasi
```bash
# Pastikan database telah dibuat di MySQL:
# CREATE DATABASE manajemen_aset_it CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Jalankan migrasi skema
python manage.py migrate

# Jalankan seeding kategori awal
python manage.py seed_initial_data

# Buat akun administrator (jika belum ada)
python manage.py setup_superuser
```

### Tahap 4: Pengumpulan Static Files
```bash
python manage.py collectstatic --noinput
```

---

## 5. Konfigurasi Layanan Produksi (Gunicorn + Nginx + Systemd)

### 5.1 Service Systemd Gunicorn (`/etc/systemd/system/itam.service`)
```ini
[Unit]
Description=Gunicorn daemon for IT Asset Management PT KMH
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/manajemen-aset-it
ExecStart=/var/www/manajemen-aset-it/venv/bin/gunicorn \
          --access-logfile /var/log/gunicorn/itam_access.log \
          --error-logfile /var/log/gunicorn/itam_error.log \
          --workers 3 \
          --bind unix:/run/itam.sock \
          itam_core.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 5.2 Konfigurasi Nginx Virtual Host (`/etc/nginx/sites-available/itam`)
```nginx
server {
    listen 80;
    server_name aset.ptkmh.co.id;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name aset.ptkmh.co.id;

    ssl_certificate /etc/ssl/certs/ptkmh_ssl.crt;
    ssl_certificate_key /etc/ssl/private/ptkmh_ssl.key;

    client_max_body_size 10M;

    # Static files dilayani langsung oleh Nginx (Cache efisien)
    location /static/ {
        alias /var/www/manajemen-aset-it/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # Media files (Dokumen BAST fisik & QR Code)
    location /media/ {
        alias /var/www/manajemen-aset-it/media/;
        expires 7d;
        add_header Cache-Control "private";
    }

    # Reverse proxy ke Gunicorn socket
    location / {
        include proxy_params;
        proxy_pass http://unix:/run/itam.sock;
    }
}
```

---

## 6. Prosedur Backup & Disaster Recovery

### 6.1 Prosedur Backup Otomatis Terjadwal (Cron Job)
Aplikasi memiliki fitur backup web di `/backup/`, namun untuk keandalan infrastruktur wajib disiapkan backup level sistem menggunakan cron job:

```bash
# Tambahkan ke crontab (setiap hari pukul 02:00 dini hari)
0 2 * * * /usr/bin/mysqldump -u db_user_it -p'password' manajemen_aset_it | gzip > /backup/db/itam_db_$(date +\%Y\%m\%d).sql.gz

# Backup folder media upload setiap minggu
0 3 * * 0 tar -czf /backup/media/itam_media_$(date +\%Y\%m\%d).tar.gz /var/www/manajemen-aset-it/media/
```

### 6.2 Prosedur Pemulihan (Restoration Runbook)
1. **Restore dari File SQL:**
   ```bash
   gunzip < /backup/db/itam_db_20261026.sql.gz | mysql -u db_user_it -p manajemen_aset_it
   ```
2. **Restore dari File JSON Django (Fitur Bawaan Aplikasi):**
   ```bash
   python manage.py loaddata backup_manajemen_aset_2026-10-26.json
   ```

---

## 7. Pemantauan & Logging Operasional

- **Application Error Log:** `error.log` di root direktori aplikasi (dikonfigurasi pada `settings.py` L165-190).
- **Web Server Logs:** `/var/log/nginx/access.log` dan `/var/log/nginx/error.log`.
- **Gunicorn Logs:** `/var/log/gunicorn/itam_error.log`.

> [!WARNING]
> File `error.log` di root folder aplikasi belum memiliki sistem *log rotation*. Pastikan dikonfigurasikan `logrotate` pada OS server agar ukuran log tidak memenuhi ruang disk.
