# -*- coding: utf-8 -*-
"""
CANTING AI — prototipe
ImpactPreneur Business Challenge · Bank Indonesia KPw Cirebon
Studi kasus: UKM Silfi Batik Tulis, Desa Ciwaringin, Kabupaten Cirebon

Jalankan:  streamlit run app.py
"""
import json
from datetime import date, timedelta

import streamlit as st

import bahasa as L
import biaya as B
import ekstraksi as E
import simpanan as SIMP
import solver as S
import tampilan as T
from buku import Buku, Kain, buku_contoh
from ekstraksi import ekstrak

def _ikon_halaman():
    """Ikon tab peramban. Pakai logo CANTING bila berkasnya ada."""
    from pathlib import Path
    for akhiran in (".png", ".jpg", ".jpeg", ".webp"):
        berkas = Path(__file__).parent / f"logo-canting{akhiran}"
        if berkas.exists():
            return str(berkas)
    return "🪶"


st.set_page_config(
    page_title="CANTING AI — Prototipe",
    page_icon=_ikon_halaman(),
    layout="wide",
    # "auto" = terbuka di layar lebar, tertutup di ponsel.
    # Sempat dipaksa "expanded" agar juri tidak kehilangan panel kalibrasi,
    # tetapi di ponsel itu justru menutupi hampir seluruh layar. Pada layar
    # lebar, CSS sudah mengunci sidebar tetap tampak, jadi "auto" aman.
    initial_sidebar_state="auto",
)
st.markdown(T.CSS, unsafe_allow_html=True)

# --------------------------------------------------------------------- STATE
# Kode usaha diambil dari alamat (?kode=XXXXXX) supaya pemilik cukup menandai
# tautannya. Penyegaran halaman, menutup tab, bahkan berganti peramban tidak
# menghilangkan datanya — selama peladennya belum didaur ulang.
def _siapkan_sesi():
    kode = (st.query_params.get("kode") or "").strip().upper()

    if kode and SIMP.ada(kode):                      # buku lama, pulihkan
        b, p = Buku.dari_kamus(SIMP.muat(kode))
    else:                                            # buku baru
        kode = kode or SIMP.kode_baru()
        b, p = buku_contoh(), B.BAKU
        SIMP.simpan(kode, b.pakai(p).ke_kamus())

    st.query_params["kode"] = kode
    st.session_state.kode = kode
    st.session_state.buku = b
    st.session_state.p = p
    st.session_state.pesan = []
    st.session_state.bahasa = "id"
    st.session_state.tunggu_pilihan = None


if "buku" not in st.session_state:
    _siapkan_sesi()

buku: Buku = st.session_state.buku
P: B.Parameter = st.session_state.p
buku.pakai(P)          # buku selalu memakai parameter kalibrasi terbaru


def simpan_sekarang(b: Buku = None, p: B.Parameter = None) -> None:
    """Tulis keadaan terkini ke penyimpanan. Dipanggil setiap kali data berubah.

    Kegagalan menyimpan tidak boleh menghentikan aplikasi — pemilik usaha
    lebih baik kehilangan satu simpanan daripada kehilangan seluruh layar.
    """
    try:
        b = b or st.session_state.buku
        p = p or st.session_state.p
        SIMP.simpan(st.session_state.kode, b.pakai(p).ke_kamus())
    except Exception:
        pass


def kirim(sisi, teks, tanda="", aturan=False, basa=None):
    st.session_state.pesan.append(
        {"sisi": sisi, "teks": teks, "tanda": tanda,
         "aturan": aturan, "basa": basa})


def balas(kunci, **slot):
    return L.ambil(st.session_state.bahasa, kunci, **slot)


# ------------------------------------------------------------------- SIDEBAR
LOGO = T.logo_canting()
IKON = T.ikon_canting()
KAIN = T.kain_megamendung()

# HTML motif sudut disiapkan sebagai variabel biasa, BUKAN langsung di dalam
# ekspresi f-string. Python 3.11 (versi yang dipakai untuk deploy, demi
# kecocokan OR-Tools) melarang backslash di dalam kurung kurawal f-string;
# tanda kutip yang di-escape (\") pada style="..." melanggar aturan itu.
AWAN_SUDUT = (f"<div class='awan' style=\"background-image:url('{KAIN}')\">"
             f"</div>") if KAIN else ""

