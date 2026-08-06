# -*- coding: utf-8 -*-
"""
Modul bahasa CANTING AI.

PRINSIP ARSITEKTUR
------------------
Masukan  : fleksibel — LLM + leksikon menafsirkan kalimat apa adanya.
Keluaran : TEMPLAT — kalimat sudah ditulis lebih dulu, sistem hanya mengisi slot.

Alasannya: model bahasa besar lemah membangkitkan bahasa Cirebon (bahasa
berdaya-rendah). Kalau AI disuruh mengarang kalimat Cirebon, hasilnya ngawur.
Dengan templat, kebenaran bahasanya dijamin manusia, dan ragam bebasan
terkunci sehingga sistem tidak pernah keliru sopan-santun.

⚠️  STATUS VALIDASI
Entri bertanda VALIDASI=False disusun dari rujukan tertulis, BUKAN dari
penutur asli. Wajib diperiksa penutur asli Ciwaringin sebelum dipakai di
depan juri. Istilah proses batik (kelompok pertama) relatif aman karena
terdokumentasi luas.
"""

VALIDASI_PENUTUR_ASLI = False   # ubah ke True setelah diperiksa penutur asli

# ============================================================== L E K S I K O N
# Kata-kata ini dipakai dua arah: membantu ekstraksi, dan menandai bahasa apa
# yang sedang dipakai pengguna.

PROSES_BATIK = {
    # kata kerja proses — penanda bahasa yang KUAT, terdokumentasi luas
    "nglowong": "menggambar kerangka motif dengan canting",
    "nglowongi": "menggambar kerangka motif dengan canting",
    "nembok": "menutup bidang dengan malam",
    "nyolet": "mewarnai dengan kuas",
    "medel": "mencelup indigo",
    "wedel": "mencelup indigo",
    "nyoga": "mencelup soga",
    "nglorod": "merebus untuk melepas malam",
    "lorod": "merebus untuk melepas malam",
    "dilorod": "sudah dilepas malamnya",
    "mbatik": "membatik",
    "nyanting": "membatik dengan canting",
}

BENDA_BATIK = {
    # BUKAN penanda bahasa — kata-kata ini lazim juga dalam bahasa Indonesia
    "mori": "kain dasar",
    "malam": "lilin batik",
    "canting": "alat tulis malam",
    "gawangan": "rangka penyangga kain",
    "soga": "pewarna cokelat alami",
    "indigo": "pewarna biru alami",
    "nila": "pewarna biru alami",
}

MOTIF = {
    # BUKAN penanda bahasa — ini nama produk, dipakai penutur mana pun.
    # Dulu keliru dimasukkan sebagai penanda, sehingga kalimat Indonesia
    # "laku 1 kain megamendung 850rb" salah dikenali sebagai bahasa Cirebon.
    "megamendung": "motif awan khas Cirebon",
    "wadasan": "motif batu karang",
    "singabarong": "motif singa bersayap",
    "paksinaga": "motif paksi naga liman",
    "sogan": "kain bercorak soga",
}

ISTILAH_BATIK = {**PROSES_BATIK, **BENDA_BATIK, **MOTIF}   # untuk ekstraksi

KATA_KERJA = {          # VALIDASI=False — perlu diperiksa penutur asli
    "tuku": "beli",
    "tumbas": "beli (bebasan)",
    "adol": "jual",
    "sade": "jual (bebasan)",
    "payu": "laku / terjual",
    "pajeng": "laku (bebasan)",
    "mbayar": "bayar",
    "rampung": "selesai",
    "entek": "habis",
    "telas": "habis (bebasan)",
    "wiwit": "mulai",
    "miwiti": "mulai",
    "gawe": "buat / kerja",
    "damel": "buat (bebasan)",
    "ngenteni": "menunggu",
    "ngantosi": "menunggu (bebasan)",
    "garing": "kering",
}

KATA_BERSAMA = {
    # Dipakai penutur DUA bahasa, jadi BUKAN penanda. Dulu keliru dimasukkan
    # ke KATA_KERJA sehingga "bayar mbak sri 300rb" dan "mulai garap
    # megamendung" salah dikenali sebagai bahasa Cirebon.
    "bayar": "bayar",
    "garap": "kerjakan",
    "beres": "selesai",
    "mulai": "mulai",
    "jual": "jual",
    "beli": "beli",
    "laku": "terjual",
}

