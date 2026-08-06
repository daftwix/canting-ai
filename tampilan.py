# -*- coding: utf-8 -*-
"""
Lapis tampilan CANTING AI — disamakan dengan deck proposal.

Palet, tipografi, kartu berpil, bar pahlawan, dan motif megamendung mengikuti
aturan yang sama persis dengan PROMPT-GENERATE-SLIDE.md, supaya prototipe dan
dokumen terbaca sebagai satu karya.
"""

BIRU = "#0B4EA2"        # biru Bank Indonesia
BIRU_TUA = "#05295C"
BIRU_MUDA = "#E8F0FA"
SOGA = "#C68B3C"        # soga — pewarna cokelat batik
SOGA_MUDA = "#E8C88F"
KREM = "#FDF8F0"
TERAKOTA = "#B4472E"
HIJAU = "#2F6B4F"
TINTA = "#1A1A1A"
ABU = "#6B6B6B"


def megamendung(lebar=460, tinggi=300, warna=BIRU, opacity=0.06, lapis=6):
    """Motif awan bertingkat khas Cirebon, digambar sebagai SVG.

    Bentuknya: rangkaian LENGKUNG CEMBUNG yang membesar ke kanan, ditumpuk
    berlapis dengan jarak tetap — stilisasi gulungan awan megamendung.

    Catatan revisi: versi pertama memakai tangga berundak. Bentuk itu masih
    terbaca sebagai awan pada ukuran kecil, tetapi begitu diperbesar menjadi
    latar halaman ia hanya terbaca sebagai pita diagonal tebal — mirip noda.
    Lengkung cembung jauh lebih menyerupai motif aslinya di segala ukuran.
    """
    jalur = []
    for i in range(lapis):
        geser = i * 27
        tebal = 10 - i * 0.85
        alpha = 1 - i * 0.12
        y = 292 - geser
        # tiga lobus awan yang makin membesar ke kanan
        d = (f"M-10,{y} "
             f"a 46,46 0 0 1 92,0 "
             f"a 62,62 0 0 1 124,0 "
             f"a 78,78 0 0 1 156,0")
        jalur.append(
            f'<path d="{d}" fill="none" stroke="{warna}" '
            f'stroke-width="{tebal:.1f}" stroke-linecap="round" '
            f'stroke-opacity="{alpha:.2f}"/>'
        )
    return (
        f'<svg width="{lebar}" height="{tinggi}" viewBox="0 0 400 300" '
        f'xmlns="http://www.w3.org/2000/svg" style="opacity:{opacity}">'
        + "".join(jalur) + "</svg>"
    )


def _megamendung_uri(warna=BIRU, opacity=0.07, lapis=7):
    """Motif sebagai data URI, untuk dipakai sebagai background CSS.

    Dipasang lewat background — BUKAN div melayang — supaya dijamin berada di
    belakang seluruh konten. Versi div sebelumnya menembus ke sidebar karena
    z-index-nya kalah oleh tumpukan Streamlit.
    """
    import base64

    svg = megamendung(760, 520, warna, opacity, lapis)
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


LATAR_URI = _megamendung_uri()


CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, .stApp, .stMarkdown, .stButton button, .stTabs,
section[data-testid="stSidebar"], input, textarea, label {{
  font-family:'Plus Jakarta Sans', 'Inter', -apple-system, 'Segoe UI', sans-serif;
}}

/* JANGAN pernah menimpa font ikon.
   Ikon Streamlit memakai LIGATUR: teks "visibility" diubah menjadi gambar mata
   oleh font Material Symbols. Kalau fontnya tertimpa, ligaturnya batal dan kata
   mentahnya muncul di layar. Aturan ini mengembalikannya. */
span[class*="material"], i[class*="material"], [data-testid*="Icon"],
.material-symbols-rounded, .material-symbols-outlined, .material-icons,
[data-baseweb] span[aria-hidden="true"] {{
  font-family:'Material Symbols Rounded','Material Symbols Outlined',
              'Material Icons' !important;
}}

