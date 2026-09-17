from app import app, db
from sqlalchemy import inspect

with app.app_context():
    # ==================================================
    # ✅ TAMBAH KOLOM jenis_khusus KE TABEL jadwal_pelajaran
    # ==================================================
    print()
    print("="*70)
    print("🔧 MENAMBAHKAN KOLOM: jenis_khusus → Tabel jadwal_pelajaran")
    print("="*70)
    print()
    
    inspeksi = inspect(db.engine)
    nama_tabel = 'jadwal_pelajaran'
    kolom_semua = [c['name'] for c in inspeksi.get_columns(nama_tabel)]
    nama_kolom = 'jenis_khusus'
    tipe = 'VARCHAR(20)'  # 'imtaq', 'upacara', atau NULL
    
    if nama_kolom not in kolom_semua:
        print(f"⚠️ Kolom {nama_kolom} belum ada → sedang ditambahkan...")
        db.session.execute(db.text(f"ALTER TABLE {nama_tabel} ADD COLUMN {nama_kolom} {tipe};"))
        db.session.commit()
        print(f"✅ Kolom {nama_kolom} BERHASIL ditambahkan!")
    else:
        print(f"✅ Kolom {nama_kolom} SUDAH ADA — tidak perlu ditambah lagi.")
    
    print()
    print("✅ Selesai! Silakan muat ulang halaman jadwal.")
    print()