# -*- coding: utf-8 -*-
"""
Ekstraksi kejadian dari kalimat sehari-hari — inti "pencatatan tanpa mencatat".

Dua jalur:
  1. LLM (Claude)   — jalur utama. Menangani kalimat berantakan, campur kode,
                      singkatan, dan bahasa Cirebon.
  2. Aturan         — jalur cadangan. Dipakai bila kunci API tidak ada, kuota
                      habis, atau jaringan mati.

Jalur cadangan itu disengaja: demo yang mati di depan juri lebih merugikan
daripada demo yang sedikit lebih sederhana.

Tujuh jenis kejadian sudah cukup untuk menghitung seluruh angka pada proposal:
  BELI · MULAI · SELESAI · JUAL · BAYAR · TANYA · PESAN
Pasangan MULAI+SELESAI itulah yang melahirkan "hari kerja" — variabel yang
selama ini tidak pernah ada di UMKM mana pun.

PESAN itu beda dari JUAL: PESAN adalah janji kerja di masa depan (DP,
pre-order, "pesenan masuk") — belum ada kain yang dikerjakan, apalagi
terjual. JUAL adalah kain yang SUDAH terjual. Membedakan dua ini penting
karena PESAN menjadi "komitmen" bagi Solver Pesanan (solver.py): kain yang
sudah dijanjikan harus diutamakan sebelum kapasitas sisa dipakai untuk
motif lain, betapa pun untung/harinya lebih rendah.
"""
from __future__ import annotations

import json
import os
import re

from bahasa import ISTILAH_BATIK, MOTIF, BILANGAN, PENGALI, deteksi_bahasa

MODEL = os.environ.get("CANTING_MODEL", "claude-sonnet-5")

JENIS_SAH = {"BELI", "MULAI", "SELESAI", "JUAL", "BAYAR", "TANYA", "PESAN",
             "TIDAK_PAHAM"}

INSTRUKSI = """Kamu mesin ekstraksi untuk pembukuan UMKM batik tulis di Cirebon.
Pemilik usaha menulis apa adanya: berantakan, disingkat, ragu, sering bercampur
bahasa Cirebon (Jawa-Cirebonan). Tugasmu mengubahnya menjadi JSON.

Kembalikan HANYA JSON, tanpa penjelasan, dengan bentuk:
{
  "jenis": "BELI|MULAI|SELESAI|JUAL|BAYAR|TANYA|PESAN|TIDAK_PAHAM",
  "maksud": "tawar|peringkat|umum" atau null,   // hanya diisi bila jenis TANYA
  "produk": string atau null,      // nama motif, mis. "megamendung"
  "item": string atau null,        // barang yang dibeli, mis. "kain mori"
  "qty": angka atau null,
  "harga": angka atau null,        // dalam rupiah penuh, mis. 850000
  "pilihan_harga": [angka] ,       // isi bila pemilik menyebut lebih dari satu
  "kategori": string atau null,    // untuk BAYAR: upah/listrik/pewarna/lain
  "keyakinan": 0.0 sampai 1.0
}

Aturan:
- "850rb", "850ewu", "850 ribu" = 850000. "1jt" = 1000000.
- Angka telanjang di bawah 10000 pada konteks harga berarti ribuan: 400 = 400000.
- Kalau pemilik menyebut dua kemungkinan harga ("400 apa 450 ya lupa"),
  isi pilihan_harga dengan keduanya dan turunkan keyakinan di bawah 0.6.
- Istilah proses batik menandakan tahap pengerjaan:
  nglowong/nembok/nyolet/medel = MULAI atau sedang berjalan;
  nglorod/dilorod/rampung/beres = SELESAI.
- "payu"/"laku"/"pajeng"/"adol" = JUAL (kain SUDAH terjual).
- "tuku"/"tumbas"/"beli" = BELI.
- "dp"/"pesenan"/"pesanan"/"pre-order"/"preorder"/"po"/"pesen"/"order masuk"
  = PESAN (janji kerja di masa depan, BELUM ada kain yang dikerjakan/terjual).
  Isi "produk" dan "qty" dari kalimatnya.
  Contoh: "ada yang DP 3 kain megamendung" -> PESAN, produk=megamendung, qty=3.
  Contoh: "pesenan 5 wadasan masuk" -> PESAN, produk=wadasan, qty=5.
  JANGAN keliru dengan JUAL: "laku 3 kain megamendung" itu JUAL, bukan PESAN,
  karena kainnya sudah selesai dan terjual, bukan baru dipesan.
- Pertanyaan = TANYA, lalu isi "maksud":
    "tawar"     -> menilai sebuah penawaran ("ada nawar 550rb, ambil ga?")
    "peringkat" -> menanyakan motif mana yang paling menguntungkan
    "umum"      -> pertanyaan lain
  PENTING: "400 apa 450 ya lupa" BUKAN pertanyaan — itu pencatatan yang ragu.
- Kalau benar-benar tidak jelas, jenis = TIDAK_PAHAM dan keyakinan rendah.
"""


