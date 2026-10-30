import os
import sys
import re
import calendar
from datetime import date, datetime
from flask import Flask
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from config import Config
from models import (
    db,
    Siswa,
    TagihanSiswa,
    RiwayatPembayaran,
    DetailPengajuanPembayaran,
)

# =========================================================
# KONFIGURASI
# =========================================================

app = Flask(__name__)
app.config.from_object(Config)

DATABASE_URI = app.config.get("SQLALCHEMY_DATABASE_URI", "")
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# =========================================================
# PENGAMAN DATABASE LOKAL
# =========================================================

if not DATABASE_URI.startswith("sqlite:///"):
    print("\nPERBAIKAN DIBATALKAN!")
    print("Script ini hanya boleh dijalankan pada database SQLite lokal.")
    print("Periksa DATABASE_URL di file .env Anda.")
    sys.exit(1)

database_path = DATABASE_URI.replace("sqlite:///", "", 1)

if not os.path.isabs(database_path):
    database_path = os.path.abspath(
        os.path.join(BASE_DIR, database_path)
    )

# Jika database berada di folder instance
if not os.path.isfile(database_path):
    database_instance = os.path.join(
        BASE_DIR,
        "instance",
        os.path.basename(database_path)
    )

    if os.path.isfile(database_instance):
        database_path = database_instance

if not database_path.startswith(BASE_DIR + os.sep):
    print("\nPERBAIKAN DIBATALKAN!")
    print("Lokasi database berada di luar folder proyek.")
    print(f"Lokasi database: {database_path}")
    sys.exit(1)

if not os.path.isfile(database_path):
    print("\nPERBAIKAN DIBATALKAN!")
    print("File database lokal tidak ditemukan.")
    print(f"Lokasi: {database_path}")
    sys.exit(1)

# =========================================================
# PARSER BULAN TAGIHAN
# =========================================================

NAMA_BULAN = {
    "januari": 1, "jan": 1,
    "februari": 2, "feb": 2,
    "maret": 3, "mar": 3,
    "april": 4, "apr": 4,
    "mei": 5,
    "juni": 6, "jun": 6,
    "juli": 7, "jul": 7,
    "agustus": 8, "agu": 8, "ags": 8,
    "september": 9, "sep": 9,
    "oktober": 10, "okt": 10,
    "november": 11, "nov": 11,
    "desember": 12, "des": 12,
}


def bulan_dari_tagihan(tagihan):
    """
    Membaca bulan dan tahun dari TagihanSiswa.bulan.
    Mendukung:
    Januari 2027
    Jan 2027
    2027-01
    2027/01
    01-2027
    01/2027
    """

    nilai = str(tagihan.bulan or "").strip().lower()

    if not nilai:
        return None

    # Format Januari 2027 / Jan 2027
    cocok = re.match(r"^([a-z]+)\s+(\d{4})$", nilai)

    if cocok:
        bulan = NAMA_BULAN.get(cocok.group(1))
        tahun = int(cocok.group(2))

        if bulan:
            return date(tahun, bulan, 1)

    # Format 2027-01 atau 2027/01
    cocok = re.match(r"^(\d{4})[-/](\d{1,2})$", nilai)

    if cocok:
        tahun = int(cocok.group(1))
        bulan = int(cocok.group(2))

        if 1 <= bulan <= 12:
            return date(tahun, bulan, 1)

    # Format 01-2027 atau 01/2027
    cocok = re.match(r"^(\d{1,2})[-/](\d{4})$", nilai)

    if cocok:
        bulan = int(cocok.group(1))
        tahun = int(cocok.group(2))

        if 1 <= bulan <= 12:
            return date(tahun, bulan, 1)

    # Jika hanya nama bulan, tahun diambil dari tahun pelajaran
    bulan = NAMA_BULAN.get(nilai)

    if bulan:
        kode_tp = str(tagihan.tahun_pelajaran or "")
        cocok = re.search(r"(\d{4})/(\d{4})", kode_tp)

        if cocok:
            tahun_awal = int(cocok.group(1))
            tahun_akhir = int(cocok.group(2))

            tahun = tahun_awal if bulan >= 7 else tahun_akhir
            return date(tahun, bulan, 1)

    return None


# =========================================================
# CEK JENIS TAGIHAN BULANAN
# =========================================================

POLA_BULANAN = {
    "bulanan",
    "per_bulan",
    "per bulan",
    "monthly",
    "setiap_bulan",
    "setiap bulan",
}


def merupakan_tagihan_bulanan(tagihan):
    if not tagihan.jenis:
        return False

    pola = str(tagihan.jenis.pola_waktu or "").strip().lower()
    return pola in POLA_BULANAN


