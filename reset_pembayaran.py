
from app import app
from collections import defaultdict
from datetime import date
from sqlalchemy import func
import re

# Sesuaikan import ini dengan lokasi model yang digunakan proyekmu.
from models import TahunPelajaran, TagihanSiswa, RiwayatPembayaran


NAMA_BULAN = {
    "januari": 1, "februari": 2, "maret": 3,
    "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "agustus": 8, "september": 9,
    "oktober": 10, "november": 11, "desember": 12,
}

# Tetap False untuk pemeriksaan pertama.
# Jangan ubah menjadi True sebelum laporan diverifikasi.
TERAPKAN_PERUBAHAN = True


def baca_periode(teks):
    if not teks:
        return None

    cocok = re.fullmatch(
        r"\s*([A-Za-z]+)\s+(\d{4})\s*",
        teks
    )
    if not cocok:
        return None

    bulan = NAMA_BULAN.get(cocok.group(1).lower())
    tahun = int(cocok.group(2))

    if bulan is None:
        return None

    return bulan, tahun


def cari_kode_tp(bulan, tahun):
    tanggal_acuan = date(tahun, bulan, 15)

    data = TahunPelajaran.query.filter(
        TahunPelajaran.tanggal_mulai <= tanggal_acuan,
        TahunPelajaran.tanggal_selesai >= tanggal_acuan,
    ).all()

    semester = [
        tp for tp in data
        if re.search(r"-[12]$", tp.kode or "")
    ]

    if len(semester) == 1:
        return semester[0].kode

    if len(semester) > 1:
        return None

    if len(data) == 1:
        return data[0].kode

    return None


def jalankan():
    with app.app_context():
        perubahan = []
        masalah = []
        grup_target = defaultdict(list)

        tagihan_bulanan = TagihanSiswa.query.filter(
            TagihanSiswa.bulan.isnot(None)
        ).order_by(TagihanSiswa.id.asc()).all()

        for tagihan in tagihan_bulanan:
            periode = baca_periode(tagihan.bulan)

            if not periode:
                continue

            bulan, tahun = periode
            kode_benar = cari_kode_tp(bulan, tahun)

            # Abaikan tagihan yang sudah sesuai.
            if kode_benar == tagihan.tahun_pelajaran:
                continue

            if not kode_benar:
                masalah.append(
                    f"ID {tagihan.id}: kode TP tidak dapat ditentukan "
                    f"secara unik untuk {tagihan.bulan}"
                )
                continue

            # Periksa apakah sudah ada tagihan lain dengan
            # siswa, jenis pembayaran, bulan, dan kode tujuan sama.
            bentrok = TagihanSiswa.query.filter(
                TagihanSiswa.id != tagihan.id,
                TagihanSiswa.siswa_id == tagihan.siswa_id,
                TagihanSiswa.jenis_pembayaran_id
                    == tagihan.jenis_pembayaran_id,
                TagihanSiswa.bulan == tagihan.bulan,
                TagihanSiswa.tahun_pelajaran == kode_benar,
            ).first()

            if bentrok:
                masalah.append(
                    f"ID {tagihan.id}: bentrok dengan ID {bentrok.id}; "
                    f"keduanya untuk {tagihan.bulan} dan kode {kode_benar}"
                )
                continue

            # Jangan otomatis mengoreksi tagihan yang sudah memiliki
            # pembayaran. Periksa manual terlebih dahulu.
            jumlah_riwayat = RiwayatPembayaran.query.filter_by(
                tagihan_id=tagihan.id
            ).count()

            if jumlah_riwayat > 0 or (tagihan.sudah_dibayar or 0) > 0:
                masalah.append(
                    f"ID {tagihan.id}: memiliki riwayat pembayaran "
                    f"atau nominal pembayaran; perlu pemeriksaan manual"
                )
                continue

            perubahan.append(
                (tagihan, tagihan.tahun_pelajaran, kode_benar)
            )

        print("=" * 100)
        print("LAPORAN KOREKSI KODE TAHUN PELAJARAN")
        print(
            "MODE:",
            "TERAPKAN PERUBAHAN" if TERAPKAN_PERUBAHAN
            else "SIMULASI — DATABASE TIDAK DIUBAH"
        )
        print("=" * 100)

        for tagihan, kode_lama, kode_baru in perubahan:
            print(
                f"ID={tagihan.id} | Siswa={tagihan.siswa_id} | "
                f"Bulan={tagihan.bulan} | "
                f"{kode_lama} -> {kode_baru} | "
                f"Nominal={tagihan.nominal_tagihan} | "
                f"Sudah dibayar={tagihan.sudah_dibayar}"
            )

        print("\nTAGIHAN YANG PERLU PEMERIKSAAN MANUAL")
        for pesan in masalah:
            print("-", pesan)

        print("\nRINGKASAN")
        print("Tagihan aman untuk dikoreksi:", len(perubahan))
        print("Kasus yang perlu diperiksa:", len(masalah))

        if TERAPKAN_PERUBAHAN:
            try:
                for tagihan, kode_lama, kode_baru in perubahan:
                    tagihan.tahun_pelajaran = kode_baru

                db.session.commit()
                print("Perubahan berhasil disimpan.")
            except Exception:
                db.session.rollback()
                raise
        else:
            print("Belum ada perubahan yang disimpan.")


if __name__ == "__main__":
    from app import db
    jalankan()
