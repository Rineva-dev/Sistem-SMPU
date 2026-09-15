from app import app, db
from sqlalchemy import inspect

with app.app_context():
    # ==================================================
    # ✅ TAMBAH KOLOM jam_izin KE TABEL absensi_guru
    # ==================================================
    print()
    print("="*70)
    print("🔧 MENAMBAHKAN KOLOM: jam_izin → Tabel absensi_guru")
    print("="*70)
    print()

    inspeksi = inspect(db.engine)
    nama_tabel = 'absensi_guru'  # ⚠️ Nama tabel yang BENAR
    kolom_semua = [c['name'] for c in inspeksi.get_columns(nama_tabel)]
    nama_kolom = 'jam_izin'
    tipe = 'VARCHAR(5)'  # Sesuai definisi model: format HH:MM

    if nama_kolom not in kolom_semua:
        print(f"⚠️ Kolom {nama_kolom} belum ada → sedang ditambahkan...")
        db.session.execute(db.text(f"ALTER TABLE {nama_tabel} ADD COLUMN {nama_kolom} {tipe};"))
        db.session.commit()
        print(f"✅ Kolom {nama_kolom} BERHASIL ditambahkan!")
    else:
        print(f"✅ Kolom {nama_kolom} SUDAH ADA — tidak perlu ditambah lagi.")

    print()
    print("✅ Selesai! Silakan muat ulang halaman.")
    print()