/* ------------------------------------------------- MEGAMENDUNG LATAR HALAMAN
   Dipasang sebagai background, bukan elemen — jadi mustahil menimpa konten.
   Hanya satu gugus di kanan bawah; gugus kedua di sisi kiri sengaja dibuang
   karena menembus sidebar dan terbaca sebagai noda. */
.stApp {{
  background-color:#FFFFFF;
  background-image:url("{LATAR_URI}");
  background-repeat:no-repeat;
  background-position:right -90px bottom -120px;
  background-attachment:fixed;
  background-size:760px 520px;
}}
/* JANGAN sembunyikan seluruh header — tombol untuk membuka kembali sidebar
   yang tertutup berada di dalamnya. Menyembunyikannya membuat sidebar yang
   sudah diminimalkan tidak bisa dibuka lagi sama sekali. Yang disembunyikan
   hanya menu dan toolbar bawaan Streamlit. */
#MainMenu, footer {{ visibility:hidden; }}
/* Header dibuat transparan saja — TINGGINYA JANGAN dinolkan. Menyetel
   height:0 membuat tombol buka-sidebar di dalamnya berukuran 0x0: terlihat
   menurut CSS, tetapi mustahil diklik. */
header[data-testid="stHeader"] {{ background:transparent; }}
[data-testid="stDecoration"] {{ display:none; }}

/* JANGAN sembunyikan stToolbar — TOMBOL BUKA SIDEBAR ADA DI DALAMNYA.
   Menyetel display:none pada toolbar membuat tombol itu berukuran 0x0,
   sehingga sidebar yang sudah ditutup TIDAK BISA dibuka lagi selamanya.
   Yang perlu disembunyikan hanya menu titik-tiga dan tombol Deploy;
   toolbarnya sendiri harus tetap hidup. */
[data-testid="stToolbar"] {{ display:flex !important; }}
[data-testid="stToolbarActions"],
[data-testid="stAppDeployButton"],
[data-testid="stMainMenu"] {{ display:none !important; }}
[data-testid="stExpandSidebarButton"] {{
  display:flex !important; width:auto !important; height:auto !important;
  min-width:34px; min-height:34px; opacity:1 !important; visibility:visible !important;
}}

/* Tombol tutup-sidebar sengaja DIMATIKAN — ini keputusan sadar, bukan kelalaian.
   Streamlit menutup sidebar dengan translateX(-300px), dan tombolnya sendiri
   berada DI DALAM sidebar sehingga ikut terdorong keluar layar. Atribut
   aria-expanded pun tetap bernilai "true" saat tertutup, jadi tidak ada pengait
   CSS untuk menarik tombol itu kembali. Akibatnya sekali ditutup, sidebar tidak
   bisa dibuka lagi — dan di dalamnya ada panel kalibrasi biaya, inti demo ini.
   Kehilangan akses ke sana jauh lebih merugikan daripada kehilangan pilihan
   menyembunyikannya. */
/* Pada LAYAR LEBAR, tombol tutup sidebar dimatikan.
   Alasannya: Streamlit versi ini tidak menampilkan tombol buka yang bisa
   diklik setelah sidebar tertutup — elemennya bahkan hilang dari DOM. Sekali
   ditutup, panel kalibrasi biaya di dalamnya menjadi tidak terjangkau.
   Melumpuhkan geserannya lewat CSS sudah dicoba dan gagal: transform sidebar
   dikendalikan di luar jangkauan CSS kita.

   Menutup akses ke tombol tutup ini AMAN, karena keadaan tertutup TIDAK
   tersimpan — memuat ulang halaman selalu mengembalikan sidebar. Jadi tidak
   ada jalan buntu yang permanen.

   Di ponsel tombol ini justru DIBIARKAN hidup: di sana sidebar memang laci
   yang harus bisa ditutup untuk membaca isinya. */
@media (min-width: 993px) {{
  [data-testid="stSidebarCollapseButton"] {{ display:none !important; }}
}}
.block-container {{ padding-top:1.6rem; padding-bottom:2rem; max-width:1400px; }}