with st.sidebar:
    if LOGO:
        st.markdown(
            f"<img src='{LOGO}' alt='CANTING AI' "
            f"style='width:100%;max-width:200px;display:block;"
            f"margin:-26px auto -2px'>"
            f"<div style='font-size:11.5px;color:{T.ABU};margin-bottom:12px;"
            f"text-align:center'>Prototipe · UKM Silfi Batik Tulis, Ciwaringin</div>",
            unsafe_allow_html=True)
    else:
        st.markdown(
            f"<div style='font-size:22px;font-weight:800;color:{T.BIRU};"
            f"letter-spacing:-.6px'>🪶 CANTING AI</div>"
            f"<div style='font-size:11.5px;color:{T.ABU};margin-bottom:14px'>"
            f"Prototipe · UKM Silfi Batik Tulis, Ciwaringin</div>",
            unsafe_allow_html=True)

    # Kunci API SENGAJA tidak diminta lewat antarmuka.
    # Pemakainya pemilik usaha batik, bukan pengembang — kolom "Kunci API"
    # hanya membingungkan dan membuat produk terbaca sebagai perkakas teknis.
    # Kunci dibaca diam-diam dari Streamlit Secrets bila memang disediakan;
    # kalau tidak ada, mesin aturan yang jalan dan semuanya tetap berfungsi.
    penyedia, kunci_api = E.penyedia_aktif()
    st.session_state.bahasa = st.radio(
        "Bahasa balasan", ["id", "crb"], horizontal=True,
        format_func=lambda k: L.TEMPLAT[k]["nama"],
        help="Bahasa juga terdeteksi otomatis dari kalimat yang Anda tulis.")
    if st.session_state.bahasa == "crb":
        st.caption("Memakai bahasa halus, sebagaimana berbicara kepada orang yang dituakan.")
        if not L.VALIDASI_PENUTUR_ASLI:
            st.warning("Kalimat Cirebon belum diperiksa penutur asli.", icon="⚠️")

    st.markdown(
        T.kartu("Biaya penuh per kain", f"""
        <table style="width:100%;font-size:12px;border-collapse:collapse">
          <tr><td>Bahan</td><td align="right">{B.rupiah(P.bahan)}</td></tr>
          <tr><td>Pewarna + energi</td><td align="right">{B.rupiah(P.pewarna_energi)}</td></tr>
          <tr><td>Tenaga {P.artisan_day_per_kain} hari</td>
              <td align="right">{B.rupiah(P.artisan_day_per_kain*P.upah_per_hari)}</td></tr>
          <tr><td>Biaya lain-lain</td><td align="right">{B.rupiah(P.overhead)}</td></tr>
          <tr style="border-top:1px solid {T.SOGA_MUDA}">
            <td style="padding-top:5px"><b>BIAYA PENUH</b></td>
            <td align="right" style="padding-top:5px">
              <b style="color:{T.BIRU};font-size:15px">{B.rupiah(B.biaya_penuh(p=P))}</b></td></tr>
        </table>
        <div style="font-size:10.5px;color:{T.ABU};margin-top:8px">
          Upah {B.rupiah(P.upah_per_hari)}/hari = {P.persen_umk:.0%} UMK Kab. Cirebon 2025
        </div>""", warna_pil="soga"),
        unsafe_allow_html=True)

    # ------------------------------------------------- KALIBRASI (Tahap 0)
    with st.expander("⚙️  Ubah harga & upah"):
        st.caption("Sesuaikan dengan usaha Anda. Semua angka di aplikasi ikut "
                   "berubah seketika — biaya, untung, harga terendah, sampai "
                   "saran pesanan.")
        bahan = st.number_input("Kain mori per lembar (Rp)", 0, 2_000_000,
                                int(P.bahan), 5_000)
        pewarna = st.number_input("Pewarna + energi per kain (Rp)", 0, 2_000_000,
                                  int(P.pewarna_energi), 5_000)
        overhead = st.number_input("Biaya lain-lain per kain (Rp)", 0, 2_000_000,
                                   int(P.overhead), 1_000)
        upah = st.number_input("Upah perajin per hari (Rp)", 0, 500_000,
                               int(P.upah_per_hari), 1_000,
                               help=f"UMK Kab. Cirebon 2025 = "
                                    f"{B.rupiah(B.UPAH_UMK_HARIAN)}/hari")
        hari = st.number_input("Hari kerja rata-rata per kain", 0.5, 40.0,
                               float(P.artisan_day_per_kain), 0.1)
        kapasitas = st.number_input("Hari kerja tersedia per minggu", 1, 200,
                                    int(P.kapasitas_minggu), 1)

        baru = P.ubah(bahan=bahan, pewarna_energi=pewarna, overhead=overhead,
                      upah_per_hari=upah, artisan_day_per_kain=hari,
                      kapasitas_minggu=kapasitas)
        if baru != P:
            selisih = B.biaya_penuh(p=baru) - B.biaya_penuh(p=P)
            st.info(f"Biaya penuh → **{B.rupiah(B.biaya_penuh(p=baru))}** "
                    f"({'+' if selisih >= 0 else ''}{B.rupiah(selisih)})")
        k1, k2 = st.columns(2)
        if k1.button("Terapkan", use_container_width=True, type="primary"):
            st.session_state.p = baru
            simpan_sekarang(p=baru)
            st.rerun()
        if k2.button("Kembalikan", use_container_width=True):
            st.session_state.p = B.BAKU
            simpan_sekarang(p=B.BAKU)
            st.rerun()

    # ------------------------------------------------- KODE USAHA
    st.markdown(
        T.kartu("Kode usaha", f"""
        <div style="font-size:26px;font-weight:800;color:{T.BIRU};
                    letter-spacing:3px;text-align:center;margin:2px 0 6px">
          {st.session_state.kode}</div>
        <div style="font-size:11px;color:{T.ABU};line-height:1.5">
          Data tersimpan otomatis dan menempel pada kode ini. Tandai halaman ini
          (bookmark) — membukanya kembali memulihkan seluruh catatan, meski
          peramban sudah ditutup.
        </div>""", warna_pil="soga"),
        unsafe_allow_html=True)

    # ------------------------------------------------- CADANGAN DATA
    # Lapis perlindungan paling sederhana, tanpa infrastruktur apa pun.
    # Data tetap tersimpan otomatis di peladen, tetapi berkas cadangan ini
    # memberi pemilik usaha kepemilikan penuh: datanya bisa dibawa pergi,
    # dibuka sendiri, dan dipulihkan di mana saja.
    with st.expander("💾  Cadangkan / pulihkan data"):
        st.caption("Berkas cadangan berformat JSON — bisa dibuka dengan Notepad "
                   "dan diperiksa isinya sendiri.")
        st.download_button(
            "⬇️  Unduh cadangan",
            data=json.dumps(buku.ke_kamus(), ensure_ascii=False, indent=2),
            file_name=f"canting-{date.today().isoformat()}.json",
            mime="application/json",
            use_container_width=True)

        naik = st.file_uploader("Pulihkan dari berkas", type="json",
                                label_visibility="collapsed")
        if naik is not None and st.button("Pulihkan sekarang",
                                          use_container_width=True):
            try:
                b2, p2 = Buku.dari_kamus(json.load(naik))
                st.session_state.buku = b2
                st.session_state.p = p2
                st.session_state.pop("motif_solver", None)
                simpan_sekarang(b2, p2)
                st.success("Data dipulihkan.")
                st.rerun()
            except Exception as e:
                st.error(f"Berkas tidak terbaca: {type(e).__name__}")

    st.write("")
    if T._logo_terpasang() is None:
        st.info("Logo Bank Indonesia belum terpasang. Simpan berkasnya sebagai "
                "**`logo-bi.png`** di folder ini — logo akan muncul sendiri. "
                "Sengaja tidak digambar ulang agar bentuknya tidak meleset.",
                icon="🖼️")

    if st.button("Mulai ulang percakapan", use_container_width=True):
        st.session_state.buku = buku_contoh()
        st.session_state.pesan = []
        st.session_state.tunggu_pilihan = None
        simpan_sekarang(b=st.session_state.buku)
        st.rerun()

