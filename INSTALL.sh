#!/bin/bash
# Installer Mod Lokalisasi Bahasa Indonesia - Danganronpa: Trigger Happy Havoc
# Milky Brain - Divisi Game Modding & Lokalisasi

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GAME_DIR="${1:-$PWD}"

WAD_FILE="$GAME_DIR/dr1_data_us.wad"
BAK_FILE="$GAME_DIR/dr1_data_us.wad.orig.bak"

echo "======================================================================="
echo "  Danganronpa: Trigger Happy Havoc - Mod Bahasa Indonesia v1.0.0"
echo "  Milky Brain - Divisi Game Modding & Lokalisasi"
echo "======================================================================="
echo ""

if [ ! -f "$WAD_FILE" ]; then
    echo "[ERROR] File 'dr1_data_us.wad' tidak ditemukan di $GAME_DIR!"
    echo "Penggunaan: ./INSTALL.sh [path_folder_game]"
    echo "Atau letakkan skrip ini langsung di dalam folder game Danganronpa."
    echo ""
    exit 1
fi

if [ ! -f "$BAK_FILE" ]; then
    echo "[1/2] Membuat backup file asli ke 'dr1_data_us.wad.orig.bak'..."
    cp -a "$WAD_FILE" "$BAK_FILE"
    echo "      Backup berhasil dibuat."
else
    echo "[1/2] File backup 'dr1_data_us.wad.orig.bak' sudah ada. Melewati backup."
fi

echo ""
echo "[2/2] Menyuntikkan lokalisasi Bahasa Indonesia ke dr1_data_us.wad..."
python3 "$SCRIPT_DIR/wad_tool.py" "$BAK_FILE" "$SCRIPT_DIR/dr1_patch_workspace" "$WAD_FILE"

echo ""
echo "======================================================================="
echo "  SUKSES! Danganronpa: Trigger Happy Havoc kini sudah berbahasa Indonesia!"
echo "  Silakan jalankan game melalui Steam."
echo "======================================================================="
