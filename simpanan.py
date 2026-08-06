# -*- coding: utf-8 -*-
"""
Penyimpanan data CANTING — SQLite, satu buku per KODE USAHA.

MENGAPA ADA KODE USAHA
----------------------
Tanpa pembeda, semua orang yang membuka tautan yang sama akan berbagi satu
buku: pemilik A melihat penjualan pemilik B, dan siapa pun bisa menghapus
data siapa pun. Kode usaha memberi tiap UMKM ruangnya sendiri.

Ini BUKAN autentikasi. Kode ini pembeda, bukan kunci — siapa pun yang
mengetahui kodenya bisa membuka bukunya. Untuk prototipe lomba itu memadai;
untuk produksi tetap dibutuhkan login yang sebenarnya. Batas ini dinyatakan
terbuka di dalam aplikasi, bukan disembunyikan.

BATAS PENYIMPANAN YANG HARUS DIKETAHUI
--------------------------------------
Streamlit Community Cloud memakai penyimpanan SEMENTARA. Berkas basis data
bertahan selama peladen hidup — melewati penyegaran halaman, penutupan tab,
maupun pergantian peramban — tetapi TERHAPUS ketika aplikasi disebarkan ulang
atau peladennya didaur. Karena itu tombol unduh cadangan tetap disediakan,
dan pemakainya diberi tahu apa adanya.
"""
from __future__ import annotations

import json
import random
import sqlite3
import string
from pathlib import Path

BERKAS = Path(__file__).parent / "canting.db"

# Huruf yang mudah membingungkan sengaja dibuang: O/0, I/1, L.
# Kode ini akan dibacakan lewat telepon dan disalin dengan tangan.
ABJAD = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def _sambung() -> sqlite3.Connection:
    sam = sqlite3.connect(BERKAS, check_same_thread=False)
    sam.execute("""
        CREATE TABLE IF NOT EXISTS buku (
            kode      TEXT PRIMARY KEY,
            data      TEXT NOT NULL,
            diperbarui TEXT NOT NULL
        )
    """)
    return sam


def kode_baru() -> str:
    """Kode 6 huruf yang belum terpakai, mis. 'K7PMQ3'."""
    with _sambung() as sam:
        for _ in range(50):
            kode = "".join(random.choices(ABJAD, k=6))
            ada = sam.execute("SELECT 1 FROM buku WHERE kode = ?", (kode,)).fetchone()
            if not ada:
                return kode
    return "".join(random.choices(ABJAD, k=8))       # kemungkinan sangat kecil


def simpan(kode: str, data: dict) -> None:
    from datetime import datetime
    with _sambung() as sam:
        sam.execute(
            "INSERT INTO buku (kode, data, diperbarui) VALUES (?, ?, ?) "
            "ON CONFLICT(kode) DO UPDATE SET data = excluded.data, "
            "diperbarui = excluded.diperbarui",
            (kode, json.dumps(data, ensure_ascii=False), datetime.now().isoformat()))


def muat(kode: str) -> dict | None:
    with _sambung() as sam:
        baris = sam.execute("SELECT data FROM buku WHERE kode = ?", (kode,)).fetchone()
    return json.loads(baris[0]) if baris else None


def ada(kode: str) -> bool:
    return muat(kode) is not None


def hapus(kode: str) -> None:
    with _sambung() as sam:
        sam.execute("DELETE FROM buku WHERE kode = ?", (kode,))


def jumlah_buku() -> int:
    with _sambung() as sam:
        return sam.execute("SELECT COUNT(*) FROM buku").fetchone()[0]


if __name__ == "__main__":
    k = kode_baru()
    print("kode baru        :", k)
    simpan(k, {"uji": True, "kain": [1, 2, 3]})
    print("dimuat kembali   :", muat(k))
    print("jumlah buku      :", jumlah_buku())
    hapus(k)
    print("setelah dihapus  :", muat(k))
