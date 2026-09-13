from app import app, db
from models import TagihanSiswa, Siswa, JenisPembayaran, RiwayatPembayaran
from datetime import date

with app.app_context():

    # ==================================================
    # ✅ TAMBAH KOLOM KE TABEL GURU
    #    NIK, GELAR DEPAN, GELAR BELAKANG,
    #    PENDIDIKAN TERAKHIR, STATUS PERNIKAHAN
    # ==================================================

    print()
    print("="*70)
    print("🔧 MENAMBAHKAN KOLOM KE TABEL: guru")
    print("     → NIK, Gelar Depan, Gelar Belakang,")
    print("       Pendidikan Terakhir, Status Pernikahan")
    print("="*70)
    print()

    from sqlalchemy import inspect
    inspeksi = inspect(db.engine)

    # Nama tabel di database (sesuaikan jika berbeda)
    nama_tabel = 'guru'
    kolom_semua = [c['name'] for c in inspeksi.get_columns(nama_tabel)]

    # Daftar kolom yang akan ditambahkan: (nama_kolom, tipe_data)
    daftar_kolom = [
        ('nik',                  'VARCHAR(20)'),
        ('gelar_depan',          'VARCHAR(30)'),
        ('gelar_belakang',       'VARCHAR(50)'),
        ('pendidikan_terakhir',  'VARCHAR(10)'),
        ('status_pernikahan',    'VARCHAR(20)'),
    ]

    for nama_kolom, tipe in daftar_kolom:
        if nama_kolom not in kolom_semua:
            print(f"⚠️ Kolom {nama_kolom} belum ada → menambahkan sekarang...")
            db.session.execute(db.text(f"ALTER TABLE {nama_tabel} ADD COLUMN {nama_kolom} {tipe};"))
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