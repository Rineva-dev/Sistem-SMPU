
import os
import sqlite3
from datetime import datetime

from app import app
from models import db, Siswa, JenisPembayaran, TagihanSiswa


NISN_TARGET = "0123456789"
ID_TARIF_SEMESTER_1 = 5
ID_TARIF_SEMESTER_2 = 6

with app.app_context():
    # 1. Pastikan database menggunakan SQLite.
    driver = db.engine.url.drivername

    if not driver.startswith("sqlite"):
        raise RuntimeError(
            f"Database menggunakan {driver}, bukan SQLite. "
            "Hentikan proses dan buat backup sesuai jenis database."
        )

    # 2. Buat backup database sebelum perubahan.
    nama_backup = (
        "backup_sebelum_perbaikan_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".db"
    )

    koneksi_asal = db.engine.raw_connection()

    try:
        with sqlite3.connect(nama_backup) as koneksi_backup:
            koneksi_asal.backup(koneksi_backup)
    finally:
        koneksi_asal.close()

    print(f"Backup dibuat: {os.path.abspath(nama_backup)}")

    # 3. Cari siswa yang akan diperbaiki.
    siswa = Siswa.query.filter_by(nisn=NISN_TARGET).first()

    if not siswa:
        raise RuntimeError("Siswa target tidak ditemukan.")

    # 4. Pastikan tarif sesuai dengan yang diperiksa.
    tarif1 = db.session.get(
        JenisPembayaran, ID_TARIF_SEMESTER_1
    )
    tarif2 = db.session.get(
        JenisPembayaran, ID_TARIF_SEMESTER_2
    )

    if (
        not tarif1
        or tarif1.kode != "bangunan_s1"
        or tarif1.pola_waktu != "semester_1"
    ):
        raise RuntimeError("Tarif semester 1 tidak sesuai.")

    if (
        not tarif2
        or tarif2.kode != "bangunan_s2"
        or tarif2.pola_waktu != "semester_2"
    ):
        raise RuntimeError("Tarif semester 2 tidak sesuai.")

    # 5. Pastikan kedua tagihan baru sudah benar.
    tagihan1 = TagihanSiswa.query.filter_by(
        siswa_id=siswa.id,
        jenis_pembayaran_id=ID_TARIF_SEMESTER_1,
        bulan=None,
        semester=1,
        tahun_pelajaran="2025/2026-1",
    ).all()

    tagihan2 = TagihanSiswa.query.filter_by(
        siswa_id=siswa.id,
        jenis_pembayaran_id=ID_TARIF_SEMESTER_2,
        bulan=None,
        semester=2,
        tahun_pelajaran="2025/2026-2",
    ).all()

    if len(tagihan1) != 1 or len(tagihan2) != 1:
        raise RuntimeError(
            "Dibatalkan: tagihan yang benar harus masing-masing "
            "tepat satu untuk semester 1 dan semester 2."
        )

    # 6. Cari hanya tagihan lama dengan semester 17 atau 18.
    tagihan_lama = TagihanSiswa.query.filter(
        TagihanSiswa.siswa_id == siswa.id,
        TagihanSiswa.jenis_pembayaran_id == ID_TARIF_SEMESTER_1,
        TagihanSiswa.bulan.is_(None),
        TagihanSiswa.semester.in_([17, 18]),
        TagihanSiswa.tahun_pelajaran == "2025/2026-1",
    ).all()

    if not tagihan_lama:
        raise RuntimeError("Tidak ditemukan tagihan lama yang cocok.")

    # 7. Batalkan semuanya jika ada pembayaran/riwayat terkait.
    for t in tagihan_lama:
        if (t.sudah_dibayar or 0) != 0 or len(t.riwayat) != 0:
            raise RuntimeError(
                f"Dibatalkan: tagihan ID {t.id} memiliki pembayaran "
                "atau riwayat. Perlu pemeriksaan manual."
            )

    print("\nTagihan lama yang akan dihapus:")
    for t in tagihan_lama:
        print(
            f"ID={t.id} | Semester={t.semester} | "
            f"Nominal={t.nominal_tagihan}"
        )

    # 8. Hapus hanya baris lama yang sudah diperiksa.
    try:
        for t in tagihan_lama:
            db.session.delete(t)

        # Perbaiki tahun tarif semester 2.
        tarif2.tahun_pelajaran = "2025/2026-2"

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    print("\nPerbaikan selesai.")
    print(f"Jumlah tagihan lama dihapus: {len(tagihan_lama)}")
    print("Tarif bangunan_s2 sekarang: 2025/2026-2")
    print("Tagihan lain tidak diubah.")