# ------------------------------------------------------------------ CADANGAN
def _angka_dari_teks(teks: str) -> list[int]:
    """Ambil semua nominal rupiah yang disebut, termasuk bentuk lisan Cirebon."""
    t = teks.lower().replace(".", "").replace(",", " ")
    hasil: list[int] = []

    # bentuk angka + satuan: 850rb, 1jt, 450 ribu, 850ewu
    pola = r"(\d+(?:[.,]\d+)?)\s*(rb|ribu|rebu|ewu|ewon|jt|juta|yuta|k)?\b"
    for cocok in re.finditer(pola, t):
        n = float(cocok.group(1).replace(",", "."))
        satuan = cocok.group(2)
        if satuan:
            n *= PENGALI.get(satuan, 1_000 if satuan == "k" else 1)
        elif n < 10_000:
            n *= 1_000          # angka telanjang pada konteks harga = ribuan
        hasil.append(int(n))

    # bentuk lisan: "wolung atus seket ewu"
    kata = t.split()
    for i, k in enumerate(kata):
        if k in BILANGAN:
            nilai = BILANGAN[k]
            for lanjut in kata[i + 1:i + 3]:
                if lanjut in PENGALI:
                    nilai *= PENGALI[lanjut]
            if nilai >= 1_000:
                hasil.append(int(nilai))

    return [n for n in hasil if n >= 1_000]


def _produk_dari_teks(teks: str, motif_dikenal=()) -> str | None:
    """Kenali nama motif dari kalimat.

    Motif bawaan hanya lima. UMKM batik jelas membuat motif lain, dan namanya
    tidak mungkin ditebak lebih dulu. Karena itu daftar motif yang SUDAH ADA
    di buku pengguna ikut diperiksa — begitu sebuah motif tercatat sekali,
    entah lewat tabel atau lewat percakapan, namanya langsung dikenali
    seterusnya. Sistemnya belajar dari datanya sendiri, bukan dari kode.
    """
    t = teks.lower()
    # nama panjang diperiksa lebih dulu agar "sogan" tidak menutupi
    # motif lain yang kebetulan memuat kata itu
    semua = sorted({*(m.lower() for m in motif_dikenal), *MOTIF},
                   key=len, reverse=True)
    for motif in semua:
        if motif and motif in t:
            return motif
    return None


KUNCI_JENIS = [
    # PESAN diperiksa PALING AWAL. Alasannya: "pesenan 5 wadasan masuk" tidak
    # mengandung kata kunci JUAL apa pun, tetapi kalimat semacam "DP buat
    # dikerjakan" bisa memuat kata yang tumpang tindih dengan MULAI ("digarap
    # nanti"). Kata kuncinya sengaja spesifik (bukan "pesen" saja) supaya
    # tidak salah menangkap kalimat lain yang kebetulan memuat suku kata itu.
    ("PESAN",   ["dp ", "dp,", "dp.", "pesenan", "pesanan", "pre-order",
                 "preorder", "pre order", "order masuk", "orderan masuk"]),
    ("SELESAI", ["nglorod", "dilorod", "lorod", "rampung", "beres", "selesai",
                 "kelar", "udah jadi", "sudah jadi"]),
    ("JUAL",    ["payu", "pajeng", "laku", "adol", "sade", "terjual", "kejual"]),
    ("BELI",    ["tuku", "tumbas", "beli", "belanja", "kulakan"]),
    ("MULAI",   ["wiwit", "miwiti", "mulai", "garap", "nggarap", "nglowong",
                 "nembok", "nyolet", "medel", "nyoga", "mbatik", "nyanting"]),
    ("BAYAR",   ["bayar", "mbayar", "gaji", "upah", "listrik", "bayaran"]),
]

