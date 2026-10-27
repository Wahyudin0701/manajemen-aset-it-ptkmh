@echo off
title Push ke Server Gitea PT. KMH
cd /d "%~dp0"

echo ==============================================================================
echo   PUSH PROYEK SISTEM MANAJEMEN ASET IT - PT. KMH
echo   Target: http://162.198.2.212:3000/ryan/KMH_IT_Assets.git
echo   Branch: main
echo ==============================================================================
echo.
echo Mengirimkan commit ke repositori Gitea...
echo (Catatan: Jika jendela terminal meminta kredensial, masukkan Username dan Password Gitea Anda)
echo.

git push -u origin main

echo.
if %ERRORLEVEL% EQU 0 (
    echo ==============================================================================
    echo [SUKSES] Seluruh berkas dan commit berhasil di-push ke server Gitea!
    echo ==============================================================================
) else (
    echo ==============================================================================
    echo [CATATAN] Periksa pesan di atas. Jika gagal karena autentikasi, pastikan
    echo Username dan Password atau Personal Access Token akun Gitea sudah benar.
    echo ==============================================================================
)

echo.
pause
exit /b %ERRORLEVEL%