/* ---------------------------------------------------------------- KEPALA */
.kicker {{
  font-size:12px; font-weight:700; letter-spacing:1.4px; text-transform:uppercase;
  color:{BIRU}; margin-bottom:2px;
}}
.kicker span {{ color:{TINTA}; font-weight:600; letter-spacing:.4px; }}
.judul {{
  font-size:34px; font-weight:800; color:{TINTA}; letter-spacing:-1px;
  line-height:1.15; margin:0 0 3px 0;
}}
.judul em {{ color:{BIRU}; font-style:normal; }}
.judul .soga {{ color:{SOGA}; font-style:normal; }}
.subjudul {{ font-size:15px; color:{ABU}; margin:0; }}
.garis-soga {{
  height:4px; width:78%; border-radius:2px; margin:12px 0 18px 0;
  background:linear-gradient(90deg, {SOGA} 0%, {SOGA_MUDA} 70%, transparent 100%);
}}
.blok-penyelenggara {{
  background:#fff; border:1px solid #E5E5E5; border-radius:12px;
  padding:9px 15px; text-align:right; box-shadow:0 1px 3px rgba(0,0,0,.05);
}}
.blok-penyelenggara .atas {{
  font-size:9px; letter-spacing:1.2px; color:{ABU}; text-transform:uppercase;
}}
.blok-penyelenggara .tengah {{ font-size:17px; font-weight:800; color:{BIRU}; letter-spacing:-.4px; }}
.blok-penyelenggara .bawah {{ font-size:10px; color:{BIRU}; font-weight:600; }}

/* ----------------------------------------------------------------- KARTU */
.kartu {{
  background:{KREM}; border:1px solid {SOGA_MUDA}; border-radius:14px;
  padding:26px 20px 18px 20px; margin-top:16px; position:relative; height:100%;
  /* menjadikan kartu sebagai acuan ukuran, sehingga angka di dalamnya bisa
     mengecil mengikuti LEBAR KARTU — bukan lebar layar */
  container-type:inline-size;
}}
.kartu.utama {{ border:2px solid {BIRU}; }}
.pil {{
  position:absolute; top:-13px; left:20px;
  background:{BIRU}; color:{KREM}; font-size:11px; font-weight:700;
  letter-spacing:.9px; text-transform:uppercase;
  padding:5px 15px; border-radius:999px;
}}
.pil.soga {{ background:{SOGA}; }}

/* -------------------------------------------------------- ANGKA PAHLAWAN */
/* Angka pahlawan TIDAK BOLEH membungkus. "Rp4.370.000" yang patah jadi
   "Rp4.370.00" + "0" bukan sekadar jelek — angkanya jadi salah dibaca.
   Baris pertama adalah cadangan untuk peramban lama; baris clamp berikutnya
   membuat ukurannya mengikuti lebar kartu (satuan cqi), sehingga muat pada
   kartu sempit tanpa mengecilkan yang lebar. */
.angka {{
  font-size:44px;
  font-size:clamp(24px, 12cqi, 44px);
  font-weight:800; letter-spacing:-1.5px; line-height:1.08; color:{BIRU};
  white-space:nowrap;
}}
.angka.besar {{
  font-size:60px;
  font-size:clamp(28px, 16cqi, 60px);
}}
.angka.merah {{ color:{TERAKOTA}; }}
.angka.hijau {{ color:{HIJAU}; }}
.angka.soga  {{ color:{SOGA}; }}
.angka-label {{ font-size:12px; color:{ABU}; font-weight:600; margin-top:1px; }}