# ---------------------------------------------------------------------- HEAD
kol_judul, kol_logo = st.columns([3.4, 1])
with kol_judul:
    st.markdown(T.kepala(
        "Prototipe", "Percakapan · Papan Angka · Cara Kerja",
        'CANTING AI <span class="soga">— Dari Ngobrol Jadi Untung</span>',
        "AI tidak menghitung angkanya. AI membuat angka itu bisa ada."),
        unsafe_allow_html=True)
with kol_logo:
    st.markdown(T.penyelenggara(), unsafe_allow_html=True)

tab_chat, tab_papan, tab_solver, tab_info = st.tabs(
    ["💬  Percakapan", "📊  Papan Angka", "🧮  Pilih Pesanan", "ℹ️  Cara Kerja"])


# ============================================================== TAB PERCAKAPAN
def proses(teks):
    kirim("kanan", teks)
    # Motif yang sudah pernah tercatat ikut dikirim, supaya nama motif baru
    # milik pengguna dikenali tanpa perlu menyentuh kode.
    motif_dikenal = {k.produk for k in buku.kain if k.produk}
    hasil = ekstrak(teks, kunci_api or None, penyedia, motif_dikenal)
    if hasil.get("bahasa") == "crb":
        st.session_state.bahasa = "crb"

    mesin = hasil.get("mesin", "aturan")
    pakai_aturan = mesin == "aturan"
    tanda = f"{hasil['jenis']} · {mesin} · yakin {hasil['keyakinan']:.0%}"

    # Kegagalan LLM tidak disembunyikan — pengguna berhak tahu otak mana yang
    # sedang dipakai, dan kenapa jalur utamanya tidak terpakai.
    if hasil.get("gagal_llm"):
        st.session_state.gagal_llm = hasil["gagal_llm"]

    if hasil.get("pilihan_harga") and len(hasil["pilihan_harga"]) > 1:
        st.session_state.tunggu_pilihan = hasil
        kirim("kiri", balas("beli_ragu",
                            harga=B.rupiah(hasil["pilihan_harga"][0])),
              tanda, pakai_aturan)
        return
    terapkan(hasil, tanda, pakai_aturan)


def jawab_peringkat(tanda, pakai_aturan, basa):
    """Jawab 'motif mana yang paling menguntungkan?' dari data yang ada."""
    peringkat = buku.peringkat_motif()
    if not peringkat:
        kirim("kiri", balas("peringkat_kosong"), tanda, pakai_aturan, basa)
        return

    daftar = "\n".join(
        f"{i}. {nama} — {B.rupiah(upd)}/hari kerja ({n} kain)"
        for i, (nama, upd, n) in enumerate(peringkat, 1))

    atas, bawah = peringkat[0], peringkat[-1]
    if bawah[1] <= 0:
        catatan = (f"Hindari {bawah[0]} — {B.rupiah(bawah[1])} per hari kerja, "
                   f"artinya merugi.")
    elif atas[1] and bawah[1]:
        catatan = (f"Selisihnya {atas[1]/bawah[1]:.1f}× dibanding {bawah[0]}.")
    else:
        catatan = ""
    kirim("kiri", balas("tanya_peringkat", daftar=daftar,
                        teratas=atas[0], catatan=catatan),
          tanda, pakai_aturan, basa)


def terapkan(hasil, tanda, pakai_aturan=True):
    jenis = hasil["jenis"]
    dampak = buku.catat(hasil)
    basa = st.session_state.bahasa
    jumlah_sebelum = len(st.session_state.pesan)

    if jenis == "BELI":
        # Kejadian dikenali tetapi nominalnya memang tidak disebut. Yang benar
        # adalah MENANYAKAN kekurangannya, bukan mengaku tidak paham — sistem
        # yang bilang "tidak mengerti" padahal mengerti itu terlihat bodoh dan
        # membuat pemakainya berhenti percaya.
        if not hasil.get("harga"):
            kirim("kiri", balas("beli_tanpa_harga",
                                item=hasil.get("item") or "Pembelian"),
                  tanda, pakai_aturan, basa)
        else:
            kirim("kiri", balas("beli", item=hasil.get("item") or "barang",
                                qty=hasil.get("qty") or 1,
                                harga=B.rupiah(hasil.get("harga") or 0),
                                total=B.rupiah(dampak.get("nominal", 0))),
                  tanda, pakai_aturan, basa)

    elif jenis == "MULAI":
        kirim("kiri", balas("mulai", produk=hasil.get("produk") or "kain",
                            tanggal=date.today().strftime("%d %b")),
              tanda, pakai_aturan, basa)

    elif jenis == "SELESAI":
        k = dampak.get("kain")
        kirim("kiri", balas("selesai", produk=k.produk if k else "kain",
                            hari=int(k.hari_kerja) if k else "-"),
              tanda, pakai_aturan, basa)

    elif jenis == "JUAL":
        h = dampak.get("hasil")
        if h is None:
            # terjual, tetapi harganya belum disebut — tanyakan, jangan menyerah
            k = dampak.get("kain")
            kirim("kiri", balas("jual_tanpa_harga",
                                produk=(k.produk if k else None)
                                       or hasil.get("produk") or "Kain"),
                  tanda, pakai_aturan, basa)
        elif h and not h["rugi"]:
            kirim("kiri", balas("jual_untung",
                                biaya=B.rupiah(h["biaya_penuh"]),
                                margin=B.rupiah(h["margin"]),
                                per_hari=B.rupiah(h["untung_per_hari"])),
                  tanda, pakai_aturan, basa)
        elif h:
            kirim("kiri", balas("jual_rugi",
                                biaya=B.rupiah(h["biaya_penuh"]),
                                margin=B.rupiah(abs(h["margin"])),
                                kurang=B.rupiah(abs(h["margin"]))),
                  tanda, pakai_aturan, basa)

    elif jenis == "BAYAR":
        kirim("kiri", balas("bayar", kategori=hasil.get("kategori") or "lain",
                            nominal=B.rupiah(dampak.get("nominal", 0))),
              tanda, pakai_aturan, basa)

    elif jenis == "TANYA" and hasil.get("maksud") == "peringkat":
        jawab_peringkat(tanda, pakai_aturan, basa)

    elif jenis == "TANYA" and not hasil.get("harga"):
        kirim("kiri", balas("tanya_umum",
                            biaya=B.rupiah(B.biaya_penuh(p=P)),
                            lantai=B.rupiah(B.lantai_harga(p=P))),
              tanda, pakai_aturan, basa)

    elif jenis == "TANYA":
        tawaran = hasil.get("harga") or 0
        h = B.hitung_margin(tawaran, p=P)
        if h["rugi"]:
            kirim("kiri", balas("tanya_tolak",
                                produk=hasil.get("produk") or "kain",
                                biaya=B.rupiah(h["biaya_penuh"]),
                                tawaran=B.rupiah(tawaran),
                                margin=B.rupiah(abs(h["margin"])),
                                lantai=B.rupiah(B.lantai_harga(p=P))),
                  tanda, pakai_aturan, basa)
        else:
            kirim("kiri", balas("tanya_terima",
                                produk=hasil.get("produk") or "kain",
                                biaya=B.rupiah(h["biaya_penuh"]),
                                tawaran=B.rupiah(tawaran),
                                margin=B.rupiah(h["margin"]),
                                per_hari=B.rupiah(h["untung_per_hari"])),
                  tanda, pakai_aturan, basa)
    else:
        kirim("kiri", balas("tidak_paham"), tanda, pakai_aturan, basa)

    # JARING PENGAMAN — sistem tidak boleh pernah diam.
    # Sebelumnya, kejadian JUAL tanpa nominal membuat seluruh cabang di atas
    # meleset sehingga tidak ada balasan sama sekali. Diam itu lebih buruk
    # daripada mengaku tidak paham: pengguna tidak tahu harus berbuat apa.
    if len(st.session_state.pesan) == jumlah_sebelum:
        kirim("kiri", balas("tidak_paham"), tanda, pakai_aturan, basa)


