from app import app, db
from models import TagihanSiswa, Siswa, JenisPembayaran, RiwayatPembayaran
from datetime import date

with app.app_context():
    # ==================================================
    # ✅ TAMBAH SEMUA KOLOM PENGATURAN JAM KERJA
    # ==================================================
    print()
    print("="*70)
    print("🔧 MENAMBAHKAN KOLOM TABEL pengaturan_jam_kerja")
    print("="*70)
    print()

    from sqlalchemy import inspect
    inspeksi = inspect(db.engine)
    kolom_semua = [c['name'] for c in inspeksi.get_columns('pengaturan_jam_kerja')]

    # Daftar kolom yang perlu ditambahkan
    daftar_kolom = [
        ('batas_terlambat',        'TIME'),
        ('jam_tutup_absensi',       'TIME'),
        ('batas_terlambat_jumat',   'TIME'),
        ('jam_tutup_absensi_jumat', 'TIME'),
    ]

    for nama_kolom, tipe in daftar_kolom:
        if nama_kolom not in kolom_semua:
            print(f"⚠️ Kolom {nama_kolom} belum ada → menambahkan sekarang...")
            db.session.execute(db.text(f"ALTER TABLE pengaturan_jam_kerja ADD COLUMN {nama_kolom} {tipe};"))
            db.session.commit()
            print(f"✅ Kolom {nama_kolom} berhasil ditambahkan!")
        else:
            print(f"✅ Kolom {nama_kolom} SUDAH ADA ✅")
        print()

    # ==================================================
    # ✅ LANJUTAN KODE YANG SUDAH ADA...
    # ==================================================
    print("="*70)
    print("🔧 LANGKAH 1: PASTIKAN STRUKTUR & RELASI TERBARU")
    print("="*70)
    print()
    # ... sisa kode kamu di sini ...