WAKTU_DAN_PENANDA = {   # VALIDASI=False
    "wis": "sudah",
    "wus": "sudah",
    "sampun": "sudah (bebasan)",
    "durung": "belum",
    "dereng": "belum (bebasan)",
    "arep": "akan / mau",
    "badhe": "akan (bebasan)",
    "siki": "sekarang",
    "sekiye": "sekarang",
    "wingi": "kemarin",
    "mengko": "nanti",
    "dina": "hari",
    "dinten": "hari (bebasan)",
    "kabeh": "semua",
    "sedaya": "semua (bebasan)",
}

BILANGAN = {            # VALIDASI=False — penting, tanpa ini nominal hilang
    "siji": 1, "loro": 2, "telu": 3, "papat": 4, "lima": 5,
    "enem": 6, "pitu": 7, "wolu": 8, "sanga": 9, "sepuluh": 10,
    "rolas": 12, "limalas": 15, "rongpuluh": 20, "selawe": 25,
    "telungpuluh": 30, "seket": 50, "sewidak": 60,
}

PENGALI = {
    "atus": 100, "atusan": 100,
    "ewu": 1_000, "ewon": 1_000, "rebu": 1_000, "ribu": 1_000, "rb": 1_000,
    "yuta": 1_000_000, "juta": 1_000_000, "jt": 1_000_000,
}

# Penanda bahasa Cirebon — SENGAJA tidak memasukkan nama motif dan nama benda,
# karena keduanya dipakai juga oleh penutur bahasa Indonesia.
KATA_CIREBON = (
    set(PROSES_BATIK) | set(KATA_KERJA) | set(WAKTU_DAN_PENANDA) | set(BILANGAN)
)


# ============================================================== T E M P L A T
# Slot diisi sistem. Ragam Cirebon dikunci di BEBASAN — ragam halus untuk
# orang yang dituakan. Jangan pernah memakai bagongan untuk membalas pemilik.

