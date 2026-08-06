# -*- coding: utf-8 -*-
"""
Solver bauran produk (product-mix) CANTING AI — Integer Linear Programming.

MASALAHNYA
----------
Kapasitas Silfi dibatasi HARI KERJA PERAJIN, bukan modal. Setiap motif memakan
jumlah hari yang berbeda dan menghasilkan margin yang berbeda. Pertanyaannya:
dalam kapasitas sekian artisan-day, motif apa saja yang sebaiknya dikerjakan
supaya total labanya paling besar?

RUMUSAN
-------
    peubah keputusan   x_i  = jumlah kain motif i yang dikerjakan (bulat, >= 0)
    fungsi tujuan      maks  Sum_i (harga_i - biaya_penuh_i) * x_i
    kendala kapasitas  Sum_i hari_i * x_i  <=  K
    kendala permintaan komitmen_i <= x_i <= permintaan_i

Bulat (integer), bukan pecahan, karena kain tidak bisa dikerjakan setengah.
Itulah sebabnya ILP, bukan LP biasa.

KENAPA PENGURUTAN SAJA TIDAK SELALU CUKUP
-----------------------------------------
Mengurutkan menurut untung per hari kerja adalah heuristik rakus (greedy).
Untuk kasus kecil hasilnya sering sama dengan optimum. Tetapi begitu ada
kendala permintaan dan sisa kapasitas yang tanggung, greedy bisa menyisakan
kapasitas menganggur yang sebenarnya masih bisa diisi motif lain.
Modul ini menjalankan KEDUANYA dan melaporkan selisihnya secara terbuka.
"""
from __future__ import annotations

from dataclasses import dataclass

import biaya as B


@dataclass
class Motif:
    nama: str
    harga: float
    hari_kerja: float
    permintaan: int = 99      # batas atas pesanan yang realistis
    komitmen: int = 0         # pesanan yang sudah terlanjur diterima

    def margin(self, p: B.Parameter | None = None) -> float:
        return self.harga - B.biaya_penuh(self.hari_kerja, p)

    def untung_per_hari(self, p: B.Parameter | None = None) -> float:
        return self.margin(p) / self.hari_kerja if self.hari_kerja else 0.0


def _greedy(motif: list[Motif], kapasitas: float,
            p: B.Parameter | None = None) -> dict:
    """Heuristik rakus: penuhi komitmen, lalu isi sisa dari untung/hari tertinggi."""
    pilihan = {m.nama: m.komitmen for m in motif}
    sisa = kapasitas - sum(m.hari_kerja * m.komitmen for m in motif)

    for m in sorted(motif, key=lambda m: -m.untung_per_hari(p)):
        if m.untung_per_hari(p) <= 0:
            continue
        while (pilihan[m.nama] < m.permintaan and m.hari_kerja <= sisa):
            pilihan[m.nama] += 1
            sisa -= m.hari_kerja

    laba = sum(m.margin(p) * pilihan[m.nama] for m in motif)
    return {"pilihan": pilihan, "laba": laba,
            "hari_terpakai": kapasitas - sisa, "metode": "greedy"}


def _lp_relaksasi(motif: list[Motif], kapasitas: float,
                  p: B.Parameter | None = None) -> dict | None:
    """LP — rumusan yang sama, tetapi peubahnya boleh PECAHAN.

    Kenapa ini dihitung juga, bukan sekadar pelengkap:

    1. LP selalu memberi nilai yang lebih baik atau sama dengan ILP, karena
       himpunan solusinya lebih longgar. Jadi hasil LP adalah BATAS ATAS yang
       terbukti bagi ILP — kalau ILP sudah menyentuh batas itu, kita tahu pasti
       tidak ada bauran lain yang lebih baik.
    2. Selisih LP dengan ILP adalah ONGKOS KEBULATAN: kerugian yang timbul
       justru karena kain tidak bisa dikerjakan setengah. Angka itu tidak
       terlihat kalau hanya menjalankan ILP.
    3. Sisa kapasitas pada solusi ILP jadi bisa dinilai: menganggur karena
       memang tidak ada pekerjaan, atau menganggur karena terpaksa dibulatkan.
    """
    try:
        from ortools.linear_solver import pywraplp
    except ImportError:
        return None

    s = pywraplp.Solver.CreateSolver("GLOP")      # GLOP = solver LP murni
    if s is None:
        return None

    x = {m.nama: s.NumVar(m.komitmen, m.permintaan, m.nama) for m in motif}
    s.Add(sum(m.hari_kerja * x[m.nama] for m in motif) <= kapasitas)
    s.Maximize(sum(m.margin(p) * x[m.nama] for m in motif))

    if s.Solve() != pywraplp.Solver.OPTIMAL:
        return None

    pilihan = {m.nama: round(x[m.nama].solution_value(), 2) for m in motif}
    return {
        "pilihan": pilihan,
        "laba": s.Objective().Value(),
        "hari_terpakai": sum(m.hari_kerja * pilihan[m.nama] for m in motif),
        "metode": "LP · OR-Tools GLOP",
        "waktu_ms": s.wall_time(),
    }


