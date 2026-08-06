# -*- coding: utf-8 -*-
"""
Uji regresi CANTING AI — jalankan SEBELUM setiap push.

    python cek.py

MENGAPA BERKAS INI ADA
----------------------
Selama pengembangan, hampir setiap perbaikan memunculkan kerusakan baru di
tempat lain: memperbaiki motif merusak tinggi kartu, menyembunyikan toolbar
mengunci sidebar, mengunci sidebar merusak tampilan ponsel. Polanya sama —
perubahan kecil di satu tempat menjatuhkan sesuatu yang jauh dan tak terpikir.

Setiap pemeriksaan di bawah MENGUNCI SATU KERUSAKAN YANG BENAR-BENAR PERNAH
TERJADI. Bukan uji karangan: tiap barisnya punya riwayat. Kalau ada yang
gagal, artinya kerusakan lama kembali.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

FOLDER = Path(__file__).parent

# Konsol Windows baku memakai cp1252 dan tersedak tanda centang. Berkas ini
# dijalankan oleh git hook, tempat keluarannya tidak dapat diatur dari luar —
# jadi pengaturannya dilakukan di sini, bukan diserahkan ke lingkungan.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
BERKAS_PY = ["app.py", "bahasa.py", "biaya.py", "buku.py",
             "ekstraksi.py", "simpanan.py", "solver.py", "tampilan.py"]

lulus, gagal = [], []


def periksa(nama: str, syarat: bool, riwayat: str, rincian: str = ""):
    (lulus if syarat else gagal).append((nama, riwayat, rincian))


# ============================================================ 1. SINTAKS
for f in BERKAS_PY:
    try:
        ast.parse((FOLDER / f).read_text(encoding="utf-8"))
        periksa(f"sintaks {f}", True, "")
    except SyntaxError as e:
        periksa(f"sintaks {f}", False, "", f"baris {e.lineno}: {e.msg}")


# =================================== 2. BACKSLASH DI EKSPRESI F-STRING
# Python 3.11 (versi deploy, dipilih demi OR-Tools) melarangnya. Pernah
# menggagalkan seluruh deploy dengan SyntaxError yang tidak muncul lokal.
BACKSLASH = chr(92)


def backslash_dalam_fstring(teks: str) -> list[int]:
    temuan = []
    for m in re.finditer(r'([fF][rR]?|[rR][fF])(\'\'\'|"""|\'|")', teks):
        kutip, i, depth = m.group(2), m.end(), 0
        while i < len(teks):
            if teks[i:i + len(kutip)] == kutip and depth == 0:
                break
            c = teks[i]
            if c == '{' and teks[i:i + 2] != '{{':
                depth += 1
            elif c == '{' and teks[i:i + 2] == '{{':
                i += 1
            elif c == '}' and depth > 0:
                depth -= 1
            elif c == BACKSLASH and depth > 0:
                temuan.append(teks[:i].count(chr(10)) + 1)
            i += 1
    return temuan


for f in BERKAS_PY:
    baris = backslash_dalam_fstring((FOLDER / f).read_text(encoding="utf-8"))
    periksa(f"f-string aman 3.11 · {f}", not baris,
            "SyntaxError saat deploy, tidak terlihat di Python 3.12 lokal",
            f"baris {baris}" if baris else "")


# ====================================================== 3. ATURAN CSS RAPUH
CSS = (FOLDER / "tampilan.py").read_text(encoding="utf-8")

periksa("toolbar tidak disembunyikan", 'display:flex !important' in
        CSS.split('[data-testid="stToolbar"]')[1][:60]
        if '[data-testid="stToolbar"]' in CSS else False,
        "display:none pada stToolbar membuat tombol buka sidebar 0x0 — "
        "sidebar yang tertutup tidak bisa dibuka lagi selamanya")

periksa("header tidak dinolkan", "height:0" not in
        CSS.split('header[data-testid="stHeader"]')[1][:80]
        if 'header[data-testid="stHeader"]' in CSS else False,
        "height:0 pada header mengempiskan tombol buka sidebar menjadi 0x0")

periksa("motif sudut dikecualikan dari z-index",
        ":not(.awan)" in CSS,
        "tanpa pengecualian, awan SVG dipaksa position:relative dan "
        "menambah ~230px ruang kosong di bawah angka bar")

