
"""
PERBAIKAN DATABASE JURNAL MENGAJAR
==================================
- Mendukung SQLite dan PostgreSQL.
- Tidak menghapus database utama.
- Tidak menghapus tabel lain.
- Menghentikan proses jika tabel yang perlu diubah berisi data.
"""

from app import app
from models import db, JurnalMengajar, AbsensiJurnalMengajar

from sqlalchemy import inspect, text


def jumlah_data(nama_tabel):
    """Menghitung jumlah baris dalam tabel."""
    return db.session.execute(
        text(f'SELECT COUNT(*) FROM "{nama_tabel}"')
    ).scalar() or 0


def perbaikan_database():

    print("\n========================================")
    print(" PERBAIKAN TABEL JURNAL MENGAJAR")
    print("========================================\n")

    inspector = inspect(db.engine)

    tabel_jurnal = JurnalMengajar.__tablename__
    tabel_absensi = AbsensiJurnalMengajar.__tablename__

    # Kolom yang seharusnya dimiliki model terbaru
    kolom_jurnal_baru = set(
        JurnalMengajar.__table__.columns.keys()
    )

    kolom_absensi_baru = set(
        AbsensiJurnalMengajar.__table__.columns.keys()
    )

    tabel_ada = set(inspector.get_table_names())

    drop_tables = []

    # ==========================================
    # 1. PERIKSA TABEL JURNAL MENGAJAR
    # ==========================================
    if tabel_jurnal in tabel_ada:

        kolom_lama = set(
            item["name"]
            for item in inspector.get_columns(tabel_jurnal)
        )

        if kolom_lama != kolom_jurnal_baru:

            print("[INFO] Struktur jurnal_mengajar berbeda dari model baru.")

            total = jumlah_data(tabel_jurnal)

            print(f"[INFO] Jumlah data jurnal lama: {total}")

            if total > 0:
                raise RuntimeError(
                    "Tabel jurnal_mengajar masih berisi data. "
                    "Migrasi otomatis dibatalkan agar data tidak hilang. "
                    "Lakukan backup dan migrasi data terlebih dahulu."
                )

            print("[OK] Tabel jurnal lama kosong dan aman untuk dibuat ulang.")

            drop_tables.append(JurnalMengajar.__table__)

        else:
            print("[OK] Struktur jurnal_mengajar sudah sesuai.")

    else:
        print("[INFO] Tabel jurnal_mengajar belum tersedia.")

    # ==========================================
    # 2. PERIKSA TABEL ABSENSI JURNAL
    # ==========================================
    if tabel_absensi in tabel_ada:

        kolom_lama = set(
            item["name"]
            for item in inspector.get_columns(tabel_absensi)
        )

        if kolom_lama != kolom_absensi_baru:

            print(
                "[INFO] Struktur absensi_jurnal_mengajar "
                "berbeda dari model baru."
            )

            total = jumlah_data(tabel_absensi)

            print(f"[INFO] Jumlah data absensi lama: {total}")

            if total > 0:
                raise RuntimeError(
                    "Tabel absensi_jurnal_mengajar masih berisi data. "
                    "Migrasi otomatis dibatalkan agar data tidak hilang."
                )

            print("[OK] Tabel absensi kosong dan aman untuk dibuat ulang.")

            drop_tables.append(
                AbsensiJurnalMengajar.__table__
            )

        else:
            print("[OK] Struktur absensi_jurnal_mengajar sudah sesuai.")

    else:
        print("[INFO] Tabel absensi_jurnal_mengajar belum tersedia.")

    # ==========================================
    # 3. JIKA TABEL JURNAL AKAN DIBUAT ULANG
    #    TABEL ABSENSI JUGA PERLU DIPERIKSA
    # ==========================================
    jurnal_perlu_dibuat_ulang = any(
        table.name == tabel_jurnal
        for table in drop_tables
    )

    if jurnal_perlu_dibuat_ulang and tabel_absensi in tabel_ada:

        total_absensi = jumlah_data(tabel_absensi)

        if total_absensi > 0:
            raise RuntimeError(
                "Tabel absensi masih berisi data dan memiliki "
                "relasi ke jurnal. Perbaikan dibatalkan."
            )

        if not any(
            table.name == tabel_absensi
            for table in drop_tables
        ):
            drop_tables.append(
                AbsensiJurnalMengajar.__table__
            )

    # ==========================================
    # 4. HAPUS HANYA TABEL YANG KOSONG
    #    DAN STRUKTURNYA TIDAK SESUAI
    # ==========================================
    if drop_tables:

        print("\n[PROSES] Menghapus tabel lama yang kosong...")

        # Hapus hanya tabel yang memang perlu diperbaiki.
        # Menggunakan SQLAlchemy Table.drop(), bukan db.drop_all().
        for table in reversed(drop_tables):
            table.drop(bind=db.engine, checkfirst=True)
            print(f"[OK] Tabel {table.name} berhasil dihapus.")

        print("[OK] Seluruh tabel lama berhasil dihapus.")

    # ==========================================
    # 5. BUAT TABEL SESUAI MODEL TERBARU
    # ==========================================
    print("\n[PROSES] Memeriksa dan membuat tabel baru...")

    db.create_all()

    # ==========================================
    # 6. VERIFIKASI HASIL
    # ==========================================
    inspector = inspect(db.engine)

    tabel_akhir = set(inspector.get_table_names())

    if tabel_jurnal not in tabel_akhir:
        raise RuntimeError(
            "Tabel jurnal_mengajar gagal dibuat."
        )

    if tabel_absensi not in tabel_akhir:
        raise RuntimeError(
            "Tabel absensi_jurnal_mengajar gagal dibuat."
        )

    kolom_jurnal_akhir = set(
        item["name"]
        for item in inspector.get_columns(tabel_jurnal)
    )

    kolom_absensi_akhir = set(
        item["name"]
        for item in inspector.get_columns(tabel_absensi)
    )

    if kolom_jurnal_akhir != kolom_jurnal_baru:
        raise RuntimeError(
            "Verifikasi struktur jurnal_mengajar gagal."
        )

    if kolom_absensi_akhir != kolom_absensi_baru:
        raise RuntimeError(
            "Verifikasi struktur absensi_jurnal_mengajar gagal."
        )

    print("\n========================================")
    print(" PERBAIKAN DATABASE BERHASIL")
    print("========================================")
    print("[OK] jurnal_mengajar")
    print("[OK] absensi_jurnal_mengajar")
    print("[OK] Struktur tabel sesuai dengan model.")
    print("[OK] Database siap digunakan.")
    print("========================================\n")


if __name__ == "__main__":

    with app.app_context():

        try:
            perbaikan_database()

        except Exception as e:
            db.session.rollback()

            print("\n[ERROR] PERBAIKAN DATABASE GAGAL")
            print(str(e))

            raise

        finally:
            db.session.remove()
