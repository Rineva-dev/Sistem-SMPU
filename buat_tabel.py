from app import app, db
from models import TagihanSiswa, Siswa, JenisPembayaran, RiwayatPembayaran
from datetime import date

with app.app_context():
    print("="*70)
    print("🔧 LANGKAH 1: PASTIKAN STRUKTUR & RELASI TERBARU")
    print("="*70)
    print()
    # Pastikan kolom tanggal_lunas sudah ada
    from sqlalchemy import inspect
    inspeksi = inspect(db.engine)
    kolom_tagihan = [c['name'] for c in inspeksi.get_columns('tagihan_siswa')]
    if 'tanggal_lunas' not in kolom_tagihan:
        print("⚠️ Kolom tanggal_lunas belum ada → menambahkan sekarang...")
        db.session.execute(db.text("ALTER TABLE tagihan_siswa ADD COLUMN tanggal_lunas DATE;"))
        db.session.commit()
        print("✅ Kolom tanggal_lunas berhasil ditambahkan!")
    else:
        print("✅ Kolom tanggal_lunas sudah ada ✅")
    # Pastikan relasi riwayat berfungsi
    cek_tagihan_contoh = TagihanSiswa.query.first()
    if hasattr(cek_tagihan_contoh, 'riwayat'):
        print("✅ Relasi riwayat pembayaran TERDAFTAR dengan benar ✅")
    else:
        print("⚠️ Relasi riwayat BELUM TERBACA → pastikan model sudah di-simpan ulang!")
    print()

    # ==================================================
    # ✅ PROSES KEDUA SISWA BERDASARKAN NISN
    # ==================================================
    print("="*70)
    print("🔧 LANGKAH 2: HAPUS SEMUA PEMBAYARAN SISWA")
    print("="*70)
    print()

    # Daftar NISN yang akan dibersihkan
    daftar_nisn = ["0125769192", "0126205123"]

    total_tagihan_diatur = 0
    total_riwayat_dihapus = 0

    for nisn_target in daftar_nisn:
        print("-"*70)
        print(f"👤 MEMPROSES NISN: {nisn_target}")
        print("-"*70)

        siswa_target = Siswa.query.filter_by(nisn=nisn_target).first()
        if not siswa_target:
            print(f"⚠️ Siswa dengan NISN {nisn_target} TIDAK DITEMUKAN!")
            print()
            continue

        print(f"✅ Nama Siswa: {siswa_target.nama}")
        print()

        daftar_tagihan = TagihanSiswa.query.filter_by(siswa_id=siswa_target.id).order_by(TagihanSiswa.id).all()
        if not daftar_tagihan:
            print("ℹ️ Tidak ada tagihan untuk siswa ini.")
            print()
            continue

        for tagihan in daftar_tagihan:
            # ✅ DIUBAH: tidak pakai tagihan.nama (yang menyebabkan error)
            print(f"🔄 Tagihan ID {tagihan.id}")
            print(f"   Sebelum: Dibayar Rp {tagihan.sudah_dibayar or 0:,} | {tagihan.status} | {len(tagihan.riwayat)} riwayat")

            # Hapus riwayat pembayaran lama jika ada
            if tagihan.riwayat:
                jumlah = len(tagihan.riwayat)
                print(f"   ⚠️ Menghapus {jumlah} riwayat pembayaran...")
                for r in tagihan.riwayat:
                    db.session.delete(r)
                total_riwayat_dihapus += jumlah

            # Kembalikan ke semula: belum dibayar
            tagihan.sudah_dibayar = 0
            tagihan.status = 'Belum Lunas'
            tagihan.tanggal_lunas = None
            total_tagihan_diatur += 1

            print(f"   ✅ Sesudah: Dibayar Rp 0 | Belum Lunas | Tanggal Lunas -")
            print()

    db.session.commit()
    print("💾 Semua perubahan tersimpan!")
    print()

    # ==================================================
    # 📋 TAMPILKAN HASIL AKHIR
    # ==================================================
    print("="*70)
    print("📋 REKAP HASIL AKHIR")
    print("="*70)
    print()

    for nisn_target in daftar_nisn:
        siswa = Siswa.query.filter_by(nisn=nisn_target).first()
        if not siswa:
            continue
        print(f"👤 {siswa.nama} (NISN: {nisn_target})")
        print(f"{'ID':<4} | {'Nominal':<16} | {'Sudah Dibayar':<16} | {'Sisa':<16} | {'Status':<15} | {'Kali Bayar'}")
        print("-"*70)
        daftar = TagihanSiswa.query.filter_by(siswa_id=siswa.id).order_by(TagihanSiswa.id).all()
        for t in daftar:
            print(f"{t.id:<4} | Rp {str(t.nominal_tagihan or 0):<13} | Rp {str(t.sudah_dibayar or 0):<13} | Rp {str(t.sisa_tagihan):<13} | {t.status:<15} | {t.jumlah_kali_bayar} kali")
        print()

    print("="*70)
    print(f"✅ SELESAI! {total_tagihan_diatur} tagihan dikembalikan, {total_riwayat_dihapus} riwayat dihapus.")
    print("="*70)