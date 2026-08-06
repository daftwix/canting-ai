# -*- coding: utf-8 -*-
"""
CANTING AI — prototipe
ImpactPreneur Business Challenge · Bank Indonesia KPw Cirebon
Studi kasus: UKM Silfi Batik Tulis, Desa Ciwaringin, Kabupaten Cirebon

Jalankan:  streamlit run app.py
"""
from datetime import date, timedelta

import streamlit as st

import bahasa as L
import biaya as B
import ekstraksi as E
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
if "buku" not in st.session_state:
    st.session_state.buku = buku_contoh()
    st.session_state.pesan = []
    st.session_state.bahasa = "id"
    st.session_state.tunggu_pilihan = None
    st.session_state.p = B.BAKU          # parameter biaya yang sedang berlaku

buku: Buku = st.session_state.buku
P: B.Parameter = st.session_state.p
buku.pakai(P)          # buku selalu memakai parameter kalibrasi terbaru


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
        st.caption("Ragam **bebasan** — ragam halus untuk yang dituakan.")
        if not L.VALIDASI_PENUTUR_ASLI:
            st.warning("Kalimat Cirebon belum divalidasi penutur asli.", icon="⚠️")

    st.markdown(
        T.kartu("Biaya penuh per kain", f"""
        <table style="width:100%;font-size:12px;border-collapse:collapse">
          <tr><td>Bahan</td><td align="right">{B.rupiah(P.bahan)}</td></tr>
          <tr><td>Pewarna + energi</td><td align="right">{B.rupiah(P.pewarna_energi)}</td></tr>
          <tr><td>Tenaga {P.artisan_day_per_kain} hari</td>
              <td align="right">{B.rupiah(P.artisan_day_per_kain*P.upah_per_hari)}</td></tr>
          <tr><td>Overhead</td><td align="right">{B.rupiah(P.overhead)}</td></tr>
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
        st.caption("Tahap 0 · Kalibrasi. Semua angka di aplikasi ikut berubah "
                   "seketika — biaya penuh, margin, lantai harga, diagnosa, "
                   "sampai hasil solver.")
        bahan = st.number_input("Kain mori per lembar (Rp)", 0, 2_000_000,
                                int(P.bahan), 5_000)
        pewarna = st.number_input("Pewarna + energi per kain (Rp)", 0, 2_000_000,
                                  int(P.pewarna_energi), 5_000)
        overhead = st.number_input("Overhead per kain (Rp)", 0, 2_000_000,
                                   int(P.overhead), 1_000)
        upah = st.number_input("Upah perajin per hari (Rp)", 0, 500_000,
                               int(P.upah_per_hari), 1_000,
                               help=f"UMK Kab. Cirebon 2025 = "
                                    f"{B.rupiah(B.UPAH_UMK_HARIAN)}/hari")
        hari = st.number_input("Hari kerja rata-rata per kain", 0.5, 40.0,
                               float(P.artisan_day_per_kain), 0.1)
        kapasitas = st.number_input("Kapasitas artisan-day per minggu", 1, 200,
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
            st.rerun()
        if k2.button("Kembalikan", use_container_width=True):
            st.session_state.p = B.BAKU
            st.rerun()

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
    ["💬  Percakapan", "📊  Papan Angka", "🧮  Solver Bauran", "ℹ️  Cara Kerja"])


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
                    st.rerun()
            if kols[-1].button("Batal", key="pilihbatal", use_container_width=True):
                st.session_state.tunggu_pilihan = None
                st.rerun()

        pesan_baru = st.chat_input("Tulis apa adanya — tak perlu rapi…")
        if pesan_baru:
            proses(pesan_baru)
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
                         f"Lantai harga {B.rupiah(B.lantai_harga(p=P))}.")
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
           <span style="opacity:.72">satuan yang benar untuk usaha yang dibatasi tenaga</span></div></div>
      <div class="pisah">▶</div>
      <div><div class="n">{s['porsi_rugi']:.0%}</div>
           <div class="t">order terjual di bawah biaya penuh<br>
           <span style="opacity:.72">{s['jumlah_rugi']} dari {s['jumlah_terjual']} kain</span></div></div>
      {AWAN_SUDUT}
    </div>""", unsafe_allow_html=True)

    a, b, c = st.columns(3)
    a.markdown(T.kartu("Omzet", T.angka(B.rupiah(s["omzet"]), "seluruh kain terjual")),
               unsafe_allow_html=True)
    b.markdown(T.kartu("Laba", T.angka(B.rupiah(s["laba"]), "setelah biaya penuh",
                                       "hijau" if s["laba"] >= 0 else "merah")),
               unsafe_allow_html=True)
    c.markdown(T.kartu("Lantai harga",
                       T.angka(B.rupiah(B.lantai_harga(p=P)), "titik impas per kain", "soga")),
               unsafe_allow_html=True)

    st.write("")
    kiri, kanan = st.columns([1, 1.1])

    with kiri:
        warna = "merah" if d["kendala"] == "kapasitas" else "soga"
        nama = "KAPASITAS" if d["kendala"] == "kapasitas" else "PERMINTAAN"
        ket = ("slot produksi penuh" if d["kendala"] == "kapasitas"
               else f"slot kosong {d['slot_kosong']:.0f} artisan-day")
        st.markdown(T.kartu("Diagnosa kendala", f"""
          {T.angka(nama, ket, warna)}
          <div style="margin:14px 0 6px 0;height:9px;background:#eee;border-radius:5px;overflow:hidden">
            <div style="width:{min(d['utilisasi'],1)*100:.0f}%;height:100%;
                        background:{T.BIRU};border-radius:5px"></div></div>
          <div style="font-size:11.5px;color:{T.ABU}">
            Pemakaian kapasitas {d['utilisasi']:.0%} —
            {d['terpakai']:.0f} dari {d['kapasitas']} artisan-day/minggu</div>
          <div style="margin-top:12px;padding:11px 13px;background:{T.BIRU_MUDA};
                      border-radius:9px;font-size:12.5px;color:{T.BIRU_TUA}">
            <b>Tuas:</b> {d['tuas']}</div>
          <div style="font-size:11px;color:{T.ABU};margin-top:9px">
            Diagnosa dijalankan <b>sebelum</b> memilih tuas. Kalau slot kosong,
            menaikkan harga justru mematikan permintaan.</div>
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
            st.markdown(T.kartu("Peringkat motif — untung per hari kerja",
                                "".join(baris) + f"""
              <div style="font-size:11px;color:{T.ABU};margin-top:4px">
                Diurutkan bukan menurut harga jual. Kain termahal belum tentu
                paling menguntungkan bila pengerjaannya lama.</div>"""),
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
                help="Selisih tanggal mulai dan selesai. Inilah yang membuat "
                     "untung per hari kerja bisa dihitung."),
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
        st.rerun()

    if t2.button("Kembalikan data contoh", use_container_width=True):
        st.session_state.buku = buku_contoh().pakai(P)
        st.session_state.pop("motif_solver", None)
        st.rerun()

    if t3.button("Kosongkan semua data", use_container_width=True):
        st.session_state.buku = Buku().pakai(P)
        st.session_state.pop("motif_solver", None)
        st.rerun()

    # kolom turunan ditampilkan terpisah — tidak boleh diketik, karena dihitung
    if buku.kain:
        st.markdown("<div style='font-size:11px;color:#6B6B6B;margin-top:10px'>"
                    "Kolom di bawah dihitung sistem, tidak bisa diketik.</div>",
                    unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([{
            "Motif": k.produk, "Status": k.status,
            "Biaya penuh": B.rupiah(B.biaya_penuh(k.hari_kerja, P)),
            "Margin": B.rupiah(k.hasil(P)["margin"]) if k.hasil(P) else "—",
            "Untung/hari": B.rupiah(k.hasil(P)["untung_per_hari"]) if k.hasil(P) else "—",
        } for k in buku.kain]), hide_index=True, use_container_width=True)

# ================================================================ TAB SOLVER
with tab_solver:
    st.markdown(f"""
    <div class="kicker">Optimisasi bauran produk · Integer Linear Programming</div>
    <div style="font-size:13px;color:{T.ABU};margin-bottom:4px">
      Dalam kapasitas terbatas, motif apa saja yang sebaiknya dikerjakan supaya
      total labanya paling besar? Bulat, bukan pecahan — kain tidak bisa
      dikerjakan setengah.
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
        "Kapasitas artisan-day pada periode ini", 1, 500,
        int(P.kapasitas_minggu), 1,
        help="Sumber daya yang langka. Ini satu-satunya kendala yang mengikat.")

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
               <div class="t">laba bauran optimal<br>
               <span style="opacity:.72">{h['metode']} · {h.get('waktu_ms','-')} ms</span></div></div>
          <div class="pisah">▶</div>
          <div><div class="n">{h['hari_terpakai']:.1f}</div>
               <div class="t">artisan-day terpakai dari {kapasitas_solver}<br>
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
            st.markdown(T.kartu("Bauran yang disarankan", "".join(baris),
                                utama=True), unsafe_allow_html=True)

        with kanan_s:
            lp = h.get("lp")
            baris_b = []
            for nama, data, cat in [
                ("LP — batas atas", lp, "peubah boleh pecahan"),
                ("ILP — dipakai", h, "peubah bulat"),
                ("Greedy — pembanding", g, "urut untung/hari"),
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
                    f"<b>Ongkos kebulatan {B.rupiah(h['ongkos_kebulatan'])}</b> "
                    f"({h['senjang_pct']:.1f}% dari batas atas LP).<br>"
                    f"LP sanggup memakai {lp['hari_terpakai']:.1f} hari, ILP hanya "
                    f"{h['hari_terpakai']:.1f} — <b>{nganggur:.1f} hari kerja "
                    f"menganggur semata-mata karena kain tidak bisa dikerjakan "
                    f"sebagian.</b> Di situlah sisa kapasitas layak dicarikan "
                    f"pekerjaan tambahan.</div>")
            elif h.get("ongkos_kebulatan") == 0:
                catatan = (f"<div style='margin-top:12px;font-size:12px;color:{T.ABU}'>"
                           f"ILP menyentuh batas atas LP — bauran ini terbukti "
                           f"optimum, bukan sekadar yang terbaik yang ditemukan.</div>")

            selisih_g = h["selisih"]
            catatan += (
                f"<div style='margin-top:10px;font-size:11.5px;color:{T.ABU}'>"
                + (f"Solver unggul {B.rupiah(selisih_g)} atas heuristik greedy."
                   if selisih_g > 0 else
                   "Pada skala ini greedy sudah menyamai optimum — sesuai catatan "
                   "pada batas yang jujur. Solver tetap diperlukan begitu motif, "
                   "batas permintaan, dan komitmen bertambah.")
                + "</div>")

            st.markdown(T.kartu("LP · ILP · Greedy",
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
menyentuh batas itu, kita tahu pasti tidak ada bauran lain yang lebih baik.
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
        st.markdown(T.kartu("Alur kerja", f"""
        <table style="width:100%;font-size:12.5px;border-collapse:collapse">
          <tr><td style="padding:6px 0;width:118px"><b>0 · Kalibrasi</b></td>
              <td>Enam pertanyaan sekali di awal → biaya penuh langsung terhitung</td></tr>
          <tr><td style="padding:6px 0"><b>1 · Harian</b></td>
              <td>Pemilik mengirim chat apa adanya. Tanpa formulir, tanpa menu</td></tr>
          <tr><td style="padding:6px 0"><b>2 · Per kain</b></td>
              <td><code>MULAI</code>+<code>SELESAI</code> → <b>hari kerja</b>;
                  <code>JUAL</code> → margin & untung per hari</td></tr>
          <tr><td style="padding:6px 0"><b>3 · Mingguan</b></td>
              <td>Diagnosa kendala, lalu tiga kalimat saran</td></tr>
          <tr><td style="padding:6px 0"><b>4 · Sewaktu-waktu</b></td>
              <td>Bertanya sebelum memutuskan: <i>"ada nawar 550rb, ambil ga?"</i></td></tr>
        </table>"""), unsafe_allow_html=True)

        st.markdown(T.kartu("Pipeline satu pesan", f"""
        <div style="font-size:12.5px;line-height:2;color:{T.BIRU_TUA}">
          transkripsi → <b>ekstraksi LLM</b> → keyakinan rendah?
          <b>konfirmasi satu ketuk</b> → jurnal → <b>mesin biaya ABC</b> →
          <b>diagnosa kendala</b> → balasan
        </div>
        <div style="font-size:12px;color:{T.ABU};margin-top:10px">
          Konfirmasi satu ketuk itu disengaja. Ekstraksi AI pasti sesekali salah;
          jalan keluarnya bukan mengejar model sempurna, melainkan membuat
          koreksinya semurah satu ketukan. Kalau pemilik harus mengetik ulang,
          ia berhenti memakai dalam sepekan.</div>""", warna_pil="soga"),
            unsafe_allow_html=True)

    with k2:
        st.markdown(T.kartu("Angka rujukan", f"""
        <table style="width:100%;font-size:12.5px;border-collapse:collapse">
          <tr><td style="padding:5px 0">Upah perajin</td>
              <td align="right"><b>{B.rupiah(P.upah_per_hari)}</b>/hari</td></tr>
          <tr><td style="padding:5px 0">Biaya penuh per kain</td>
              <td align="right"><b style="color:{T.BIRU}">{B.rupiah(B.biaya_penuh(p=P))}</b></td></tr>
          <tr><td style="padding:5px 0">Margin pada Rp675.000</td>
              <td align="right"><b>{B.rupiah(P.harga_rata-B.biaya_penuh(p=P))}</b> (15%)</td></tr>
          <tr><td style="padding:5px 0">Untung per hari kerja</td>
              <td align="right"><b style="color:{T.BIRU}">Rp19.346</b></td></tr>
          <tr style="border-top:1px solid {T.SOGA_MUDA}">
              <td style="padding:7px 0">Impas pada upah formal penuh</td>
              <td align="right"><b style="color:{T.TERAKOTA}">
                  {B.rupiah(B.titik_impas_upah_formal(P))}</b></td></tr>
        </table>
        <div style="font-size:11px;color:{T.ABU};margin-top:8px">
          Upah diancarkan ke UMK Kab. Cirebon 2025
          ({B.rupiah(B.UMK_KAB_CIREBON_2025)}/bulan ÷ 26 hari × 0,65).
          Impas menuntut harga <b>13% di atas</b> rata-rata saat ini.</div>"""),
            unsafe_allow_html=True)

        st.markdown(T.kartu("Batas yang jujur", f"""
        <div style="font-size:12px;line-height:1.7;color:{T.TINTA}">
          • Riwayat awal adalah <b>data contoh</b>, bukan pembukuan Silfi.<br>
          • Ekstraksi punya dua jalur: <b>LLM</b> bila kredensialnya tersedia
            pada peladen, dan <b>mesin aturan</b> bila tidak. Pemilik usaha
            tidak pernah diminta mengatur apa pun — pergantiannya otomatis,
            dan sistem tidak pernah mati saat didemokan.<br>
          • Solver LP/ILP belum dipasang; pengurutan menurut untung per hari
            memberi hasil sama untuk kasus sekecil ini.<br>
          • Masukan suara belum tersedia.<br>
          • Kalimat bahasa Cirebon <b>belum divalidasi penutur asli</b>.
        </div>"""), unsafe_allow_html=True)

# ------------------------------------------------------------------ PENUTUP
st.markdown(
    f"<div style='margin-top:26px;padding-top:14px;border-top:1px solid #eee;"
    f"font-size:11px;color:{T.ABU};display:flex;justify-content:space-between'>"
    f"<span>Seluruh angka bersumber dari <code>model_finansial_canting.py</code></span>"
    f"<span style='color:{T.SOGA}'>Satu canting menuliskan pola di kain. "
    f"Satu canting lagi menuliskan pola di angka.</span></div>",
    unsafe_allow_html=True)
