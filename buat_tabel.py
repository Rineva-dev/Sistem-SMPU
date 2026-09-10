from app import app, db
from models import TagihanSiswa, Siswa, JenisPembayaran, RiwayatPembayaran
from datetime import date

with app.app_context():
    # ==================================================
    # ✅ TAMBAH KOLOM jam_tutup_absensi
    # ==================================================
    print()
    print("="*70)
    print("🔧 MENAMBAHKAN KOLOM jam_tutup_absensi")
    print("="*70)
    print()

    from sqlalchemy import inspect
    inspeksi = inspect(db.engine)
    kolom_pengaturan = [c['name'] for c in inspeksi.get_columns('pengaturan_jam_kerja')]

    if 'jam_tutup_absensi' not in kolom_pengaturan:
        print("⚠️ Kolom jam_tutup_absensi belum ada → menambahkan sekarang...")
        db.session.execute(db.text("ALTER TABLE pengaturan_jam_kerja ADD COLUMN jam_tutup_absensi TIME;"))
        db.session.commit()
        print("✅ Kolom jam_tutup_absensi berhasil ditambahkan!")
    else:
        print("✅ Kolom jam_tutup_absensi SUDAH ADA ✅")

    print()

    # ==================================================
    # ✅ Lanjutan kode Anda yang sudah ada...
    # ==================================================
    print("="*70)
    print("🔧 LANGKAH 1: PASTIKAN STRUKTUR & RELASI TERBARU")
    print("="*70)
    print()