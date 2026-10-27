@echo off
setlocal enabledelayedexpansion
title Sistem Manajemen Aset IT - PT. KMH

:: Pindah ke direktori tempat file batch ini berada
cd /d "%~dp0"

:: -----------------------------------------------------------------
:: 1. Deteksi dan Aktivasi Virtual Environment
:: -----------------------------------------------------------------
set "VENV_ACTIVATED=0"
if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
    set "VENV_ACTIVATED=1"
) else if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
    set "VENV_ACTIVATED=1"
) else if exist "env\Scripts\activate.bat" (
    call "env\Scripts\activate.bat"
    set "VENV_ACTIVATED=1"
)

:: -----------------------------------------------------------------
:: 2. Cek Keberadaan File .env
:: -----------------------------------------------------------------
if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] File .env tidak ditemukan. Membuat .env otomatis dari .env.example...
        copy ".env.example" ".env" >nul
        echo [OK] File .env berhasil dibuat. Silakan sesuaikan konfigurasi database jika diperlukan.
        echo.
    )
)

:: -----------------------------------------------------------------
:: 3. Dukungan Parameter Command-Line Langsung (Quick CLI Args)
:: -----------------------------------------------------------------
if /i "%~1"=="server" goto cmd_server
if /i "%~1"=="test" goto cmd_test
if /i "%~1"=="migrate" goto cmd_migrate
if /i "%~1"=="makemigrations" goto cmd_makemigrations
if /i "%~1"=="seed" goto cmd_seed
if /i "%~1"=="superuser" goto cmd_superuser
if /i "%~1"=="build" goto cmd_build
if /i "%~1"=="shell" goto cmd_shell
if /i "%~1"=="check" goto cmd_check_syntax

:: -----------------------------------------------------------------
:: 4. Menu Utama Interaktif
:: -----------------------------------------------------------------
:main_menu
cls
echo ==============================================================================
echo       SISTEM MANAJEMEN ASET IT - PT. KMH (Kerinci Hydropower)
echo ==============================================================================
if "!VENV_ACTIVATED!"=="1" (
    echo  [STATUS] Virtual Environment : AKTIF
) else (
    echo  [STATUS] Virtual Environment : TIDAK AKTIF (Menggunakan Python Global)
)
echo ==============================================================================
echo.
echo   [1] Jalankan Server Web LAN/Lokal (runserver 0.0.0.0:8000)
echo   [2] Jalankan Automated Test Suite (python manage.py test assets)
echo   [3] Jalankan Test dengan Output Terperinci (Verbose -v 2)
echo   [4] Jalankan Migrasi Database (python manage.py migrate)
echo   [5] Buat Migrasi Baru (python manage.py makemigrations)
echo   [6] Seed Data Awal ('Aset Karyawan', 'Aset Network', & Consumables)
echo   [7] Setup Akun Superuser Administrator (setup_superuser)
echo   [8] Build Aset Frontend / TailwindCSS (npm run build)
echo   [9] Install / Update Dependensi Python (pip install -r requirements.txt)
echo   [10] Buat Virtual Environment Baru dan Install Dependensi Otomatis
echo   [11] Buka Django Shell Interaktif
echo   [12] Cek Kesehatan Sintaks Kode (py_compile check)
echo   [13] Buka Port 8000 di Windows Firewall (Akses Jaringan LAN)
echo.
echo   [0] Keluar
echo.
echo ==============================================================================
set /p choice="Pilih menu [0-13]: "

if "%choice%"=="1" goto cmd_server
if "%choice%"=="2" goto cmd_test
if "%choice%"=="3" goto cmd_test_verbose
if "%choice%"=="4" goto cmd_migrate
if "%choice%"=="5" goto cmd_makemigrations
if "%choice%"=="6" goto cmd_seed
if "%choice%"=="7" goto cmd_superuser
if "%choice%"=="8" goto cmd_build
if "%choice%"=="9" goto cmd_install
if "%choice%"=="10" goto cmd_setup_venv
if "%choice%"=="11" goto cmd_shell
if "%choice%"=="12" goto cmd_check_syntax
if "%choice%"=="13" goto cmd_firewall
if "%choice%"=="0" goto cmd_exit

echo.
echo [ERROR] Pilihan tidak valid. Silakan coba lagi.
timeout /t 2 >nul
goto main_menu

:: -----------------------------------------------------------------
:: Subroutine Eksekusi Perintah
:: -----------------------------------------------------------------