periksa("angka tidak boleh membungkus",
        "white-space:nowrap" in CSS.split(".angka {")[1][:260]
        if ".angka {" in CSS else False,
        "Rp4.370.000 patah menjadi 'Rp4.370.00' + '0' — angkanya salah dibaca")

periksa("ukuran angka mengikuti lebar kartu",
        "cqi" in CSS and "container-type:inline-size" in CSS,
        "ukuran tetap 44px membuat angka membungkus pada kartu sempit")

periksa("isi tombol rata kiri di kedua lapis",
        CSS.count("justify-content:flex-start") >= 2,
        "hanya lapis luar yang diratakan → tepi kiri tombol bergerigi, "
        "tiap tombol mulai di titik berbeda")

periksa("font ikon tidak tertimpa",
        "Material Symbols" in CSS,
        "font ikon tertimpa → ligatur batal, kata 'visibility' muncul mentah")

periksa("aturan ponsel ada",
        "@media (max-width: 992px)" in CSS,
        "sidebar 300px pada layar 375px menyisakan 75px dan menimbun isinya")


# ================================================ 4. ANGKA INTI TIDAK BERUBAH
sys.path.insert(0, str(FOLDER))
import biaya as B                                            # noqa: E402
import ekstraksi as E                                        # noqa: E402
import solver as S                                           # noqa: E402
from buku import Buku, buku_contoh                           # noqa: E402

ANGKA_ACUAN = {
    "biaya penuh": (B.biaya_penuh(p=B.BAKU), 574_400),
    "upah harian": (B.UPAH_PER_HARI, 67_000),
    "margin": (B.HARGA_RATA - B.biaya_penuh(p=B.BAKU), 100_600),
    "impas upah formal": (round(B.titik_impas_upah_formal(B.BAKU)), 762_276),
}
for nama, (nyata, harus) in ANGKA_ACUAN.items():
    periksa(f"angka · {nama}", round(nyata) == harus,
            "seluruh proposal memakai angka ini; berubah diam-diam = "
            "klaim di deck tidak lagi dapat direproduksi",
            f"{round(nyata):,} != {harus:,}")


# ================================================== 5. EKSTRAKSI ENAM KALIMAT
KALIMAT_UJI = [
    ("td beli kain sm bu ani 5 lembar, 400 apa 450 ya lupa", "BELI", None),
    ("mulai garap megamendung buat bu risa", "MULAI", None),
    ("wis dilorod kabeh, siki ngenteni garing", "SELESAI", None),
    ("laku 1 kain megamendung 850rb", "JUAL", None),
    ("ada yang nawar 550rb buat kain sogan, ambil ga?", "TANYA", "tawar"),
    ("apa jenis batik yang paling laku?", "TANYA", "peringkat"),
]
for teks, jenis_harus, maksud_harus in KALIMAT_UJI:
    h = E.ekstrak_aturan(teks)
    cocok = h["jenis"] == jenis_harus and (
        maksud_harus is None or h.get("maksud") == maksud_harus)
    periksa(f"ekstraksi · {teks[:34]}…", cocok,
            "enam kalimat ini adalah tombol contoh yang pasti dicoba juri",
            f"dapat {h['jenis']}/{h.get('maksud')}, "
            f"harusnya {jenis_harus}/{maksud_harus}")

# "400 apa 450 ya lupa" TIDAK boleh dianggap pertanyaan
h = E.ekstrak_aturan("td beli kain sm bu ani 5 lembar, 400 apa 450 ya lupa")
periksa("kalimat ragu bukan pertanyaan", h["jenis"] == "BELI",
        "deteksi pertanyaan yang terlalu longgar menelan pencatatan ragu, "
        "dan fitur konfirmasi satu ketuk mati")
periksa("dua pilihan harga terbaca", len(h.get("pilihan_harga", [])) == 2,
        "tanpa ini tombol [Rp400rb][Rp450rb] tidak pernah muncul")

# motif yang disebut tidak boleh nyasar ke kain lain
b = buku_contoh().pakai(B.BAKU)
d = b.catat({"jenis": "JUAL", "produk": "singabarong", "harga": None})
periksa("penjualan menempel pada motif yang benar",
        d.get("kain") and d["kain"].produk == "singabarong",
        "'singabarong laku' pernah tercatat pada megamendung yang sedang "
        "dikerjakan — salah kain berarti salah hari kerja")


