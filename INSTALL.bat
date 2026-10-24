@echo off
title Danganronpa: Trigger Happy Havoc - Indonesian Localization Installer
color 0A

echo =======================================================================
echo   Danganronpa: Trigger Happy Havoc - Mod Bahasa Indonesia v1.0.0
echo   Milky Brain - Divisi Game Modding ^& Lokalisasi
echo =======================================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "GAME_DIR=%CD%"

if not exist "%GAME_DIR%\dr1_data_us.wad" (
    echo [ERROR] File 'dr1_data_us.wad' tidak ditemukan di folder ini!
    echo Harap letakkan folder mod ini langsung di dalam folder game Danganronpa:
    echo Contoh: C:\Program Files (x86)\Steam\steamapps\common\Danganronpa Trigger Happy Havoc\
    echo.
    pause
    exit /b 1
)

if not exist "%GAME_DIR%\dr1_data_us.wad.orig.bak" (
    echo [1/3] Membuat backup file asli ke 'dr1_data_us.wad.orig.bak'...
    copy /y "%GAME_DIR%\dr1_data_us.wad" "%GAME_DIR%\dr1_data_us.wad.orig.bak" >nul
    echo       Backup berhasil dibuat.
) else (
    echo [1/3] File backup 'dr1_data_us.wad.orig.bak' sudah ada. Melewati backup.
)

echo.
echo [2/3] Memeriksa Python di komputer Anda...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    py --version >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo.
        echo [PERINGATAN] Python belum terdeteksi di Windows Anda.
        echo Opsi Solusi:
        echo 1. Instal Python (centang 'Add Python to PATH'): https://www.python.org/downloads/
        echo 2. ATAU gunakan paket 'Drop-In Edition' (tinggal timpa file dr1_data_us.wad tanpa butuh Python).
        echo.
        pause
        exit /b 1
    ) else (
        set "PY_CMD=py"
    )
) else (
    set "PY_CMD=python"
)

echo [3/3] Menyuntikkan lokalisasi Bahasa Indonesia ke dr1_data_us.wad...
%PY_CMD% "%SCRIPT_DIR%wad_tool.py" "%GAME_DIR%\dr1_data_us.wad.orig.bak" "%SCRIPT_DIR%dr1_patch_workspace" "%GAME_DIR%\dr1_data_us.wad"

if %ERRORLEVEL% equ 0 (
    echo.
    echo =======================================================================
    echo   SUKSES! Danganronpa: Trigger Happy Havoc kini sudah berbahasa Indonesia!
    echo   Silakan jalankan game melalui Steam.
    echo =======================================================================
) else (
    echo.
    echo [ERROR] Terjadi kesalahan saat proses patching.
)

echo.
pause
