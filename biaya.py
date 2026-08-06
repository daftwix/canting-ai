# -*- coding: utf-8 -*-
"""
Mesin biaya CANTING AI — Activity-Based Costing.

Nilai baku di sini HARUS sama persis dengan model_finansial_canting.py.
Kalau salah satu diubah, ubah juga di sana, lalu jalankan ulang modelnya.

Seluruh angka dikumpulkan dalam satu objek Parameter supaya bisa diubah dari
antarmuka tanpa menyentuh kode — persis seperti Tahap 0 · Kalibrasi pada alur
kerja, tempat pemilik usaha menyebutkan harga bahan dan upah yang sebenarnya.
"""
from dataclasses import dataclass, replace

# ----------------------------------------------------------------- BASIS UPAH
# Rantai penurunan yang dapat diperiksa:
#   1. UMK Kabupaten Cirebon 2025          = Rp2.681.382 / bulan
#   2. dibagi 26 hari kerja                = Rp103.130 / hari  (upah formal)
#   3. dikali faktor sentra kerajinan 0,65 = Rp67.000 / hari
UMK_KAB_CIREBON_2025 = 2_681_382
HARI_KERJA_PER_BULAN = 26
UPAH_UMK_HARIAN = UMK_KAB_CIREBON_2025 / HARI_KERJA_PER_BULAN
FAKTOR_SENTRA = 0.65
UPAH_PER_HARI = round(UPAH_UMK_HARIAN * FAKTOR_SENTRA, -3)      # Rp67.000

# Nilai baku — dipertahankan sebagai konstanta agar rujukan lama tetap jalan
BIAYA_BAHAN = 150_000
BIAYA_PEWARNA_ENERGI = 60_000
BIAYA_OVERHEAD = 16_000
ARTISAN_DAY_PER_KAIN = 5.2
HARGA_RATA = 675_000
KAIN_PER_BULAN = 15
ARTISAN_DAY_PER_BULAN = KAIN_PER_BULAN * ARTISAN_DAY_PER_KAIN            # 78
KAPASITAS_ARTISAN_DAY_PER_MINGGU = round(ARTISAN_DAY_PER_BULAN / 4.33)   # 18


@dataclass(frozen=True)
class Parameter:
    """Semua angka biaya dalam satu tempat, supaya bisa dikalibrasi ulang.

    Dibuat frozen agar perubahan selalu menghasilkan objek baru — mencegah
    satu sesi pengguna diam-diam mengubah angka milik sesi lain.
    """
    bahan: float = BIAYA_BAHAN
    pewarna_energi: float = BIAYA_PEWARNA_ENERGI
    overhead: float = BIAYA_OVERHEAD
    upah_per_hari: float = UPAH_PER_HARI
    artisan_day_per_kain: float = ARTISAN_DAY_PER_KAIN
    harga_rata: float = HARGA_RATA
    kapasitas_minggu: int = KAPASITAS_ARTISAN_DAY_PER_MINGGU

    @property
    def biaya_tanpa_tenaga(self) -> float:
        return self.bahan + self.pewarna_energi + self.overhead

    @property
    def persen_umk(self) -> float:
        return self.upah_per_hari / UPAH_UMK_HARIAN

    def ubah(self, **kolom) -> "Parameter":
        return replace(self, **kolom)


BAKU = Parameter()


# ------------------------------------------------------------------ PERHITUNGAN
def biaya_penuh(hari_kerja: float | None = None, p: Parameter | None = None) -> float:
    """Biaya penuh satu kain. Tenaga dihitung dari hari kerja NYATA bila ada."""
    p = p or BAKU
    hari = p.artisan_day_per_kain if hari_kerja is None else hari_kerja
    return p.biaya_tanpa_tenaga + hari * p.upah_per_hari


def hitung_margin(harga_jual: float, hari_kerja: float | None = None,
                  p: Parameter | None = None) -> dict:
    """Hasil lengkap satu kain: biaya, margin, dan untung per hari kerja."""
    p = p or BAKU
    hari = p.artisan_day_per_kain if hari_kerja is None else hari_kerja
    bp = biaya_penuh(hari, p)
    margin = harga_jual - bp
    return {
        "biaya_penuh": bp,
        "margin": margin,
        "margin_pct": margin / harga_jual if harga_jual else 0.0,
        "untung_per_hari": margin / hari if hari else 0.0,
        "rugi": margin < 0,
    }


def lantai_harga(hari_kerja: float | None = None, margin_minimum: float = 0.0,
                 p: Parameter | None = None) -> float:
    """Harga terendah yang masih menutup biaya penuh.

    margin_minimum=0 berarti impas. Isi 0,15 bila ingin menjaga margin 15%.
    """
    bp = biaya_penuh(hari_kerja, p)
    return bp / (1 - margin_minimum) if margin_minimum < 1 else bp


def titik_impas_upah_formal(p: Parameter | None = None) -> float:
    """Harga jual minimum bila perajin dibayar setara UMK penuh."""
    p = p or BAKU
    return p.biaya_tanpa_tenaga + p.artisan_day_per_kain * UPAH_UMK_HARIAN


def rupiah(n: float) -> str:
    """Format rupiah gaya Indonesia: Rp574.400 (titik sebagai pemisah ribuan)."""
    tanda = "-" if n < 0 else ""
    return f"{tanda}Rp{abs(int(round(n))):,}".replace(",", ".")


if __name__ == "__main__":
    p = BAKU
    print(f"Upah per hari      {rupiah(p.upah_per_hari)}  ({p.persen_umk:.0%} UMK)")
    print(f"Biaya penuh/kain   {rupiah(biaya_penuh(p=p))}")
    h = hitung_margin(p.harga_rata, p=p)
    print(f"Margin             {rupiah(h['margin'])}  ({h['margin_pct']:.0%})")
    print(f"Untung/hari kerja  {rupiah(h['untung_per_hari'])}")
    print(f"Impas upah formal  {rupiah(titik_impas_upah_formal(p))}")

    print("\nContoh kalibrasi ulang — harga kain mori naik jadi Rp180.000:")
    p2 = p.ubah(bahan=180_000)
    h2 = hitung_margin(p2.harga_rata, p=p2)
    print(f"  Biaya penuh      {rupiah(biaya_penuh(p=p2))}")
    print(f"  Margin           {rupiah(h2['margin'])}  ({h2['margin_pct']:.0%})")