TEMPLAT = {
    "id": {
        "nama": "Indonesia",
        "sapaan": "Halo! Saya CANTING. Cerita saja seperti biasa — "
                  "beli apa, mulai garap apa, laku berapa.",
        "beli": "Tercatat: {item} {qty} × {harga}. Total {total}.",
        "beli_ragu": "Saya catat {harga} dulu ya (bisa dikoreksi).",
        "mulai": "Tercatat: mulai mengerjakan {produk}, {tanggal}.",
        "selesai": "Tercatat: {produk} selesai — {hari} hari kerja.",
        "jual_untung": "Tercatat. Biaya penuh {biaya} → untung {margin}, "
                       "setara {per_hari} per hari kerja.",
        "jual_rugi": "Tercatat. Biaya penuh {biaya} → RUGI {margin}. "
                     "Harga ini {kurang} di bawah titik impas.",
        "bayar": "Tercatat: pengeluaran {kategori} {nominal}.",
        "tanya_terima": "Biaya penuh {produk} {biaya}. Tawaran {tawaran} "
                        "masih untung {margin} ({per_hari} per hari kerja). "
                        "Layak diambil.",
        "tanya_tolak": "Biaya penuh {produk} {biaya}. Tawaran {tawaran} "
                       "RUGI {margin}. Lantai harga Anda {lantai}.",
        "jual_tanpa_harga": "{produk} tercatat terjual. Terjual berapa? "
                            "Sebutkan angkanya saja, mis. \"850rb\".",
        "beli_tanpa_harga": "{item} tercatat. Habis berapa? "
                            "Sebutkan angkanya saja, mis. \"400rb\".",
        "tanya_peringkat": "Diurutkan menurut untung per hari kerja — bukan menurut "
                           "harga jual:\n{daftar}\n\nDahulukan {teratas}. "
                           "{catatan}",
        "peringkat_kosong": "Belum ada kain terjual yang tercatat, jadi peringkatnya "
                            "belum bisa dihitung. Catat dulu beberapa penjualan.",
        "tanya_umum": "Yang bisa saya jawab sekarang:\n"
                      "• motif mana yang paling menguntungkan per hari kerja\n"
                      "• layak tidaknya sebuah tawaran — sebutkan angkanya\n"
                      "• biaya penuh & lantai harga per kain\n\n"
                      "Biaya penuh saat ini {biaya}, lantai harga {lantai}.",
        "tidak_paham": "Maaf, saya belum menangkap maksudnya. "
                       "Boleh diulang dengan kalimat lain?",
        "ringkasan_judul": "Ringkasan minggu ini",
        "kendala_kapasitas": "Slot produksi penuh → kendala Anda: kapasitas. "
                             "Naikkan harga, dahulukan untung per hari tertinggi.",
        "kendala_permintaan": "Slot produksi kosong {kosong} hari → kendala Anda: "
                              "permintaan, bukan kapasitas. Jangan naikkan harga "
                              "dulu; dahulukan motif cepat.",
    },
    "crb": {
        "nama": "Cerbon",
        "ragam": "bebasan",
        "sapaan": "Sugeng rawuh. Kula CANTING. Cariyos kemawon sakersanipun — "
                  "tumbas napa, miwiti damel napa, pajeng pinten.",
        "beli": "Sampun kacatet: {item} {qty} × {harga}. Gunggungipun {total}.",
        "beli_ragu": "Kula catet {harga} rumiyin nggih (saged dipun leresaken).",
        "mulai": "Sampun kacatet: miwiti damel {produk}, {tanggal}.",
        "selesai": "Nggih, sampun kacatet — {produk} rampung. {hari} dinten kerja.",
        "jual_untung": "Sampun kacatet. Waragad sedaya {biaya} → bathi {margin}, "
                       "sami kaliyan {per_hari} saben dinten kerja.",
        "jual_rugi": "Sampun kacatet. Waragad sedaya {biaya} → RUGI {margin}. "
                     "Rega punika {kurang} ing ngandhap titik impas.",
        "bayar": "Sampun kacatet: wedalan {kategori} {nominal}.",
        "tanya_terima": "Waragad sedaya {produk} {biaya}. Panawaran {tawaran} "
                        "taksih bathi {margin} ({per_hari} saben dinten kerja). "
                        "Sae dipun tampi.",
        "tanya_tolak": "Waragad sedaya {produk} {biaya}. Panawaran {tawaran} "
                       "RUGI {margin}. Rega paling andhap panjenengan {lantai}.",
        "jual_tanpa_harga": "{produk} sampun kacatet pajeng. Pajeng pinten? "
                            "Cekap sebutaken angkanipun, tuladha \"850ewu\".",
        "beli_tanpa_harga": "{item} sampun kacatet. Telas pinten? "
                            "Cekap sebutaken angkanipun, tuladha \"400ewu\".",
        "tanya_peringkat": "Dipun urutaken miturut bathi saben dinten kerja — sanes "
                           "miturut rega sade:\n{daftar}\n\nDahulukaken {teratas}. "
                           "{catatan}",
        "peringkat_kosong": "Dereng wonten kain pajeng ingkang kacatet, dados "
                            "urutanipun dereng saged kaétang.",
        "tanya_umum": "Ingkang saged kula wangsuli sapunika:\n"
                      "• motif pundi ingkang paling bathi saben dinten kerja\n"
                      "• sae menapa boten satunggaling panawaran — sebutaken reginipun\n"
                      "• waragad sedaya & rega paling andhap saben kain\n\n"
                      "Waragad sapunika {biaya}, rega paling andhap {lantai}.",
        "tidak_paham": "Nyuwun pangapunten, kula dereng mangertos. "
                       "Saged dipun wangsuli mawi ukara sanes?",
        "ringkasan_judul": "Ringkesan minggu punika",
        "kendala_kapasitas": "Slot damel kebak → alangan panjenengan: kapasitas. "
                             "Regi dipun inggilaken, dahulukaken bathi saben dinten "
                             "ingkang paling inggil.",
        "kendala_permintaan": "Slot damel kosong {kosong} dinten → alangan "
                              "panjenengan: pesenan, sanes kapasitas. Sampun "
                              "ngindhakaken regi rumiyin; dahulukaken motif cepet.",
    },
}


def deteksi_bahasa(teks: str) -> str:
    """Tebak bahasa dari kata-kata penanda. Kembalikan 'crb' atau 'id'."""
    kata = set(teks.lower().replace(",", " ").replace(".", " ").split())
    return "crb" if kata & KATA_CIREBON else "id"


def ambil(bahasa: str, kunci: str, **slot) -> str:
    """Ambil templat lalu isi slotnya. Jatuh ke Indonesia bila kunci hilang."""
    kamus = TEMPLAT.get(bahasa, TEMPLAT["id"])
    templat = kamus.get(kunci) or TEMPLAT["id"].get(kunci, "")
    try:
        return templat.format(**slot)
    except KeyError:
        return templat


if __name__ == "__main__":
    print("Kata penanda Cirebon terdaftar:", len(KATA_CIREBON))
    for t in ["wis dilorod kabeh, siki ngenteni garing",
              "laku 1 kain megamendung 850rb",
              "td beli kain sm bu ani 5 lembar"]:
        print(f"  {deteksi_bahasa(t):4} <- {t}")
    print()
    print(ambil("crb", "selesai", produk="megamendung", hari=6))
    print(ambil("id", "selesai", produk="megamendung", hari=6))