with tab_chat:
    if st.session_state.get("gagal_llm"):
        st.warning(f"Jalur LLM gagal, sistem beralih ke **mesin aturan** — "
                   f"`{st.session_state.gagal_llm}`", icon="🔁")

    kol_hp, kol_alat = st.columns([1, 1.05])

    with kol_hp:
        gel = []
        if not st.session_state.pesan:
            gel.append(f"<div class='gel kiri'>{L.ambil(st.session_state.bahasa,'sapaan')}"
                       f"<div class='jam'>—</div></div>")
        for p in st.session_state.pesan:
            t = ""
            if p["tanda"]:
                kls = "tanda aturan" if p.get("aturan") else "tanda"
                t = f"<span class='{kls}'>{p['tanda']}</span><br>"
            basa_html = ""
            if p.get("basa") == "crb":
                basa_html = ("<div><span class='pil-basa aktif'>Cerbon · bebasan</span>"
                             "<span class='pil-basa'>Indonesia</span></div>")
            gel.append(f"<div class='gel {p['sisi']}'>{t}{p['teks']}{basa_html}"
                       f"<div class='jam'>{date.today().strftime('%d/%m')}</div></div>")

        # peredam krem ditumpuk sebagai lapisan background di ATAS motif, supaya
        # ikut tergulung bersama isi percakapan
        dinding = (f"background-image:"
                   f"linear-gradient(rgba(236,229,221,.80),rgba(236,229,221,.80)),"
                   f"url('{KAIN}')") if KAIN else ""
        avatar = (f"<div class='wa-avatar'><img src='{IKON}' alt='CANTING'></div>"
                  if IKON else "<div class='wa-avatar emoji'>🪶</div>")
        st.markdown(f"""
        <div class="ponsel"><div class="layar">
          <div class="wa-kepala">
            {avatar}
            <div><div class="wa-nama">CANTING AI</div>
                 <div class="wa-status">online · membalas dalam hitungan detik</div></div>
          </div>
          <div class="wa-isi" style="{dinding}">{''.join(gel)}</div>
        </div></div>""", unsafe_allow_html=True)

        if st.session_state.tunggu_pilihan:
            tunggu = st.session_state.tunggu_pilihan
            st.caption("Pilih nominal yang benar — cukup satu ketukan:")
            kols = st.columns(len(tunggu["pilihan_harga"]) + 1)
            for i, harga in enumerate(tunggu["pilihan_harga"]):
                if kols[i].button(B.rupiah(harga), key=f"pilih{i}",
                                  use_container_width=True, type="primary"):
                    tunggu["harga"] = harga
                    tunggu["pilihan_harga"] = []
                    st.session_state.tunggu_pilihan = None
                    terapkan(tunggu, f"{tunggu['jenis']} · dikonfirmasi · yakin 100%", False)
                    simpan_sekarang()
                    st.rerun()
            if kols[-1].button("Batal", key="pilihbatal", use_container_width=True):
                st.session_state.tunggu_pilihan = None
                st.rerun()

        pesan_baru = st.chat_input("Tulis apa adanya — tak perlu rapi…")
        if pesan_baru:
            proses(pesan_baru)
            simpan_sekarang()
            st.rerun()

    with kol_alat:
        st.markdown(
            f"<div style='font-size:11px;font-weight:700;letter-spacing:1.1px;"
            f"text-transform:uppercase;color:{T.BIRU};margin-bottom:8px'>"
            f"Coba kalimat ini — tekan saja</div>", unsafe_allow_html=True)
        contoh = [
            ("Berantakan & ragu", "td beli kain sm bu ani 5 lembar, 400 apa 450 ya lupa"),
            ("Mulai mengerjakan", "mulai garap megamendung buat bu risa"),
            ("Bahasa Cirebon", "wis dilorod kabeh, siki ngenteni garing"),
            ("Terjual — untung", "laku 1 kain megamendung 850rb"),
            ("Terjual — RUGI", "sogan payu 480rb"),
            ("Menawar sebelum ambil", "ada yang nawar 550rb buat kain sogan, ambil ga?"),
        ]
        for label, teks in contoh:
            if st.button(f"**{label}**  \n{teks}", key=f"c{label}",
                         use_container_width=True):
                proses(teks)
                simpan_sekarang()
                st.rerun()

        st.write("")
        if st.button("📅  Kirim ringkasan mingguan", use_container_width=True,
                     type="primary"):
            d = buku.diagnosa()
            baris = [balas("ringkasan_judul")]
            baris.append("1. " + (balas("kendala_kapasitas")
                                  if d["kendala"] == "kapasitas"
                                  else balas("kendala_permintaan",
                                             kosong=int(d["slot_kosong"]))))
            peringkat = buku.peringkat_motif()
            if len(peringkat) >= 2:
                atas, bawah = peringkat[0], peringkat[-1]
                rasio = (atas[1] / bawah[1]) if bawah[1] > 0 else 0
                baris.append(
                    f"2. Dahulukan {atas[0]} — {B.rupiah(atas[1])}/hari kerja"
                    + (f", {rasio:.1f}× lebih untung daripada {bawah[0]}."
                       if rasio > 0 else
                       f". Hindari {bawah[0]} — {B.rupiah(bawah[1])}/hari."))
            s = buku.statistik()
            baris.append(f"3. {s['jumlah_rugi']} dari {s['jumlah_terjual']} kain "
                         f"terjual di bawah biaya penuh ({s['porsi_rugi']:.0%}). "
                         f"Jangan dijual di bawah {B.rupiah(B.lantai_harga(p=P))}.")
            kirim("kiri", "\n".join(baris), "RINGKASAN MINGGUAN", False,
                  st.session_state.bahasa)
            st.rerun()