# Penanda pertanyaan diperiksa LEBIH DULU daripada kata kerja transaksi.
# Tanpa ini, "apa jenis batik yang paling laku?" tertangkap sebagai JUAL hanya
# karena mengandung kata "laku", padahal itu pertanyaan.
KATA_AWAL_TANYA = ("apa", "apakah", "gimana", "bagaimana", "berapa", "mana",
                   "motif apa", "kenapa", "bisakah", "haruskah")
FRASA_TANYA = ("ambil ga", "ambil gak", "boleh ga", "boleh gak", "terima ga",
               "worth it", "untung ga", "layak ga", "sebaiknya", "nawar",
               "ditawar", "menawar")
KUNCI_PERINGKAT = ("paling laku", "paling untung", "paling menguntungkan",
                   "paling bagus", "paling cepet", "paling cepat", "terlaris",
                   "terbaik", "jenis batik", "motif apa", "motif mana",
                   "yang paling", "peringkat", "urutan")


def _apakah_pertanyaan(t: str) -> bool:
    """Deteksi pertanyaan secara ketat.

    Sengaja TIDAK memakai keberadaan kata "apa" di mana pun, sebab kalimat
    seperti "400 apa 450 ya lupa" adalah pencatatan yang ragu — bukan
    pertanyaan. Yang dipakai: tanda tanya di akhir, kata tanya di awal
    kalimat, atau frasa tanya yang eksplisit.
    """
    t = t.strip().lower()
    if t.endswith("?"):
        return True
    if t.startswith(KATA_AWAL_TANYA):
        return True
    return any(f in t for f in FRASA_TANYA)


def ekstrak_aturan(teks: str, motif_dikenal=()) -> dict:
    """Cadangan berbasis aturan. Selalu jalan, tidak butuh jaringan."""
    t = teks.lower()
    harga_list = _angka_dari_teks(teks)
    maksud = None

    if _apakah_pertanyaan(t):
        jenis = "TANYA"
        if any(k in t for k in KUNCI_PERINGKAT):
            maksud = "peringkat"          # motif mana yang paling menguntungkan
        elif harga_list:
            maksud = "tawar"              # menilai sebuah penawaran
        else:
            maksud = "umum"
    else:
        jenis = "TIDAK_PAHAM"
        for nama, kunci in KUNCI_JENIS:
            if any(k in t for k in kunci):
                jenis = nama
                break

    qty = None
    m = re.search(r"(\d+)\s*(lembar|potong|kain|pcs|buah)", t)
    if m:
        qty = int(m.group(1))
        harga_list = [h for h in harga_list if h != int(m.group(1)) * 1_000]
    elif jenis == "PESAN":
        # Kalimat pesanan sering tidak menyebut satuan sama sekali, dan
        # angkanya bisa mendahului ATAU mengikuti nama motif:
        #   "pesenan 5 wadasan masuk"   -> angka di depan
        #   "ada pre-order sogan 2"     -> angka di belakang
        # Pola BELI/JUAL tidak perlu ini karena biasanya disertai harga, yang
        # sudah tertangkap lewat _angka_dari_teks. Di sini cukup angka mandiri
        # pertama yang bukan bagian dari kata lain.
        m2 = re.search(r"(?<!\w)(\d{1,3})(?!\w)", t)
        if m2:
            qty = int(m2.group(1))

    item = None
    for kata in ISTILAH_BATIK:
        if kata in t and kata not in MOTIF:
            item = kata
            break
    if item is None and "kain" in t:
        item = "kain mori"

    keyakinan = 0.75 if jenis != "TIDAK_PAHAM" else 0.2
    if len(harga_list) > 1:
        keyakinan = 0.45          # pemilik menyebut lebih dari satu nominal

    return {
        "jenis": jenis,
        "maksud": maksud,
        "produk": _produk_dari_teks(teks, motif_dikenal),
        "item": item,
        "qty": qty,
        "harga": harga_list[0] if harga_list else None,
        "pilihan_harga": harga_list if len(harga_list) > 1 else [],
        "kategori": "upah" if any(k in t for k in ("gaji", "upah", "mbayar")) else None,
        "keyakinan": keyakinan,
        "mesin": "aturan",
    }


# ----------------------------------------------------------------------- LLM
# Lapis ekstraksi sengaja dipisah dari lapis logika. Penyedia model boleh
# diganti tanpa menyentuh mesin biaya, diagnosa kendala, maupun templat bahasa.
# Ketergantungan pada satu penyedia bukan risiko yang ditanggung, melainkan
# yang dihindari lewat rancangan.