/* ---------------------------------------------------------- BAR PAHLAWAN */
.bar-pahlawan {{
  background:linear-gradient(100deg, {BIRU} 0%, {BIRU_TUA} 100%);
  border-radius:14px; padding:18px 26px; color:{KREM};
  display:flex; align-items:center; gap:26px; flex-wrap:wrap;
  margin:6px 0 4px 0; position:relative; overflow:hidden;
}}
.bar-pahlawan .n {{ font-size:40px; font-weight:800; color:{SOGA_MUDA}; letter-spacing:-1.5px; }}
.bar-pahlawan .t {{ font-size:13px; opacity:.92; line-height:1.3; }}
/* Pemisah antar angka — garis meruncing berujung anak panah.
   Dua percobaan sebelumnya gagal karena alasan berlawanan: karakter "▶" 26px
   terlalu ringan hingga terbaca seperti noda, sedangkan lencana bulat 44px
   terlalu berat hingga bersaing dengan angkanya sendiri. Bentuk ini menempati
   ruang selebar keduanya, tetapi bobot tintanya tipis — hadir tanpa menuntut
   perhatian, dan arah "menjadi" terbaca jelas. */
.bar-pahlawan .pisah {{
  flex:0 0 auto; position:relative;
  width:64px; height:2px; margin:0 4px;
  font-size:0;                       /* sembunyikan karakter aslinya */
  background:linear-gradient(to right, rgba(198,139,60,0), {SOGA});
  border-radius:2px;
}}
.bar-pahlawan .pisah::after {{
  content:""; position:absolute; right:-2px; top:-5px;
  border-left:11px solid {SOGA};
  border-top:6px solid transparent;
  border-bottom:6px solid transparent;
}}
/* Motif sudut. Memakai GAMBAR megamendung asli, bukan SVG gambaran sendiri.
   Warnanya dicuci jadi keputihan lewat filter agar tampil setara dengan versi
   SVG sebelumnya — putih samar di atas biru. Grayscale dulu supaya biru asli
   motif tidak bertabrakan dengan biru bar. */
/* Satu-satunya lapisan motif pada bar. Setelah lapisan full-bleed dibuang,
   motif ini diberi ruang lebih lega: dibesarkan dan digeser lebih ke luar
   supaya yang tampak hanya LENGKUNG BESARNYA — bukan pusaran kecil yang
   rapat, sebab pusaran rapat itulah yang tadi terbaca berantakan. */