# ================================================================= TAB PAPAN
with tab_papan:
    s = buku.statistik()
    d = buku.diagnosa()
    peringkat = buku.peringkat_motif()

    # --- bar pahlawan: dua angka terpenting proposal
    st.markdown(f"""
    <div class="bar-pahlawan">
      <div><div class="n">{B.rupiah(s['untung_per_hari'])}</div>
           <div class="t">untung per hari kerja perajin<br>
           <span style="opacity:.72">ukuran yang tepat, sebab yang terbatas itu tenaga</span></div></div>
      <div class="pisah">▶</div>
      <div><div class="n">{s['porsi_rugi']:.0%}</div>
           <div class="t">kain terjual lebih murah daripada biayanya<br>
           <span style="opacity:.72">{s['jumlah_rugi']} dari {s['jumlah_terjual']} kain</span></div></div>
      {AWAN_SUDUT}
    </div>""", unsafe_allow_html=True)

    a, b, c = st.columns(3)
    a.markdown(T.kartu("Omzet", T.angka(B.rupiah(s["omzet"]), "uang masuk dari kain terjual")),
               unsafe_allow_html=True)
    b.markdown(T.kartu("Laba", T.angka(B.rupiah(s["laba"]), "sisa setelah semua biaya",
                                       "hijau" if s["laba"] >= 0 else "merah")),
               unsafe_allow_html=True)
    c.markdown(T.kartu("Harga terendah",
                       T.angka(B.rupiah(B.lantai_harga(p=P)), "jangan dijual di bawah ini", "soga")),
               unsafe_allow_html=True)

    st.write("")
    kiri, kanan = st.columns([1, 1.1])

    with kiri:
        kapasitas_penuh = d["kendala"] == "kapasitas"
        warna = "merah" if kapasitas_penuh else "soga"
        # Kata "KAPASITAS"/"PERMINTAAN" diganti kalimat yang langsung berarti
        # bagi pemilik usaha. Istilahnya boleh benar secara teori, tetapi kalau
        # harus dijelaskan lebih dulu, ia gagal sebagai antarmuka.
        nama = "WAKTU KERJA PENUH" if kapasitas_penuh else "PESANAN KURANG"
        ket = ("pesanan lebih banyak daripada yang sanggup dikerjakan"
               if kapasitas_penuh
               else f"masih ada {d['slot_kosong']:.0f} hari kerja yang kosong")
        st.markdown(T.kartu("Yang sedang menghambat", f"""
          {T.angka(nama, ket, warna)}
          <div style="margin:14px 0 6px 0;height:9px;background:#eee;border-radius:5px;overflow:hidden">
            <div style="width:{min(d['utilisasi'],1)*100:.0f}%;height:100%;
                        background:{T.BIRU};border-radius:5px"></div></div>
          <div style="font-size:11.5px;color:{T.ABU}">
            Waktu kerja perajin sudah terpakai {d['utilisasi']:.0%} —
            {d['terpakai']:.0f} dari {d['kapasitas']} hari per minggu</div>
          <div style="margin-top:12px;padding:11px 13px;background:{T.BIRU_MUDA};
                      border-radius:9px;font-size:12.5px;color:{T.BIRU_TUA}">
            <b>Sebaiknya:</b> {d['tuas']}</div>
          <div style="font-size:11px;color:{T.ABU};margin-top:9px">
            Penyebabnya dicari <b>lebih dulu</b>, baru sarannya diberikan.
            Kalau yang kurang justru pesanannya, menaikkan harga malah
            membuat pembeli makin sepi.</div>
        """, utama=True), unsafe_allow_html=True)

    with kanan:
        if peringkat:
            baris = []
            tinggi_maks = max(abs(u) for _, u, _ in peringkat) or 1
            for nama_m, upd, n in peringkat:
                w = abs(upd) / tinggi_maks * 100
                c_bar = T.HIJAU if upd >= 0 else T.TERAKOTA
                baris.append(f"""
                <div style="margin-bottom:11px">
                  <div style="display:flex;justify-content:space-between;font-size:12.5px">
                    <span style="font-weight:600">{nama_m}</span>
                    <span style="color:{c_bar};font-weight:700">{B.rupiah(upd)}/hari</span>
                  </div>
                  <div style="height:7px;background:#eee;border-radius:4px;margin-top:3px">
                    <div style="width:{w:.0f}%;height:100%;background:{c_bar};
                                border-radius:4px"></div></div>
                </div>""")
            st.markdown(T.kartu("Motif mana yang paling menguntungkan",
                                "".join(baris) + f"""
              <div style="font-size:11px;color:{T.ABU};margin-top:4px">
                Diurutkan menurut untung per hari kerja, bukan harga jual. Kain
                termahal belum tentu paling menguntungkan kalau lama dikerjakan.</div>"""),
                unsafe_allow_html=True)

    st.write("")
    st.markdown("<div class='kicker' style='margin-top:10px'>Daftar kain</div>"
                "<div style='font-size:12px;color:#6B6B6B;margin-bottom:6px'>"
                "Angka boleh diubah langsung di tabel. Baris baru lewat tanda + "
                "di bawah tabel; hapus baris dengan mencentangnya lalu tekan "
                "tombol hapus.</div>", unsafe_allow_html=True)

    import pandas as pd

    df_kain = pd.DataFrame([{
        "Motif": k.produk,
        "Hari kerja": float(k.hari_kerja),
        "Harga jual": float(k.harga_jual) if k.harga_jual else None,
    } for k in buku.kain])

    edit_kain = st.data_editor(
        df_kain, hide_index=True, use_container_width=True, num_rows="dynamic",
        key="editor_kain",
        column_config={
            "Motif": st.column_config.TextColumn("Motif", required=True),
            "Hari kerja": st.column_config.NumberColumn(
                "Hari kerja", min_value=0.5, max_value=60.0, step=0.5,
                help="Berapa hari kain itu dikerjakan. Dari sinilah untung per "
                     "hari kerja bisa dihitung."),
            "Harga jual": st.column_config.NumberColumn(
                "Harga jual", min_value=0, step=10_000, format="Rp%d",
                help="Kosongkan bila kain belum terjual."),
        })

    t1, t2, t3 = st.columns([1, 1, 2])
    if t1.button("Simpan perubahan", use_container_width=True, type="primary"):
        baru = []
        for _, r in edit_kain.iterrows():
            nama = str(r["Motif"]).strip()
            if not nama:
                continue
            hari = float(r["Hari kerja"] or B.ARTISAN_DAY_PER_KAIN)
            harga = r["Harga jual"]
            harga = float(harga) if pd.notna(harga) and harga else None
            # tanggal disusun ulang agar selisihnya sama dengan hari kerja
            selesai = date.today()
            baru.append(Kain(produk=nama,
                             mulai=selesai - timedelta(days=int(round(hari))),
                             selesai=selesai, harga_jual=harga))
        buku.kain = baru
        st.session_state.pop("motif_solver", None)   # solver ikut memakai data baru
        simpan_sekarang()
        st.rerun()

    if t2.button("Kembalikan data contoh", use_container_width=True):
        st.session_state.buku = buku_contoh().pakai(P)
        st.session_state.pop("motif_solver", None)
        simpan_sekarang(b=st.session_state.buku)
        st.rerun()

    # Penghapusan menyeluruh tidak dapat dibatalkan, sedangkan kode usaha
    # hanyalah pembeda — bukan kunci. Siapa pun yang membuka tautannya bisa
    # menekan tombol ini. Meminta kode diketik ulang bukan pengamanan
    # sungguhan, melainkan penghalang sengaja: cukup untuk mencegah
    # kehilangan karena keliru tekan, tanpa berpura-pura menjadi autentikasi.
    if t3.button("Kosongkan semua data", use_container_width=True):
        st.session_state.minta_hapus = True

    if st.session_state.get("minta_hapus"):
        st.warning(f"Tindakan ini menghapus **seluruh catatan** dan tidak dapat "
                   f"dibatalkan. Ketik kode usaha **{st.session_state.kode}** "
                   f"untuk melanjutkan.", icon="⚠️")
        h1, h2 = st.columns([2, 1])
        ketikan = h1.text_input("Kode usaha", label_visibility="collapsed",
                                placeholder="Ketik kode usaha…")
        if h2.button("Batalkan", use_container_width=True):
            st.session_state.minta_hapus = False
            st.rerun()
        if ketikan.strip().upper() == st.session_state.kode:
            st.session_state.buku = Buku().pakai(P)
            st.session_state.pop("motif_solver", None)
            st.session_state.minta_hapus = False
            simpan_sekarang(b=st.session_state.buku)
            st.rerun()
        elif ketikan.strip():
            st.error("Kode tidak cocok.")

    # kolom turunan ditampilkan terpisah — tidak boleh diketik, karena dihitung
    if buku.kain:
        st.markdown("<div style='font-size:11px;color:#6B6B6B;margin-top:10px'>"
                    "Kolom di bawah dihitung sistem, tidak bisa diketik.</div>",
                    unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([{
            "Motif": k.produk, "Status": k.status,
            "Biaya penuh": B.rupiah(B.biaya_penuh(k.hari_kerja, P)),
            "Untung": B.rupiah(k.hasil(P)["margin"]) if k.hasil(P) else "—",
            "Untung per hari": B.rupiah(k.hasil(P)["untung_per_hari"]) if k.hasil(P) else "—",
        } for k in buku.kain]), hide_index=True, use_container_width=True)

