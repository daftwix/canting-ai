# -*- coding: utf-8 -*-
"""
Buku CANTING — menyimpan kejadian, menurunkan angka, dan mendiagnosa kendala.

Yang membedakan dari aplikasi pembukuan biasa: buku ini tidak berhenti pada
"uang masuk / uang keluar". Ia melacak ARTISAN-DAY, karena kapasitas Silfi
dibatasi hari kerja perajin — bukan modal.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

import biaya as B


@dataclass
class Kain:
    produk: str
    mulai: date | None = None
    selesai: date | None = None
    harga_jual: float | None = None

    @property
    def hari_kerja(self) -> float:
        if self.mulai and self.selesai:
            selisih = (self.selesai - self.mulai).days
            if selisih >= 1:
                return float(selisih)
        return B.ARTISAN_DAY_PER_KAIN     # belum ada data nyata

    @property
    def status(self) -> str:
        if self.harga_jual is not None:
            return "terjual"
        if self.selesai:
            return "selesai"
        return "dikerjakan"

    def hasil(self, p: B.Parameter | None = None) -> dict | None:
        if self.harga_jual is None:
            return None
        return B.hitung_margin(self.harga_jual, self.hari_kerja, p)


@dataclass
class Buku:
    kain: list[Kain] = field(default_factory=list)
    pengeluaran: list[dict] = field(default_factory=list)
    riwayat: list[dict] = field(default_factory=list)
    p: B.Parameter | None = None      # parameter biaya yang sedang berlaku

    def pakai(self, p: B.Parameter) -> "Buku":
        """Pasang parameter biaya terbaru. Dipanggil tiap kali kalibrasi diubah."""
        self.p = p
        return self

    # ------------------------------------------------------------- pencatatan
    def _kain_aktif(self, produk: str | None) -> Kain | None:
        """Kain yang paling pas untuk dikenai kejadian berikutnya.

        Bila motifnya DISEBUT tetapi tidak ada kain motif itu yang belum
        terjual, kembalikan None — jangan pernah jatuh ke kain lain. Versi
        sebelumnya mengambil kain terakhir apa pun motifnya, sehingga
        "singabarong laku" bisa terpasang pada megamendung yang kebetulan
        sedang dikerjakan. Salah kain berarti salah hari kerja, dan itu
        merusak seluruh perhitungan untung per hari.
        """
        calon = [k for k in self.kain if k.status != "terjual"]
        if produk:
            cocok = [k for k in calon if k.produk == produk]
            return cocok[-1] if cocok else None
        return calon[-1] if calon else None

    def catat(self, e: dict, hari_ini: date | None = None) -> dict:
        """Terapkan satu kejadian hasil ekstraksi. Kembalikan ringkasan dampak."""
        hari_ini = hari_ini or date.today()
        jenis = e.get("jenis")
        produk = e.get("produk")
        dampak: dict = {"jenis": jenis}

        if jenis == "MULAI":
            k = Kain(produk=produk or "tanpa nama", mulai=hari_ini)
            self.kain.append(k)
            dampak["kain"] = k

        elif jenis == "SELESAI":
            k = self._kain_aktif(produk)
            if k:
                k.selesai = hari_ini
                dampak["kain"] = k

        elif jenis == "JUAL":
            k = self._kain_aktif(produk)
            if k is None:                      # terjual tanpa pernah dicatat mulai
                k = Kain(produk=produk or "tanpa nama",
                         mulai=hari_ini - timedelta(days=int(B.ARTISAN_DAY_PER_KAIN)),
                         selesai=hari_ini)
                self.kain.append(k)
            k.selesai = k.selesai or hari_ini
            k.harga_jual = e.get("harga")
            dampak["kain"] = k
            dampak["hasil"] = k.hasil(self.p)

        elif jenis in ("BELI", "BAYAR"):
            self.pengeluaran.append({
                "tanggal": hari_ini,
                "kategori": e.get("kategori") or e.get("item") or "lain",
                "nominal": (e.get("harga") or 0) * (e.get("qty") or 1),
            })
            dampak["nominal"] = self.pengeluaran[-1]["nominal"]

        self.riwayat.append({"tanggal": hari_ini, **e})
        return dampak

    # -------------------------------------------------------------- diagnosis
    def artisan_day_terpakai(self, sejak: date | None = None) -> float:
        sejak = sejak or (date.today() - timedelta(days=7))
        return sum(k.hari_kerja for k in self.kain
                   if k.mulai and k.mulai >= sejak)

    def diagnosa(self) -> dict:
        """Tentukan kendala yang sedang MENGIKAT sebelum memilih tuas apa pun.

        Inilah yang membedakan CANTING dari penasihat yang asal menyuruh
        menaikkan harga: kalau slot kosong, menaikkan harga justru mematikan.
        """
        kapasitas = (self.p or B.BAKU).kapasitas_minggu
        terpakai = self.artisan_day_terpakai()
        utilisasi = terpakai / kapasitas if kapasitas else 0.0
        kosong = max(0.0, kapasitas - terpakai)

        # Kalimat saran ditulis sebagaimana orang berbicara, bukan sebagai
        # istilah. "Tuas" dan "order rugi" benar secara teori, tetapi pemilik
        # usaha batik tidak memakai kata-kata itu.
        if utilisasi >= 0.85:
            kendala = "kapasitas"
            tuas = ("harga boleh dinaikkan, dan kerjakan dulu motif yang "
                    "untungnya paling besar per hari")
        else:
            kendala = "permintaan"
            tuas = ("tahan dulu harganya, jangan terima pesanan yang harganya "
                    "di bawah biaya, dan kerjakan motif yang cepat selesai")

        return {
            "kendala": kendala,
            "tuas": tuas,
            "utilisasi": utilisasi,
            "slot_kosong": kosong,
            "kapasitas": kapasitas,
            "terpakai": terpakai,
        }

    # ------------------------------------------------------------- statistik
    def statistik(self) -> dict:
        terjual = [k for k in self.kain if k.status == "terjual"]
        hasil = [k.hasil(self.p) for k in terjual]
        rugi = [h for h in hasil if h and h["rugi"]]

        total_margin = sum(h["margin"] for h in hasil if h)
        total_hari = sum(k.hari_kerja for k in terjual)

        return {
            "jumlah_kain": len(self.kain),
            "jumlah_terjual": len(terjual),
            "sedang_dikerjakan": len([k for k in self.kain if k.status == "dikerjakan"]),
            "omzet": sum(k.harga_jual for k in terjual if k.harga_jual),
            "laba": total_margin,
            "untung_per_hari": total_margin / total_hari if total_hari else 0.0,
            "porsi_rugi": len(rugi) / len(terjual) if terjual else 0.0,
            "jumlah_rugi": len(rugi),
            "pengeluaran": sum(p["nominal"] for p in self.pengeluaran),
        }

    def peringkat_motif(self) -> list[tuple[str, float, int]]:
        """Motif diurutkan menurut untung per hari kerja — bukan menurut harga.

        Di sinilah kain Rp1 juta yang butuh 3 minggu bisa kalah dari kain
        Rp600 ribu yang selesai 5 hari.
        """
        kumpul: dict[str, list[float]] = {}
        for k in self.kain:
            h = k.hasil(self.p)
            if h:
                kumpul.setdefault(k.produk, []).append(h["untung_per_hari"])
        hasil = [(nama, sum(v) / len(v), len(v)) for nama, v in kumpul.items()]
        return sorted(hasil, key=lambda r: -r[1])


    # ------------------------------------------------------ SIMPAN & PULIHKAN
    def ke_kamus(self) -> dict:
        """Ubah seluruh isi buku menjadi struktur yang bisa disimpan.

        Tanggal ditulis sebagai teks ISO agar berkasnya tetap terbaca manusia —
        pemilik usaha harus bisa membuka cadangannya sendiri dan melihat bahwa
        itu memang datanya, bukan berkas gelap yang tak bisa diperiksa.
        """
        p = self.p or B.BAKU
        return {
            "versi": 1,
            "disimpan": date.today().isoformat(),
            "kain": [
                {
                    "produk": k.produk,
                    "mulai": k.mulai.isoformat() if k.mulai else None,
                    "selesai": k.selesai.isoformat() if k.selesai else None,
                    "harga_jual": k.harga_jual,
                }
                for k in self.kain
            ],
            "pengeluaran": [
                {**x, "tanggal": x["tanggal"].isoformat()
                 if hasattr(x.get("tanggal"), "isoformat") else x.get("tanggal")}
                for x in self.pengeluaran
            ],
            "kalibrasi": {
                "bahan": p.bahan,
                "pewarna_energi": p.pewarna_energi,
                "overhead": p.overhead,
                "upah_per_hari": p.upah_per_hari,
                "artisan_day_per_kain": p.artisan_day_per_kain,
                "kapasitas_minggu": p.kapasitas_minggu,
            },
        }

    @staticmethod
    def dari_kamus(data: dict) -> tuple["Buku", B.Parameter]:
        """Pulihkan buku beserta kalibrasinya. Kembalikan (buku, parameter)."""
        def tgl(s):
            return date.fromisoformat(s) if s else None

        b = Buku()
        for k in data.get("kain", []):
            b.kain.append(Kain(
                produk=k.get("produk") or "tanpa nama",
                mulai=tgl(k.get("mulai")),
                selesai=tgl(k.get("selesai")),
                harga_jual=k.get("harga_jual"),
            ))
        for x in data.get("pengeluaran", []):
            y = dict(x)
            if isinstance(y.get("tanggal"), str):
                y["tanggal"] = tgl(y["tanggal"])
            b.pengeluaran.append(y)

        kal = data.get("kalibrasi") or {}
        p = B.BAKU.ubah(**{k: v for k, v in kal.items()
                           if k in B.BAKU.__dataclass_fields__})
        return b.pakai(p), p


def buku_contoh() -> Buku:
    """Riwayat awal supaya papan angka tidak kosong saat pertama dibuka.

    Angkanya dipilih agar mencerminkan temuan proposal: sebagian order memang
    terjual di bawah biaya penuh.
    """
    b = Buku()
    hari_ini = date.today()
    riwayat = [
        ("megamendung", 26, 5, 850_000),
        ("wadasan",     22, 7, 620_000),
        ("sogan",       18, 4, 520_000),   # di bawah biaya penuh
        ("megamendung", 14, 6, 900_000),
        ("singabarong", 10, 9, 1_000_000),
        ("sogan",        6, 4, 480_000),   # di bawah biaya penuh
    ]
    for produk, lalu, lama, harga in riwayat:
        mulai = hari_ini - timedelta(days=lalu)
        b.kain.append(Kain(produk=produk, mulai=mulai,
                           selesai=mulai + timedelta(days=lama),
                           harga_jual=harga))
    b.kain.append(Kain(produk="megamendung", mulai=hari_ini - timedelta(days=3)))
    return b


if __name__ == "__main__":
    b = buku_contoh()
    s = b.statistik()
    print(f"Kain terjual        {s['jumlah_terjual']}")
    print(f"Omzet               {B.rupiah(s['omzet'])}")
    print(f"Laba                {B.rupiah(s['laba'])}")
    print(f"Untung/hari kerja   {B.rupiah(s['untung_per_hari'])}")
    print(f"Order di bawah biaya {s['porsi_rugi']:.0%} ({s['jumlah_rugi']} kain)")
    d = b.diagnosa()
    print(f"\nKendala             {d['kendala']} (utilisasi {d['utilisasi']:.0%})")
    print(f"Tuas                {d['tuas']}")
    print("\nPeringkat motif menurut untung per hari kerja:")
    for nama, upd, n in b.peringkat_motif():
        print(f"  {nama:14} {B.rupiah(upd):>12} /hari  ({n} kain)")
