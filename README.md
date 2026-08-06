# CANTING AI — Prototipe

Prototipe untuk **ImpactPreneur Business Challenge**, Bank Indonesia KPw Cirebon.
Studi kasus: **UKM Silfi Batik Tulis**, Desa Ciwaringin, Kabupaten Cirebon.

> Buku besar mencatat apa yang **sudah** terjadi.
> CANTING memberi tahu **order mana yang sebenarnya untung — sebelum dikerjakan.**

---

## Memasang logo Bank Indonesia

Simpan berkas logo resmi (PNG berlatar transparan) sebagai **`logo-bi.png`**
di folder ini. Aplikasi mendeteksinya sendiri dan langsung memakainya —
tidak ada pengaturan yang perlu diubah. Nama lain yang juga dikenali:
`logo-bi.jpg`, `logo-bi.webp`, `logo-bi.svg`.

Selama berkasnya belum ada, blok penyelenggara memakai tulisan biasa dan
sidebar menampilkan pengingat.

> Logo **sengaja tidak digambar ulang** dalam bentuk SVG atau susunan huruf.
> Logo bank sentral yang bentuknya meleset lebih merusak daripada tidak ada
> logo sama sekali. Aturan yang sama berlaku pada deck.

Tulisan **"DISELENGGARAKAN OLEH"** di atas logo wajib dipertahankan, supaya
logo terbaca sebagai keterangan penyelenggara — bukan klaim dukungan atas isi
proposal.

---

## Menjalankan di komputer sendiri

```bash
pip install -r requirements.txt
streamlit run app.py
```

Terbuka di `http://localhost:8501`.

Kunci API **tidak wajib**. Tanpa kunci, ekstraksi memakai mesin aturan —
lebih sederhana daripada LLM, tetapi tidak pernah mati saat didemokan.

---

## Menyebarkan ke Streamlit Cloud (gratis, untuk tautan di slide 4)

1. Unggah folder `prototipe-canting/` ke sebuah repositori GitHub publik.
2. Buka [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Pilih repositorinya, isi **Main file path** dengan `app.py`.
4. *(opsional)* **Advanced settings → Secrets**, isi:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
5. **Deploy.** Tautannya berbentuk `https://<nama>.streamlit.app` —
   itu yang ditempel di slide 4.

Tanpa langkah 4 pun aplikasinya tetap jalan penuh.

---

## Susunan berkas

| Berkas | Isi |
|---|---|
| `app.py` | Antarmuka Streamlit — percakapan gaya WhatsApp, papan angka, penjelasan |
| `biaya.py` | Mesin biaya Activity-Based Costing. **Konstantanya harus sama persis dengan `../model_finansial_canting.py`** |
| `ekstraksi.py` | Ekstraksi kejadian: LLM sebagai jalur utama, aturan sebagai cadangan |
| `bahasa.py` | Leksikon bahasa Cirebon + templat balasan (ragam *bebasan*) |
| `buku.py` | Buku kejadian, artisan-day, diagnosa kendala, peringkat motif |

---

## Enam jenis kejadian

Hanya enam, dan dari enam ini seluruh angka pada proposal dapat dihitung:

| Kejadian | Contoh kalimat |
|---|---|
| `BELI` | "td beli kain sm bu ani 5 lembar, 400 apa 450 ya lupa" |
| `MULAI` | "mulai garap megamendung buat bu risa" |
| `SELESAI` | "wis dilorod kabeh, siki ngenteni garing" |
| `JUAL` | "laku 1 kain megamendung 850rb" |
| `BAYAR` | "bayar mbak sri 300rb" |
| `TANYA` | "ada yang nawar 550rb buat kain sogan, ambil ga?" |

Pasangan **`MULAI` + `SELESAI` melahirkan hari kerja** — variabel yang selama ini
tidak pernah ada di UMKM mana pun, dan tanpa itu "untung per hari kerja" mustahil
dihitung.

---

## Tiga hal yang layak diperhatikan saat mencoba

**1. Konfirmasi satu ketuk.**
Tulis kalimat yang ragu ("400 apa 450 ya lupa"). Sistem tidak menebak diam-diam —
ia menawarkan tombol. Ekstraksi AI pasti sesekali salah; jalan keluarnya bukan
mengejar model sempurna, melainkan membuat koreksinya semurah satu ketukan.
Kalau pemilik harus mengetik ulang, ia berhenti memakai dalam sepekan.

**2. Bahasa Cirebon terdeteksi sendiri.**
Tulis *"wis dilorod kabeh"* — balasan otomatis berpindah ke bahasa Cirebon
ragam **bebasan**, ragam halus untuk orang yang dituakan. Nama motif seperti
*megamendung* sengaja **tidak** dijadikan penanda bahasa, karena dipakai penutur
kedua bahasa.

**3. Diagnosa mendahului saran.**
Buka **Papan Angka**. Sistem lebih dulu menetapkan kendala yang mengikat —
kapasitas atau permintaan — baru memilih tuas. Kalau slot kosong, menaikkan
harga justru mematikan permintaan.

Dan pada **Peringkat motif**, perhatikan bahwa kain seharga Rp1.000.000 yang
butuh 9 hari kalah menguntungkan daripada kain Rp850.000 yang selesai 5 hari.

---

## Batas yang jujur

- Riwayat awal adalah **data contoh**, bukan pembukuan Silfi yang sebenarnya.
- Solver LP/ILP belum dipasang; pengurutan menurut untung per hari kerja
  memberi hasil yang sama untuk kasus sekecil ini.
- Masukan suara belum tersedia.
- Kalimat bahasa Cirebon disusun dari rujukan tertulis dan **belum divalidasi
  penutur asli**. Setelah divalidasi, ubah `VALIDASI_PENUTUR_ASLI = True`
  pada `bahasa.py`.

---

## Angka rujukan

| | |
|---|---|
| Upah perajin | Rp67.000/hari — 65% UMK Kab. Cirebon 2025 (Rp2.681.382 ÷ 26 hari) |
| Biaya penuh per kain | **Rp574.400** |
| Margin pada harga rata-rata Rp675.000 | Rp100.600 (15%) |
| Untung per hari kerja | **Rp19.346** |
| Impas pada upah formal penuh | **Rp762.276** — 13% di atas harga rata-rata saat ini |

Sumber seluruh angka: `../model_finansial_canting.py`
