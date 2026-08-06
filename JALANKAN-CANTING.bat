@echo off
REM ============================================================
REM  CANTING AI - pintasan menjalankan prototipe
REM  Klik dua kali berkas ini, lalu tunggu peramban terbuka.
REM  Selama jendela hitam ini terbuka, aplikasinya hidup.
REM  Menutup jendela ini = mematikan aplikasinya.
REM ============================================================
title CANTING AI - jangan tutup jendela ini
cd /d "%~dp0"

echo.
echo   Menyalakan CANTING AI...
echo   Peramban akan terbuka sendiri di http://localhost:8501
echo.
echo   JANGAN TUTUP jendela ini selama memakai aplikasi.
echo.

python -m streamlit run app.py --server.port 8501

REM kalau gagal, jendela tetap terbuka supaya pesan galatnya terbaca
echo.
echo   Aplikasi berhenti. Tekan tombol apa saja untuk menutup.
pause >nul