PENYEDIA = {
    "aturan": {"label": "Mesin aturan (tanpa kunci)", "model": None},
    "claude": {"label": "Claude", "model": os.environ.get("CANTING_MODEL_CLAUDE",
                                                          "claude-sonnet-5")},
    "gemini": {"label": "Gemini Flash", "model": os.environ.get("CANTING_MODEL_GEMINI",
                                                                "gemini-2.5-flash")},
}


def penyedia_aktif() -> tuple[str, str]:
    """Tentukan penyedia dari kunci yang tersedia — TANPA bertanya ke pengguna.

    Pemakai CANTING adalah pemilik usaha batik, bukan pengembang. Meminta
    "Kunci API" lewat antarmuka hanya membingungkan dan membuat produk terbaca
    sebagai perkakas teknis. Kunci diambil diam-diam dari Streamlit Secrets
    atau variabel lingkungan; kalau tidak ada, mesin aturan yang jalan dan
    seluruh fitur tetap berfungsi.

    Urutan pemeriksaan: Gemini dulu (ada kuota gratis), baru Claude.
    """
    def ambil(nama: str) -> str:
        nilai = os.environ.get(nama, "")
        if nilai:
            return nilai
        try:                      # st.secrets melempar bila berkas rahasia tidak ada
            import streamlit as st
            return st.secrets.get(nama, "")
        except Exception:
            return ""

    for penyedia, nama_kunci in (("gemini", "GEMINI_API_KEY"),
                                 ("claude", "ANTHROPIC_API_KEY")):
        kunci = ambil(nama_kunci)
        if kunci:
            return penyedia, kunci
    return "aturan", ""


def _bersihkan_json(mentah: str) -> dict:
    mentah = re.sub(r"^```(?:json)?|```$", "", mentah.strip(), flags=re.M).strip()
    return json.loads(mentah)


def ekstrak_claude(teks: str, key: str) -> tuple[dict | None, str]:
    try:
        import anthropic

        model = PENYEDIA["claude"]["model"]
        klien = anthropic.Anthropic(api_key=key)
        jawab = klien.messages.create(
            model=model, max_tokens=400, system=INSTRUKSI,
            messages=[{"role": "user", "content": teks}])
        data = _bersihkan_json(jawab.content[0].text)
        if data.get("jenis") not in JENIS_SAH:
            return None, "jenis kejadian tidak dikenali"
        data["mesin"] = model
        return data, ""
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"[:160]


# Daftar model Gemini DIKUNCI dan berurutan, bukan dipilih otomatis.
#
# Deteksi otomatis sebelumnya berbahaya karena dua alasan yang terbukti saat
# diuji langsung ke API:
#   1. Model bisa TERDAFTAR tetapi tidak bisa dipanggil. "gemini-2.5-flash"
#      muncul pada daftar model, namun generateContent membalas HTTP 404.
#      Pemilih otomatis akan memilihnya dan sistem gagal tanpa sebab jelas.
#   2. Perilaku sistem jadi berubah sendiri setiap Google merilis model baru —
#      persis pada masa penjurian pun bisa berganti tanpa disadari.
#
# Urutan di bawah disusun dari hasil pengukuran nyata (kalimat uji yang sama):
#   gemini-3.5-flash  2.327 ms, 364 token berpikir   <- tercepat, dipakai
#   gemini-3.6-flash  4.371 ms, 628 token berpikir   <- cadangan, terverifikasi
#   gemini-2.0-flash  cadangan generasi lama
# Bila model teratas ditarik Google, sistem turun ke berikutnya sendiri.
MODEL_GEMINI_URUT = (
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-2.0-flash",
)

_MODEL_GEMINI_TERPILIH: dict[str, str] = {}     # singgahan per kunci


