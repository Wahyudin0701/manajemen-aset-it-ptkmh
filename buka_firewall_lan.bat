@echo off
title Buka Port 8000 Windows Firewall - PT. KMH
cd /d "%~dp0"

echo ==============================================================================
echo   KONFIGURASI WINDOWS FIREWALL - AKSES JARINGAN LAN (PORT 8000)
echo   Sistem Manajemen Aset IT - PT. Kerinci Hydropower
echo ==============================================================================
echo.

:: Cek hak administrator
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [PERHATIAN] File ini membutuhkan izin Administrator.
    echo.
    echo Silakan TUTUP jendela ini, lalu:
    echo KLIK KANAN pada file 'buka_firewall_lan.bat' -^> Pilih 'Run as administrator'.
    echo.
    pause
    exit /b 1
)

echo [INFO] Mendaftarkan Inbound Rule TCP Port 8000 di Windows Firewall...
netsh advfirewall firewall add rule name="ITAM PT KMH (Port 8000)" dir=in action=allow protocol=TCP localport=8000 profile=any >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==============================================================================
    echo [SUKSES] Port 8000 berhasil dibuka pada Windows Firewall!
    echo.
    echo Komputer klien dalam satu jaringan LAN / Wi-Fi sekarang dapat mengakses aplikasi
    echo melalui browser menggunakan URL IP Server (contoh: http://162.198.2.212:8000).
    echo ==============================================================================
) else (
    echo.
    echo [GAGAL] Terjadi kesalahan saat mendaftarkan aturan firewall.
)

echo.
pause
exit /b 0