:cmd_server
cls
set "SERVER_IP=127.0.0.1"
for /f "delims=" %%a in ('python -c "import socket; ips=socket.gethostbyname_ex(socket.gethostname())[2]; print(ips[0] if ips else '127.0.0.1')" 2^>nul') do set "SERVER_IP=%%a"
echo ==============================================================================
echo Menjalankan Server Web Django untuk Jaringan Lokal (LAN)...
echo ==============================================================================
echo.
echo   [KOMPUTER SERVER INI] Buka di browser : http://127.0.0.1:8000
echo   [KOMPUTER KLIEN / LAN] Buka di browser: http://!SERVER_IP!:8000
echo.
echo   *Catatan: Pastikan komputer klien terhubung di jaringan Wi-Fi/LAN yang sama.
echo   *Jika klien tidak dapat mengakses, gunakan menu [13] untuk membuka Firewall.
echo.
echo Tekan CTRL+C untuk menghentikan server.
echo ==============================================================================
echo.
python manage.py runserver 0.0.0.0:8000
echo.
pause
goto main_menu

:cmd_firewall
cls
echo ==============================================================================
echo Membuka Port 8000 di Windows Firewall (Inbound Rule)...
echo ==============================================================================
echo.
netsh advfirewall firewall add rule name="ITAM PT KMH (Port 8000)" dir=in action=allow protocol=TCP localport=8000
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUKSES] Port 8000 berhasil dibuka! Komputer klien sekarang bisa mengakses.
) else (
    echo.
    echo [PERINGATAN] Akses ditolak. Untuk membuka firewall secara otomatis,
    echo silakan jalankan file 'buka_firewall_lan.bat' dengan Klik Kanan -^> 'Run as administrator'.
)
echo.
pause
goto main_menu


:cmd_test
cls
echo ==============================================================================
echo Menjalankan Test Suite Otomatis (assets/tests.py)...
echo ==============================================================================
echo.
python manage.py test assets
echo.
echo ==============================================================================
pause
goto main_menu

:cmd_test_verbose
cls
echo ==============================================================================
echo Menjalankan Test Suite Otomatis (Verbose Mode -v 2)...
echo ==============================================================================
echo.
python manage.py test assets -v 2
echo.
echo ==============================================================================
pause
goto main_menu

:cmd_migrate
cls
echo ==============================================================================
echo Menerapkan Migrasi Database...
echo ==============================================================================
echo.
python manage.py migrate
echo.
pause
goto main_menu

:cmd_makemigrations
cls
echo ==============================================================================
echo Memeriksa dan Membuat Migrasi Skema Baru...
echo ==============================================================================
echo.
python manage.py makemigrations assets
echo.
pause
goto main_menu

:cmd_seed
cls
echo ==============================================================================
echo Mengisi Data Awal ('Aset Karyawan', 'Aset Network', & Consumable Items)...
echo ==============================================================================
echo.
python manage.py seed_initial_data
python manage.py seed_consumables
echo.
pause
goto main_menu

:cmd_superuser
cls
echo ==============================================================================
echo Menjalankan Setup Superuser Administrator...
echo (Pastikan SUPERUSER_USERNAME dan SUPERUSER_PASSWORD terisi di .env)
echo ==============================================================================
echo.
python manage.py setup_superuser
echo.
pause
goto main_menu

:cmd_build
cls
echo ==============================================================================
echo Mengompilasi Aset Frontend TailwindCSS & Vite...
echo ==============================================================================
echo.
call npm run build
echo.
pause
goto main_menu

:cmd_install
cls
echo ==============================================================================
echo Menginstall dependensi dari requirements.txt...
echo ==============================================================================
echo.
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
pause
goto main_menu

:cmd_setup_venv
cls
echo ==============================================================================
echo Menyiapkan Virtual Environment Baru (venv)...
echo ==============================================================================
echo.
if exist "venv" (
    echo [INFO] Folder venv sudah ada. Mengaktifkan...
) else (
    echo Membuat virtual environment di folder 'venv'...
    python -m venv venv
)
call "venv\Scripts\activate.bat"
set "VENV_ACTIVATED=1"
echo.
echo Menginstall dependensi Python...
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo [SUKSES] Virtual Environment telah aktif dan dependensi terpasang!
echo.
pause
goto main_menu

:cmd_shell
cls
echo ==============================================================================
echo Membuka Django Interactive Shell...
echo Ketik exit() untuk kembali ke menu.
echo ==============================================================================
echo.
python manage.py shell
echo.
goto main_menu

:cmd_check_syntax
cls
echo ==============================================================================
echo Memeriksa Kesehatan Sintaks Kode Sumber Python...
echo ==============================================================================
echo.
python -m py_compile assets/views.py itam_core/urls.py itam_core/settings.py assets/tests.py assets/models.py
if %ERRORLEVEL% EQU 0 (
    echo [OK] Seluruh file inti bebas dari kesalahan sintaks!
) else (
    echo [ERROR] Ditemukan kesalahan sintaks pada salah satu file.
)
echo.
pause
goto main_menu

:cmd_exit
echo.
echo Terima kasih! Keluar dari program.
endlocal
exit /b 0