def optimalkan(motif: list[Motif], kapasitas: float,
               p: B.Parameter | None = None) -> dict:
    """Cari bauran produk terbaik. Kembalikan hasil solver + pembanding greedy.

    Kalau OR-Tools tidak tersedia, hasil greedy dipakai sebagai jawaban.
    Prototipe tidak boleh mati hanya karena satu pustaka tidak terpasang.
    """
    hasil_greedy = _greedy(motif, kapasitas, p)

    try:
        from ortools.linear_solver import pywraplp
    except ImportError:
        return {**hasil_greedy, "metode": "greedy (OR-Tools tidak terpasang)",
                "greedy": hasil_greedy, "optimal": False, "selisih": 0.0}

    s = pywraplp.Solver.CreateSolver("SCIP") or pywraplp.Solver.CreateSolver("CBC")
    if s is None:
        return {**hasil_greedy, "metode": "greedy (solver tidak tersedia)",
                "greedy": hasil_greedy, "optimal": False, "selisih": 0.0}

    x = {m.nama: s.IntVar(m.komitmen, m.permintaan, m.nama) for m in motif}

    # kendala kapasitas — satu-satunya sumber daya yang langka
    s.Add(sum(m.hari_kerja * x[m.nama] for m in motif) <= kapasitas)

    # tujuan: maksimalkan total margin
    s.Maximize(sum(m.margin(p) * x[m.nama] for m in motif))

    status = s.Solve()
    if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        return {**hasil_greedy, "metode": "greedy (solver gagal)",
                "greedy": hasil_greedy, "optimal": False, "selisih": 0.0}

    pilihan = {m.nama: int(round(x[m.nama].solution_value())) for m in motif}
    laba = s.Objective().Value()
    terpakai = sum(m.hari_kerja * pilihan[m.nama] for m in motif)
    lp = _lp_relaksasi(motif, kapasitas, p)

    return {
        "pilihan": pilihan,
        "laba": laba,
        "hari_terpakai": terpakai,
        "sisa_kapasitas": kapasitas - terpakai,
        "metode": "ILP · OR-Tools " + ("SCIP" if "SCIP" in s.SolverVersion() else "CBC"),
        "optimal": status == pywraplp.Solver.OPTIMAL,
        "greedy": hasil_greedy,
        "selisih": laba - hasil_greedy["laba"],
        "waktu_ms": s.wall_time(),
        # LP dipakai sebagai batas atas yang terbukti bagi ILP
        "lp": lp,
        "ongkos_kebulatan": (lp["laba"] - laba) if lp else None,
        "senjang_pct": ((lp["laba"] - laba) / lp["laba"] * 100)
                       if lp and lp["laba"] else None,
    }


def motif_dari_buku(buku, p: B.Parameter | None = None) -> list[Motif]:
    """Susun daftar motif dari riwayat penjualan yang sudah tercatat."""
    kumpul: dict[str, list[tuple[float, float]]] = {}
    for k in buku.kain:
        if k.harga_jual:
            kumpul.setdefault(k.produk, []).append((k.harga_jual, k.hari_kerja))

    motif = []
    for nama, catatan in kumpul.items():
        harga = sum(c[0] for c in catatan) / len(catatan)
        hari = sum(c[1] for c in catatan) / len(catatan)
        motif.append(Motif(nama=nama, harga=round(harga, -3),
                           hari_kerja=round(hari, 1), permintaan=6))
    return motif


if __name__ == "__main__":
    p = B.BAKU
    contoh = [
        Motif("megamendung", 875_000, 5.5, permintaan=4),
        Motif("singabarong", 1_000_000, 9.0, permintaan=3),
        Motif("wadasan",       620_000, 7.0, permintaan=5),
        Motif("sogan",         500_000, 4.0, permintaan=6),
    ]
    K = 18  # artisan-day per minggu

    print(f"Kapasitas {K} artisan-day/minggu\n")
    print(f"{'motif':14} {'harga':>11} {'hari':>5} {'margin':>11} {'untung/hari':>12}")
    for m in contoh:
        print(f"{m.nama:14} {B.rupiah(m.harga):>11} {m.hari_kerja:>5} "
              f"{B.rupiah(m.margin(p)):>11} {B.rupiah(m.untung_per_hari(p)):>12}")

    h = optimalkan(contoh, K, p)
    lp, g = h["lp"], h["greedy"]

    print(f"\n{'':12} {'laba':>13} {'hari':>7}   bauran")
    if lp:
        print(f"{'LP  (batas atas)':<22} {B.rupiah(lp['laba']):>13} "
              f"{lp['hari_terpakai']:>6.1f}   "
              + " · ".join(f"{n}×{v:g}" for n, v in lp["pilihan"].items() if v))
    print(f"{'ILP (dipakai)':<22} {B.rupiah(h['laba']):>13} "
          f"{h['hari_terpakai']:>6.1f}   "
          + " · ".join(f"{n}×{v}" for n, v in h["pilihan"].items() if v))
    print(f"{'Greedy (pembanding)':<22} {B.rupiah(g['laba']):>13} "
          f"{g['hari_terpakai']:>6.1f}")

    print(f"\nMetode ILP        {h['metode']} ({h.get('waktu_ms','-')} ms)")
    if h["ongkos_kebulatan"] is not None:
        print(f"Ongkos kebulatan  {B.rupiah(h['ongkos_kebulatan'])} "
              f"({h['senjang_pct']:.1f}% dari batas atas LP)")
    print(f"Selisih vs greedy {B.rupiah(h['selisih'])}")