# ===================================================== 5b. PESAN & KOMITMEN
KALIMAT_PESAN = [
    ("ada yang DP 3 kain megamendung", "megamendung", 3),
    ("pesenan 5 wadasan masuk", "wadasan", 5),
    ("ada pre-order sogan 2", "sogan", 2),
]
for teks, produk_harus, qty_harus in KALIMAT_PESAN:
    h = E.ekstrak_aturan(teks)
    periksa(f"PESAN terdeteksi · {teks[:30]}…",
            h["jenis"] == "PESAN" and h.get("qty") == qty_harus,
            "consultant AI sempat mengusulkan menambah intent PESAN; "
            "ini menguncinya supaya tidak diam-diam berhenti terdeteksi",
            f"dapat jenis={h['jenis']} qty={h.get('qty')}, "
            f"harusnya PESAN/{qty_harus}")

# JUAL tidak boleh disalahartikan sebagai PESAN — kain yang SUDAH terjual
# beda siklus hidup dari yang BARU dipesan.
h = E.ekstrak_aturan("laku 3 kain megamendung 900rb")
periksa("JUAL tidak tertukar dengan PESAN", h["jenis"] == "JUAL",
        "kalau tertukar, kain yang sudah terjual malah dihitung dua kali "
        "sebagai komitmen yang belum dikerjakan")

# Komitmen harus lahir dari Buku.pesanan, BUKAN ditempel ke objek Motif dari
# luar — objek Motif dibangun ulang dari nol setiap Solver Pesanan dibuka,
# jadi apa pun yang ditempelkan langsung akan hilang lagi.
b3p = Buku().pakai(B.BAKU)
b3p.catat({"jenis": "PESAN", "produk": "megamendung", "qty": 3})
b3p.catat({"jenis": "PESAN", "produk": "megamendung", "qty": 2})
komit = b3p.komitmen_per_motif()
periksa("komitmen terkumpul per motif dari Buku.pesanan",
        komit.get("megamendung") == 5,
        "dua PESAN untuk motif yang sama harus terjumlah, bukan saling timpa",
        f"dapat {komit}")

motif_baru = S.motif_dari_buku(b3p, B.BAKU)
m_megamendung = next((m for m in motif_baru if m.nama == "megamendung"), None)
# b3p sudah dikenai DUA kejadian PESAN sebelumnya (3 + 2), jadi komitmennya
# yang benar adalah 5 — sama seperti pada pemeriksaan komitmen_per_motif().
periksa("motif TANPA riwayat penjualan tetap muncul bila sudah dipesan",
        m_megamendung is not None and m_megamendung.komitmen == 5,
        "consultant AI mengusulkan menempel komitmen ke Motif yang sudah "
        "ada — tetapi motif yang belum pernah terjual pun harus tetap "
        "muncul di solver begitu ada pesanannya",
        f"dapat {m_megamendung}")

hasil_pesan = S.optimalkan(motif_baru, 18, B.BAKU)
periksa("solver menghormati komitmen sebagai batas bawah",
        hasil_pesan["pilihan"].get("megamendung", 0) >= 5,
        "kalau komitmen diabaikan, solver bisa menyarankan MENGERJAKAN "
        "LEBIH SEDIKIT daripada yang sudah dijanjikan ke pembeli",
        f"pilihan megamendung = {hasil_pesan['pilihan'].get('megamendung')}")

# Bolak-balik cadangan tidak boleh menjatuhkan pesanan
b4p, _ = Buku.dari_kamus(b3p.ke_kamus())
periksa("cadangan memulihkan pesanan",
        b4p.komitmen_per_motif().get("megamendung") == 5,
        "pesanan yang hilang saat dipulihkan berarti komitmen ke pembeli "
        "ikut hilang tanpa jejak")


# ============================================================== 6. SOLVER
b2 = buku_contoh().pakai(B.BAKU)
hasil = S.optimalkan(S.motif_dari_buku(b2, B.BAKU), 18, B.BAKU)
periksa("solver memakai OR-Tools", "OR-Tools" in hasil["metode"],
        "kalau turun ke greedy diam-diam, klaim 'solver ILP' pada deck "
        "tidak lagi benar", hasil["metode"])