# ================================================================ TAB SOLVER
with tab_solver:
    st.markdown(f"""
    <div class="kicker">Memilih pesanan yang paling menguntungkan</div>
    <div style="font-size:13px;color:{T.ABU};margin-bottom:4px">
      Dengan waktu kerja yang terbatas, motif apa saja yang sebaiknya
      dikerjakan supaya untungnya paling besar?
    </div>""", unsafe_allow_html=True)

    if "motif_solver" not in st.session_state:
        st.session_state.motif_solver = S.motif_dari_buku(buku, P) or [
            S.Motif("megamendung", 875_000, 5.5, 4),
            S.Motif("singabarong", 1_000_000, 9.0, 3),
            S.Motif("wadasan", 620_000, 7.0, 5),
            S.Motif("sogan", 500_000, 4.0, 6),
        ]

    import pandas as pd

    st.markdown("**Data motif** — ubah angkanya langsung di tabel")
    df_in = pd.DataFrame([{
        "Motif": m.nama, "Harga jual": int(m.harga), "Hari kerja": m.hari_kerja,
        "Permintaan maks": m.permintaan, "Komitmen": m.komitmen,
    } for m in st.session_state.motif_solver])

    df_edit = st.data_editor(df_in, hide_index=True, use_container_width=True,
                             num_rows="dynamic", key="editor_motif")

    kapasitas_solver = st.number_input(
        "Hari kerja perajin yang tersedia", 1, 500,
        int(P.kapasitas_minggu), 1,
        help="Inilah yang membatasi. Bukan modal, bukan bahan — tenaga.")

    motif = [S.Motif(str(r["Motif"]), float(r["Harga jual"]),
                     float(r["Hari kerja"]), int(r["Permintaan maks"]),
                     int(r["Komitmen"]))
             for _, r in df_edit.iterrows() if str(r["Motif"]).strip()]

    if not motif:
        st.info("Isi minimal satu motif untuk menjalankan solver.")
    else:
        h = S.optimalkan(motif, kapasitas_solver, P)
        g = h["greedy"]

        st.markdown(f"""
        <div class="bar-pahlawan">
          <div><div class="n">{B.rupiah(h['laba'])}</div>
               <div class="t">untung dari pilihan terbaik<br>
               <span style="opacity:.72">{h['metode']} · {h.get('waktu_ms','-')} ms</span></div></div>
          <div class="pisah">▶</div>
          <div><div class="n">{h['hari_terpakai']:.1f}</div>
               <div class="t">hari kerja terpakai dari {kapasitas_solver}<br>
               <span style="opacity:.72">sisa {kapasitas_solver-h['hari_terpakai']:.1f} hari</span></div></div>
          {AWAN_SUDUT}
        </div>""", unsafe_allow_html=True)

        kiri_s, kanan_s = st.columns([1.15, 1])
        with kiri_s:
            baris = []
            for m in motif:
                n = h["pilihan"][m.nama]
                warna = T.HIJAU if m.untung_per_hari(P) >= 0 else T.TERAKOTA
                baris.append(f"""
                <div style="display:flex;justify-content:space-between;
                            padding:7px 0;border-bottom:1px solid #eee;font-size:13px">
                  <span><b>{m.nama}</b>
                    <span style="color:{T.ABU};font-size:11.5px">
                      · {m.hari_kerja} hari · {B.rupiah(m.margin(P))}/kain</span></span>
                  <span style="text-align:right">
                    <b style="color:{T.BIRU};font-size:15px">{n} kain</b><br>
                    <span style="color:{warna};font-size:11px">
                      {B.rupiah(m.untung_per_hari(P))}/hari</span></span>
                </div>""")
            st.markdown(T.kartu("Yang sebaiknya dikerjakan", "".join(baris),
                                utama=True), unsafe_allow_html=True)

        with kanan_s:
            lp = h.get("lp")
            baris_b = []
            for nama, data, cat in [
                ("Batas tertinggi yang mungkin", lp, "kain boleh dihitung sebagian"),
                ("Pilihan yang dipakai", h, "kain dihitung utuh"),
                ("Cara sederhana, sebagai pembanding", g, "urut dari untung per hari"),
            ]:
                if not data:
                    continue
                tebal = "700" if nama.startswith("ILP") else "400"
                warna = T.BIRU if nama.startswith("ILP") else T.ABU
                baris_b.append(f"""
                <div style="display:flex;justify-content:space-between;
                            padding:7px 0;border-bottom:1px solid #eee;font-size:12.5px">
                  <span style="font-weight:{tebal}">{nama}
                    <span style="color:{T.ABU};font-size:10.5px">· {cat}</span></span>
                  <span style="font-weight:{tebal};color:{warna}">
                    {B.rupiah(data['laba'])}
                    <span style="color:{T.ABU};font-weight:400">
                      · {data['hari_terpakai']:.1f} hari</span></span>
                </div>""")

            catatan = ""
            if h.get("ongkos_kebulatan") is not None and h["ongkos_kebulatan"] > 0:
                nganggur = lp["hari_terpakai"] - h["hari_terpakai"]
                catatan = (
                    f"<div style='margin-top:12px;padding:11px 13px;"
                    f"background:{T.BIRU_MUDA};border-radius:9px;font-size:12px;"
                    f"color:{T.BIRU_TUA}'>"
                    f"<b>Selisih {B.rupiah(h['ongkos_kebulatan'])}</b> "
                    f"({h['senjang_pct']:.1f}% dari batas tertinggi).<br>"
                    f"Secara hitungan bisa memakai {lp['hari_terpakai']:.1f} hari, nyatanya hanya "
                    f"{h['hari_terpakai']:.1f} — <b>{nganggur:.1f} hari kerja "
                    f"menganggur semata-mata karena kain tidak bisa dikerjakan "
                    f"sebagian.</b> Di situlah sisa kapasitas layak dicarikan "
                    f"pekerjaan tambahan.</div>")
            elif h.get("ongkos_kebulatan") == 0:
                catatan = (f"<div style='margin-top:12px;font-size:12px;color:{T.ABU}'>"
                           f"Pilihan ini sudah menyentuh batas tertinggi — terbukti "
                           f"paling menguntungkan, bukan sekadar yang kebetulan ditemukan.</div>")

            selisih_g = h["selisih"]
            catatan += (
                f"<div style='margin-top:10px;font-size:11.5px;color:{T.ABU}'>"
                + (f"Cara ini unggul {B.rupiah(selisih_g)} dibanding cara sederhana."
                   if selisih_g > 0 else
                   "Pada jumlah sekecil ini, cara sederhana sudah menyamai hasil terbaik — "
                   "sesuai catatan pada batas yang jujur. Perhitungan penuh baru terasa "
                   "gunanya begitu motif dan pesanannya bertambah banyak.")
                + "</div>")

            st.markdown(T.kartu("Perbandingan cara menghitung",
                                "".join(baris_b) + catatan), unsafe_allow_html=True)

        with st.expander("Rumusan matematisnya"):
            st.markdown(f"""
**Peubah keputusan** $x_i$ = jumlah kain motif $i$ (bulat, $\\ge 0$)

**Fungsi tujuan**

$$\\max \\; \\sum_i (\\text{{harga}}_i - \\text{{biaya penuh}}_i)\\, x_i$$

**Kendala kapasitas** — hari kerja perajin, satu-satunya sumber daya langka

$$\\sum_i \\text{{hari}}_i \\, x_i \\;\\le\\; {kapasitas_solver}$$

**Kendala permintaan**

$$\\text{{komitmen}}_i \\;\\le\\; x_i \\;\\le\\; \\text{{permintaan}}_i$$

---

**LP dan ILP — rumusan sama, satu syarat berbeda**

| | Peubah $x_i$ | Solver | Gunanya |
|---|---|---|---|
| **LP** | pecahan, $x_i \\in \\mathbb{{R}}_{{\\ge 0}}$ | GLOP | batas atas yang terbukti |
| **ILP** | bulat, $x_i \\in \\mathbb{{Z}}_{{\\ge 0}}$ | SCIP | jawaban yang dipakai |

LP selalu bernilai lebih baik atau sama dengan ILP, karena himpunan solusinya
lebih longgar. Karena itu **hasil LP menjadi batas atas ILP** — kalau ILP
menyentuh batas itu, kita tahu pasti tidak ada pilihan lain yang lebih baik.
Selisih keduanya adalah **ongkos kebulatan**: kerugian yang timbul justru
karena kain tidak bisa dikerjakan setengah.

Biaya penuh tiap motif memakai parameter kalibrasi yang sedang berlaku —
upah {B.rupiah(P.upah_per_hari)}/hari, bahan {B.rupiah(P.bahan)}.
Ubah di sidebar, hasil solver ikut berubah.
""")