def _panggil_gemini(model: str, teks: str, key: str):
    """Satu panggilan ke satu model. Kembalikan (data, galat, model_hilang)."""
    import urllib.error
    import urllib.request

    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={key}")
    badan = json.dumps({
        "systemInstruction": {"parts": [{"text": INSTRUKSI}]},
        "contents": [{"role": "user", "parts": [{"text": teks}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            # Model Gemini generasi 3 "berpikir" secara baku sebelum menulis
            # jawaban — sebagian model bahkan MENOLAK thinkingBudget=0 dengan
            # HTTP 400. Daripada bergantung pada kolom yang dukungannya beda
            # antar model, jatah token dilebihkan jauh supaya proses berpikir
            # tuntas duluan sebelum menulis JSON pendek yang diminta.
            "maxOutputTokens": 2048,
            "temperature": 0,
        },
    }).encode()
    try:
        permintaan = urllib.request.Request(
            url, data=badan, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(permintaan, timeout=20) as tanggapan:
            hasil = json.loads(tanggapan.read())

        calon = hasil.get("candidates") or [{}]
        alasan_henti = calon[0].get("finishReason", "")
        bagian = calon[0].get("content", {}).get("parts", [])
        teks_jawab = "".join(b.get("text", "") for b in bagian if "text" in b)

        if not teks_jawab:
            return None, f"keluaran kosong (finishReason={alasan_henti or '?'})", False

        try:
            data = _bersihkan_json(teks_jawab)
        except json.JSONDecodeError:
            if alasan_henti == "MAX_TOKENS":
                return None, "JSON terpotong karena batas token", False
            raise

        if data.get("jenis") not in JENIS_SAH:
            return None, "jenis kejadian tidak dikenali", False
        data["mesin"] = model
        return data, "", False
    except urllib.error.HTTPError as e:
        # 404 = model ditarik/tidak tersedia bagi kunci ini → coba model berikutnya.
        # Galat lain (429 kuota, 400 permintaan) bukan salah modelnya.
        return None, f"HTTP {e.code}: {e.read()[:100].decode('utf-8','ignore')}", e.code == 404
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"[:140], False


def ekstrak_gemini(teks: str, key: str) -> tuple[dict | None, str]:
    """Coba model sesuai URUTAN TERKUNCI, turun ke berikutnya hanya bila 404.

    Model yang berhasil disinggahi agar panggilan berikutnya langsung tepat
    sasaran — tanpa mengulangi percobaan yang sudah diketahui gagal.
    """
    urutan = list(MODEL_GEMINI_URUT)
    tersimpan = _MODEL_GEMINI_TERPILIH.get(key)
    if tersimpan in urutan:                      # dahulukan yang terbukti jalan
        urutan.remove(tersimpan)
        urutan.insert(0, tersimpan)

    galat_terakhir = "tidak ada model Gemini yang tersedia"
    for model in urutan:
        data, galat, model_hilang = _panggil_gemini(model, teks, key)
        if data is not None:
            _MODEL_GEMINI_TERPILIH[key] = model
            return data, ""
        galat_terakhir = f"{model} → {galat}"
        if not model_hilang:
            break                                # bukan salah model; hentikan
    return None, galat_terakhir


def ekstrak(teks: str, api_key: str | None = None,
            penyedia: str = "aturan", motif_dikenal=()) -> dict:
    """Antarmuka utama: coba penyedia terpilih, jatuh ke aturan bila gagal.

    Jalur cadangan itu disengaja — demo yang mati di depan juri lebih merugikan
    daripada demo yang sedikit lebih sederhana.
    """
    data, alasan = None, ""
    if penyedia == "claude" and api_key:
        data, alasan = ekstrak_claude(teks, api_key)
    elif penyedia == "gemini" and api_key:
        data, alasan = ekstrak_gemini(teks, api_key)

    if data is None:
        hasil = ekstrak_aturan(teks, motif_dikenal)
        if penyedia != "aturan":
            hasil["gagal_llm"] = alasan or "kunci API belum diisi"
    else:
        hasil = data
        hasil.setdefault("pilihan_harga", [])
        hasil.setdefault("maksud", None)
        hasil.setdefault("keyakinan", 0.9)

    hasil["bahasa"] = deteksi_bahasa(teks)
    hasil["teks_asli"] = teks
    return hasil


if __name__ == "__main__":
    contoh = [
        "td beli kain sm bu ani 5 lembar, 400 apa 450 ya lupa",
        "mulai garap megamendung buat bu risa",
        "wis dilorod kabeh, siki ngenteni garing",
        "laku 1 kain megamendung 850rb",
        "bayar mbak sri 300rb",
        "ada yang nawar 550rb buat kain sogan, ambil ga?",
    ]
    for c in contoh:
        h = ekstrak_aturan(c)
        h["bahasa"] = deteksi_bahasa(c)
        print(f"{h['jenis']:12} {h['bahasa']:4} harga={h['harga']} "
              f"pilihan={h['pilihan_harga']} produk={h['produk']} "
              f"yakin={h['keyakinan']}")
        print(f"             <- {c}")