periksa("LP dihitung sebagai batas atas", hasil.get("lp") is not None,
        "tanpa LP tidak ada bukti optimalitas maupun ongkos kebulatan")
periksa("LP >= ILP", (hasil["lp"]["laba"] + 1e-6) >= hasil["laba"]
        if hasil.get("lp") else False,
        "relaksasi LP harus selalu >= ILP; kalau tidak, rumusannya salah")


# ================================================ 7. TEMPLAT DUA BAHASA UTUH
import bahasa as L                                           # noqa: E402

kunci_id = {k for k, v in L.TEMPLAT["id"].items() if isinstance(v, str)}
kunci_crb = {k for k, v in L.TEMPLAT["crb"].items() if isinstance(v, str)}
hilang = kunci_id - kunci_crb - {"nama"}
periksa("templat Cirebon lengkap", not hilang,
        "kunci yang hilang membuat balasan diam-diam jatuh ke bahasa "
        "Indonesia di tengah percakapan Cirebon", f"hilang: {hilang}")

periksa("nama motif bukan penanda bahasa",
        "megamendung" not in L.KATA_CIREBON,
        "'laku 1 kain megamendung 850rb' pernah dikira bahasa Cirebon")
periksa("kata Indonesia bukan penanda bahasa",
        not ({"bayar", "garap", "beres"} & L.KATA_CIREBON),
        "'bayar mbak sri 300rb' pernah dikira bahasa Cirebon")


# ============================================ 8. SIMPAN & PULIHKAN UTUH
b3 = buku_contoh().pakai(B.BAKU.ubah(bahan=180_000, upah_per_hari=75_000))
b4, p4 = Buku.dari_kamus(b3.ke_kamus())
periksa("cadangan memulihkan kain", len(b3.kain) == len(b4.kain),
        "data hilang saat dipulihkan")
periksa("cadangan memulihkan kalibrasi", p4.bahan == 180_000
        and p4.upah_per_hari == 75_000,
        "kalibrasi hilang → seluruh angka berubah setelah dipulihkan")
periksa("cadangan memulihkan laba",
        b3.statistik()["laba"] == b4.statistik()["laba"],
        "angka berubah setelah pulih = cadangan tidak dapat dipercaya")


# ==================================================== 9. ASET & BERAT HALAMAN
import tampilan as T                                         # noqa: E402

for nama in ["logo-bi", "logo-canting", "logo-canting-ikon", "megamendung"]:
    periksa(f"aset · {nama}", T.berkas_gambar(nama) is not None,
            "aset hilang → logo/motif tidak tampil di aplikasi yang disebar")

berat = sum(len(T.berkas_gambar(n) or "") for n in
            ["logo-bi", "logo-canting", "logo-canting-ikon", "megamendung"]) / 1024
periksa(f"berat aset {berat:.0f} KB <= 260 KB", berat <= 260,
        "aset besar memperlambat lukisan pertama, terasa paling parah "
        "tepat setelah peladen bangun dari tidur")


# ===================================================== 10. KUNCI TIDAK BOCOR
for f in BERKAS_PY + ["README.md"]:
    isi = (FOLDER / f).read_text(encoding="utf-8")
    bocor = re.search(r'(AIza[\w-]{30,}|AQ\.[\w-]{30,}|sk-ant-[\w-]{20,})', isi)
    periksa(f"tanpa kunci API · {f}", bocor is None,
            "kunci yang ikut ter-commit menjadi publik selamanya",
            bocor.group()[:18] + "…" if bocor else "")


# ================================================================== LAPORAN
print(f"\n{'':2}CANTING AI — uji regresi")
print(f"{'':2}{'-' * 62}")
for nama, _, _ in lulus:
    print(f"{'':2}✓  {nama}")
if gagal:
    print()
    for nama, riwayat, rincian in gagal:
        print(f"{'':2}✗  {nama}")
        if rincian:
            print(f"{'':5}{rincian}")
        print(f"{'':5}riwayat: {riwayat}")
print(f"{'':2}{'-' * 62}")
print(f"{'':2}{len(lulus)} lulus, {len(gagal)} gagal\n")
sys.exit(1 if gagal else 0)