.bar-pahlawan .awan {{
  position:absolute; right:-120px; bottom:-190px;
  width:620px; height:460px; pointer-events:none;
  background-size:cover; background-position:left top;
  filter:grayscale(1) brightness(2.5) contrast(.40);
  opacity:.15;
  /* Elemen ini kotak, jadi tepi kirinya terpotong lurus dan terbaca sebagai
     garis pemisah. Masker dua arah melunakkan tepi kiri sekaligus tepi atas. */
  -webkit-mask-image:
    linear-gradient(to left, #000 0%, #000 30%, transparent 96%),
    linear-gradient(to top,  #000 0%, #000 55%, transparent 100%);
  -webkit-mask-composite:source-in;
  mask-image:
    linear-gradient(to left, #000 0%, #000 30%, transparent 96%),
    linear-gradient(to top,  #000 0%, #000 55%, transparent 100%);
  mask-composite:intersect;
}}
/* CATATAN: lapisan motif full-bleed (.kain) sengaja DIHAPUS.
   Sebelumnya bar memuat DUA salinan motif sekaligus — satu memenuhi seluruh
   bidang, satu lagi di sudut — pada skala dan posisi berbeda. Lengkung
   keduanya saling memotong dan terbaca sebagai motif yang bertabrakan.
   Kini hanya tersisa satu motif di sudut, dan latar bar cukup memakai
   gradasinya sendiri. */
/* HARUS mengecualikan .awan juga. Tanpa itu, awan SVG yang seharusnya
   melayang (position:absolute) ikut dipaksa relative, masuk aliran normal,
   dan menambah ~230px ruang kosong di bawah angka. */
.bar-pahlawan > div:not(.awan) {{ position:relative; z-index:2; }}

/* ------------------------------------------------------------- PONSEL WA */
.ponsel {{
  background:#1c1c1e; border-radius:38px; padding:11px; max-width:400px;
  box-shadow:0 14px 34px rgba(0,0,0,.22); margin:0 auto;
}}
.layar {{ background:#ECE5DD; border-radius:28px; overflow:hidden; }}
.wa-kepala {{
  background:#075E54; color:#fff; padding:12px 16px 10px 16px;
  display:flex; align-items:center; gap:11px;
}}
.wa-avatar {{
  width:36px; height:36px; border-radius:50%; background:#FFFFFF;
  display:flex; align-items:center; justify-content:center; font-size:17px;
  overflow:hidden; flex:0 0 36px;
}}
.wa-avatar img {{ width:100%; height:100%; object-fit:contain; padding:3px; }}
/* Tanpa berkas lambang, avatar kembali memakai emoji di atas lingkaran soga */
.wa-avatar.emoji {{ background:{SOGA}; }}
.wa-nama {{ font-weight:600; font-size:14.5px; line-height:1.2; }}
.wa-status {{ font-size:11px; opacity:.82; }}
/* Dinding percakapan. WhatsApp asli memang punya wallpaper, jadi memasang
   megamendung di sini bukan hiasan yang dipaksakan — justru autentik. Aman
   pula: gelembung pesan berlatar penuh, jadi teksnya tidak pernah bertabrakan
   dengan motif. */
.wa-isi {{
  padding:14px 11px 18px 11px; max-height:452px; overflow-y:auto;
  background-size:cover; background-position:center;
  /* Lapisan krem menyatu ke dalam background, BUKAN elemen ::before terpisah.
     Versi sebelumnya memakai ::before dengan inset:0; di wadah yang bisa
     digulung, elemen itu hanya menutupi tinggi yang terlihat, sehingga saat
     percakapan digulung motifnya muncul mentah tanpa peredam. Sebagai latar,
     peredamnya selalu ikut ke mana pun isinya digulung. */
  background-color:#ECE5DD;
}}
.gel {{
  max-width:82%; padding:8px 12px; border-radius:11px; margin:7px 0;
  font-size:13.5px; line-height:1.46; box-shadow:0 1px 1px rgba(0,0,0,.11);
  white-space:pre-wrap; word-wrap:break-word; position:relative;
}}
.kanan {{ background:#DCF8C6; margin-left:auto; border-top-right-radius:3px; }}
.kiri  {{ background:#FFFFFF; margin-right:auto; border-top-left-radius:3px; }}
.jam   {{ font-size:10px; color:#8b8b8b; text-align:right; margin-top:3px; }}
.tanda {{
  display:inline-block; font-size:9.5px; font-weight:700; letter-spacing:.5px;
  padding:2px 8px; border-radius:999px; background:{BIRU_MUDA}; color:{BIRU};
  margin-bottom:5px; text-transform:uppercase;
}}
.tanda.aturan {{ background:#EFEFEF; color:{ABU}; }}
.pil-basa {{
  display:inline-block; font-size:10px; padding:2px 9px; border-radius:999px;
  border:1px solid #cfd8e3; color:{ABU}; margin:6px 4px 0 0; background:#fff;
}}
.pil-basa.aktif {{ background:{BIRU}; color:#fff; border-color:{BIRU}; font-weight:600; }}

/* ---------------------------------------------------------------- TOMBOL */
.stButton button {{
  border-radius:10px; border:1px solid {SOGA_MUDA}; background:{KREM};
  color:{TINTA}; font-size:12.5px; text-align:left; transition:all .12s;
  /* Tombol Streamlit adalah wadah flex ber-justify-content:center. Menyetel
     text-align saja TIDAK cukup: blok teksnya tetap dipusatkan, lalu tiap
     baris menyusut selebar isinya — sehingga tepi kirinya bergerigi dan
     daftar contoh kalimat terbaca berantakan. Perataan harus dilakukan pada
     wadah flexnya, bukan pada teksnya. */
  justify-content:flex-start;
}}
/* Isi tombol dibungkus DUA lapis flex, dan keduanya ber-justify-content:center.
   Meratakan lapis luar saja tidak cukup: lapis dalam tetap menciutkan span
   selebar teksnya lalu memusatkannya, sehingga tombol berteks pendek mulai
   jauh lebih ke kanan daripada yang berteks panjang. Keduanya harus diratakan,
   dan tiap lapis dipaksa selebar penuh agar tidak menciut. */
.stButton button > div {{ justify-content:flex-start; width:100%; }}
.stButton button > div > span,
.stButton button [data-testid="stMarkdownContainer"],
.stButton button p {{
  width:100%; text-align:left; margin:0;
}}

/* Tombol utama tetap dipusatkan — isinya perintah pendek, bukan kalimat. */
.stButton button[kind="primary"],
.stButton button[kind="primary"] > div {{ justify-content:center; }}
.stButton button[kind="primary"] > div > span,
.stButton button[kind="primary"] [data-testid="stMarkdownContainer"],
.stButton button[kind="primary"] p {{ text-align:center; }}
.stButton button:hover {{ border-color:{BIRU}; color:{BIRU}; background:#fff; }}
.stButton button[kind="primary"] {{
  background:{BIRU}; color:#fff; border-color:{BIRU}; font-weight:700;
}}
.stButton button[kind="primary"]:hover {{ background:{BIRU_TUA}; color:#fff; }}

/* ------------------------------------------------------------------ LAIN */
.stTabs [data-baseweb="tab-list"] {{ gap:6px; border-bottom:1px solid #eee; }}
.stTabs [data-baseweb="tab"] {{
  font-size:13.5px; font-weight:600; color:{ABU}; padding:9px 16px;
}}
.stTabs [aria-selected="true"] {{ color:{BIRU} !important; }}
.stTabs [data-baseweb="tab-highlight"] {{ background:{BIRU}; height:3px; }}
section[data-testid="stSidebar"] {{ background:{KREM}; border-right:1px solid #ece3d5; }}

/* ------------------------------------------------------------------ PONSEL
   Juri hampir pasti membuka tautan ini dari ponsel. Pemilik UMKM sendiri
   memakai WhatsApp, bukan halaman ini — tetapi kalau tampilannya berdesakan
   saat dinilai, seluruh isinya tidak terbaca. */
@media (max-width: 992px) {{
  /* Sidebar diperlakukan sebagai LACI, bukan dinding: menyisakan sedikit isi
     yang terlihat di kanan supaya jelas ia menimpa sementara dan bisa ditutup.
     Kalau menutup seluruh lebar, pembukanya mengira itulah seluruh halaman. */
  section[data-testid="stSidebar"] {{
    width:84vw !important; min-width:0 !important; max-width:300px !important;
    box-shadow:6px 0 26px rgba(0,0,0,.18);
  }}

  .block-container {{ padding-left:14px !important; padding-right:14px !important; }}
  .judul {{ font-size:25px; letter-spacing:-.6px; }}
  .subjudul {{ font-size:13.5px; }}
  .garis-soga {{ width:100%; }}

  /* blok penyelenggara pindah ke bawah judul, tidak lagi berdesakan di kanan */
  .blok-penyelenggara {{ text-align:left; margin-top:8px; }}
  .blok-penyelenggara img {{ margin-left:0 !important; }}

  /* bar pahlawan menumpuk ke bawah; panah horizontal tidak masuk akal lagi */
  .bar-pahlawan {{ flex-direction:column; align-items:flex-start; gap:14px;
                   padding:16px 18px; }}
  .bar-pahlawan .n {{ font-size:32px; }}
  .bar-pahlawan .pisah {{ display:none; }}
  .bar-pahlawan .awan {{ width:320px; height:240px; right:-70px; bottom:-120px; }}

  /* ponsel mockup diperkecil supaya muat utuh tanpa menggulung ke samping */
  .ponsel {{ max-width:100%; padding:8px; border-radius:28px; }}
  .layar {{ border-radius:22px; }}
  .wa-isi {{ max-height:400px; }}

  .kartu {{ padding:24px 15px 15px 15px; }}
  .kicker {{ font-size:11px; }}
}}
div[data-testid="stDataFrame"] {{ border:1px solid {SOGA_MUDA}; border-radius:10px; }}
hr {{ border-color:#eee; }}
</style>
"""


def kepala(kicker_kiri, kicker_kanan, judul_html, subjudul):
    """Kepala slide: kicker, judul berfrasa warna, sub, garis soga."""
    return f"""
    <div class="kicker">{kicker_kiri} <span>· {kicker_kanan}</span></div>
    <div class="judul">{judul_html}</div>
    <div class="subjudul">{subjudul}</div>
    <div class="garis-soga"></div>
    """


def berkas_gambar(nama_dasar: str) -> str | None:
    """Cari berkas gambar di folder ini dan ubah jadi data URI.

    Dipakai untuk aset yang TIDAK BOLEH digambar ulang oleh kode — logo
    institusi maupun karya visual. Logo yang salah gambar lebih merusak
    daripada tidak ada logo sama sekali. Kalau berkasnya belum ada,
    kembalikan None dan pemanggil memakai versi cadangan.
    """
    import base64
    from pathlib import Path

    folder = Path(__file__).parent
    for akhiran in (".png", ".jpg", ".jpeg", ".webp", ".svg"):
        berkas = folder / f"{nama_dasar}{akhiran}"
        if berkas.exists():
            jenis = "svg+xml" if akhiran == ".svg" else akhiran.lstrip(".")
            data = base64.b64encode(berkas.read_bytes()).decode()
            return f"data:image/{jenis};base64,{data}"
    return None


def _logo_terpasang():
    return berkas_gambar("logo-bi")


def logo_canting():
    """Logo CANTING AI lengkap dengan tulisannya — untuk sidebar."""
    return berkas_gambar("logo-canting")


def ikon_canting():
    """Lambang CANTING saja, tanpa tulisan — bujur sangkar, untuk avatar.

    Logo penuh memuat wordmark "CANTING AI" di bawah lambangnya. Dipaksa masuk
    lingkaran avatar 36px, tulisannya akan gepeng dan tak terbaca. Karena itu
    dipakai berkas terpisah yang hanya berisi lambangnya.
    """
    return berkas_gambar("logo-canting-ikon") or berkas_gambar("logo-canting")


def kain_megamendung():
    """Motif megamendung bergambar — berkas `megamendung.*` di folder ini.

    Berbeda dengan fungsi megamendung() yang menggambar SVG sederhana, ini
    adalah karya visual penuh. Sengaja TIDAK dipakai sebagai latar seluruh
    halaman: motifnya padat, dan angka-angka pada papan akan tenggelam.
    Hanya dipakai pada dua tempat yang memang dekoratif dan tidak memuat
    data — bar pahlawan dan dinding percakapan.
    """
    return berkas_gambar("megamendung")


def penyelenggara():
    logo = _logo_terpasang()
    tengah = (f'<img src="{logo}" alt="Bank Indonesia" '
              f'style="height:42px;display:block;margin:3px 0 4px auto;'
              f'max-width:100%">'
              if logo else
              '<div class="tengah">BANK INDONESIA</div>')
    return f"""
    <div class="blok-penyelenggara">
      <div class="atas">Diselenggarakan oleh</div>
      {tengah}
      <div class="bawah">ImpactPreneur Business Challenge · KPw Cirebon</div>
    </div>
    """


def latar_megamendung():
    """Tidak dipakai lagi — latar kini dipasang lewat background pada .stApp.

    Dipertahankan sebagai fungsi kosong agar pemanggilan lama tidak error.
    """
    return ""


def kartu(pil_teks, isi_html, utama=False, warna_pil=""):
    kelas = "kartu utama" if utama else "kartu"
    return (f'<div class="{kelas}"><div class="pil {warna_pil}">{pil_teks}</div>'
            f'{isi_html}</div>')


def angka(nilai, label, kelas=""):
    return (f'<div><div class="angka {kelas}">{nilai}</div>'
            f'<div class="angka-label">{label}</div></div>')