# ================================================================== TAB INFO
with tab_info:
    k1, k2 = st.columns([1.15, 1])
    with k1:
        st.markdown(T.kartu("Cara memakainya", f"""
        <table style="width:100%;font-size:12.5px;border-collapse:collapse">
          <tr><td style="padding:6px 0;width:128px"><b>Sekali di awal</b></td>
              <td>Enam pertanyaan tentang harga bahan dan upah. Setelah itu
                  biaya per kain langsung ketahuan</td></tr>
          <tr><td style="padding:6px 0"><b>Setiap hari</b></td>
              <td>Cukup kirim pesan seperti biasa. Tidak ada formulir,
                  tidak ada menu yang harus dipelajari</td></tr>
          <tr><td style="padding:6px 0"><b>Setiap kain</b></td>
              <td>Dari kabar "mulai" dan "selesai", lamanya pengerjaan
                  terhitung sendiri. Begitu laku, untungnya langsung muncul</td></tr>
          <tr><td style="padding:6px 0"><b>Setiap minggu</b></td>
              <td>Dicari dulu apa yang sedang menghambat, baru diberi
                  tiga saran</td></tr>
          <tr><td style="padding:6px 0"><b>Kapan saja</b></td>
              <td>Bertanya sebelum memutuskan:
                  <i>"ada nawar 550rb, ambil ga?"</i></td></tr>
        </table>"""), unsafe_allow_html=True)

        st.markdown(T.kartu("Apa yang terjadi di balik layar", f"""
        <div style="font-size:12.5px;line-height:1.9;color:{T.BIRU_TUA}">
          pesan dibaca → <b>ditangkap maksudnya</b> → kalau ragu,
          <b>ditanyakan dulu</b> → dicatat → <b>biayanya dihitung</b> →
          <b>dicari apa yang menghambat</b> → dijawab
        </div>
        <div style="font-size:12px;color:{T.ABU};margin-top:10px">
          Bagian "kalau ragu, ditanyakan dulu" itu disengaja. Pembacaan otomatis
          pasti sesekali meleset; jalan keluarnya bukan mengejar ketepatan
          sempurna, melainkan membuat pembetulannya cukup satu ketukan. Kalau
          pemiliknya harus mengetik ulang, ia berhenti memakai dalam sepekan.
        </div>""", warna_pil="soga"),
            unsafe_allow_html=True)

    with k2:
        st.markdown(T.kartu("Angka rujukan", f"""
        <table style="width:100%;font-size:12.5px;border-collapse:collapse">
          <tr><td style="padding:5px 0">Upah perajin</td>
              <td align="right"><b>{B.rupiah(P.upah_per_hari)}</b>/hari</td></tr>
          <tr><td style="padding:5px 0">Biaya penuh per kain</td>
              <td align="right"><b style="color:{T.BIRU}">{B.rupiah(B.biaya_penuh(p=P))}</b></td></tr>
          <tr><td style="padding:5px 0">Untung bila dijual Rp675.000</td>
              <td align="right"><b>{B.rupiah(P.harga_rata-B.biaya_penuh(p=P))}</b> (15%)</td></tr>
          <tr><td style="padding:5px 0">Untung per hari kerja</td>
              <td align="right"><b style="color:{T.BIRU}">Rp19.346</b></td></tr>
          <tr style="border-top:1px solid {T.SOGA_MUDA}">
              <td style="padding:7px 0">Harga agar tidak rugi, bila perajin
                  dibayar penuh sesuai upah minimum</td>
              <td align="right"><b style="color:{T.TERAKOTA}">
                  {B.rupiah(B.titik_impas_upah_formal(P))}</b></td></tr>
        </table>
        <div style="font-size:11px;color:{T.ABU};margin-top:8px">
          Upah dihitung dari UMK Kab. Cirebon 2025
          ({B.rupiah(B.UMK_KAB_CIREBON_2025)}/bulan ÷ 26 hari × 0,65).
          Agar tidak rugi, harganya perlu <b>13% lebih tinggi</b> daripada
          rata-rata sekarang.</div>"""),
            unsafe_allow_html=True)

        st.markdown(T.kartu("Batas yang jujur", f"""
        <div style="font-size:12px;line-height:1.7;color:{T.TINTA}">
          • Riwayat awal adalah <b>data contoh</b>, bukan pembukuan Silfi.<br>
          • Data tersimpan otomatis dan bertahan melewati penyegaran halaman,
            tetapi penyimpanan peladen ini bersifat <b>sementara</b> — data
            terhapus bila aplikasi disebarkan ulang. Karena itu tombol
            <b>unduh cadangan</b> disediakan. Versi produksi memerlukan basis
            data permanen.<br>
          • <b>Kode usaha hanya pembeda, bukan kunci.</b> Siapa pun yang
            mengetahui kodenya dapat membuka buku itu. Memisahkan data antar
            UMKM sudah cukup untuk prototipe; produksi tetap membutuhkan
            proses masuk yang sebenarnya.<br>
          • Pembacaan pesan punya dua cara: memakai AI bila tersedia, dan cara
            sederhana bila tidak. Pemilik usaha tidak pernah diminta mengatur
            apa pun — pergantiannya otomatis, dan aplikasinya tidak pernah
            berhenti bekerja.<br>
          
          • Masukan suara belum tersedia.<br>
          • Kalimat bahasa Cirebon <b>belum diperiksa penutur asli</b>.
        </div>"""), unsafe_allow_html=True)

# ------------------------------------------------------------------ PENUTUP
st.markdown(
    f"<div style='margin-top:26px;padding-top:14px;border-top:1px solid #eee;"
    f"font-size:11px;color:{T.ABU};display:flex;justify-content:space-between'>"
    f"<span>Seluruh angka bersumber dari <code>model_finansial_canting.py</code></span>"
    f"<span style='color:{T.SOGA}'>Satu canting menuliskan pola di kain. "
    f"Satu canting lagi menuliskan pola di angka.</span></div>",
    unsafe_allow_html=True)