# =========================================================
# CEK APAKAH TAGIHAN AMAN DIHAPUS
# =========================================================

def aman_dihapus(tagihan):
    if float(tagihan.sudah_dibayar or 0) > 0:
        return False, "Sudah ada pembayaran"

    status = str(tagihan.status or "").strip().lower()

    if status in {"lunas", "paid", "dibayar"}:
        return False, "Status tagihan sudah lunas"

    riwayat = RiwayatPembayaran.query.filter_by(
        tagihan_id=tagihan.id
    ).first()

    if riwayat:
        return False, "Memiliki riwayat pembayaran"

    detail = DetailPengajuanPembayaran.query.filter_by(
        tagihan_id=tagihan.id
    ).first()

    if detail:
        return False, "Terhubung dengan pengajuan pembayaran"

    return True, "Aman dihapus"


# =========================================================
# PROSES PERBAIKAN
# =========================================================

def jalankan_perbaikan(mode_execute=False):

    total_diperiksa = 0
    total_dihapus = 0
    total_dilewati = 0

    daftar_hapus = []

    print("\n==============================================")
    print("     PERBAIKAN TAGIHAN SISWA")
    print("==============================================")
    print(f"Database lokal: {database_path}")
    print("Mode:", "EKSEKUSI" if mode_execute else "SIMULASI")
    print("----------------------------------------------")

    siswa_list = Siswa.query.all()

    for siswa in siswa_list:

        if not siswa.tanggal_diterima:
            continue

        tanggal_diterima = siswa.tanggal_diterima

        if isinstance(tanggal_diterima, datetime):
            tanggal_diterima = tanggal_diterima.date()

        bulan_mulai = date(
            tanggal_diterima.year,
            tanggal_diterima.month,
            1
        )

        tagihan_list = TagihanSiswa.query.filter_by(
            siswa_id=siswa.id
        ).all()

        for tagihan in tagihan_list:

            total_diperiksa += 1

            if not merupakan_tagihan_bulanan(tagihan):
                continue

            bulan_tagihan = bulan_dari_tagihan(tagihan)

            if not bulan_tagihan:
                total_dilewati += 1
                print(
                    f"[LEWATI] {siswa.nama} | "
                    f"Tagihan #{tagihan.id} | "
                    f"Bulan tidak dikenali: {tagihan.bulan}"
                )
                continue

            # Tagihan sebelum bulan diterima siswa
            if bulan_tagihan >= bulan_mulai:
                continue

            aman, alasan = aman_dihapus(tagihan)

            if not aman:
                total_dilewati += 1
                print(
                    f"[TIDAK DIHAPUS] {siswa.nama} | "
                    f"{tagihan.bulan} | {alasan}"
                )
                continue

            daftar_hapus.append(tagihan)

            print(
                f"[TARGET HAPUS] {siswa.nama} | "
                f"NIS: {siswa.nis} | "
                f"Tagihan: {tagihan.bulan} | "
                f"Diterima: {tanggal_diterima}"
            )

    print("\n==============================================")
    print("RINGKASAN")
    print("==============================================")
    print(f"Total tagihan diperiksa : {total_diperiksa}")
    print(f"Total kandidat dihapus  : {len(daftar_hapus)}")
    print(f"Total dilewati          : {total_dilewati}")

    if not mode_execute:
        print("\nSIMULASI SELESAI.")
        print("Belum ada data yang dihapus.")
        print("Jika daftar di atas sudah benar, jalankan:")
        print("python perbaikan.py --execute")
        return

    if not daftar_hapus:
        print("\nTidak ada tagihan yang perlu dihapus.")
        return

    print("\nPERHATIAN!")
    print("Tagihan yang tercantum di atas akan dihapus.")
    konfirmasi = input(
        f"Ketik HAPUS {len(daftar_hapus)} untuk melanjutkan: "
    )

    if konfirmasi != f"HAPUS {len(daftar_hapus)}":
        print("\nDIBATALKAN. Tidak ada data yang dihapus.")
        return

    try:
        for tagihan in daftar_hapus:
            db.session.delete(tagihan)
            total_dihapus += 1

        db.session.commit()

        print("\nPERBAIKAN BERHASIL!")
        print(f"Total tagihan dihapus: {total_dihapus}")

    except SQLAlchemyError as e:
        db.session.rollback()
        print("\nGAGAL MELAKUKAN PERBAIKAN.")
        print(f"Kesalahan: {e}")


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    mode_execute = "--execute" in sys.argv

    with app.app_context():
        db.init_app(app)

        jalankan_perbaikan(mode_execute)