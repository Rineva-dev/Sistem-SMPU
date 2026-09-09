# ==============================================
# HAPUS SEMUA DATA ABSENSI GURU
# Jalankan: python hapus_absensi.py
# Database: sekolah.db
# ==============================================

from datetime import date
import sys
import os

# Tambahkan path supaya bisa import dari app & models
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import AbsensiGuru

hari_ini = date.today()

with app.app_context():
    # Hitung jumlah data sebelum dihapus
    jumlah = AbsensiGuru.query.count()

    if jumlah == 0:
        print("✅ TIDAK ADA data absensi di database.")
        sys.exit(0)

    print(f"⚠️ Akan MENGHAPUS SEMUA {jumlah} data absensi guru...")
    print("📅 Termasuk data tanggal:", hari_ini)
    print()

    # Hapus SEMUA
    AbsensiGuru.query.delete()
    db.session.commit()

    print("✅ ✅ ✅ BERHASIL!")
    print(f"🗑️ Semua {jumlah} data absensi sudah DIHAPUS dari sekolah.db")
    print()
    print("👉 Sekarang halaman absensi sudah bersih.")