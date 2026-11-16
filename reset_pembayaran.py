
import uuid

from sqlalchemy import text
from app import app, db


def perbaiki_public_id():
    print("=" * 55)
    print("PERBAIKAN DATABASE SISWA - PUBLIC ID")
    print("=" * 55)

    with app.app_context():

        # Pastikan database yang digunakan adalah SQLite
        if db.engine.dialect.name != "sqlite":
            print("ERROR: Database aplikasi bukan SQLite.")
            print("Database terdeteksi:", db.engine.dialect.name)
            return

        print("Database SQLite terdeteksi.")

        with db.engine.begin() as conn:

            # 1. Periksa kolom tabel siswa
            columns = conn.execute(
                text("PRAGMA table_info(siswa)")
            ).fetchall()

            column_names = [column[1] for column in columns]

            # 2. Tambahkan kolom jika belum tersedia
            if "public_id" not in column_names:
                print("Menambahkan kolom public_id...")

                conn.execute(
                    text("""
                        ALTER TABLE siswa
                        ADD COLUMN public_id VARCHAR(36)
                    """)
                )

                print("Kolom public_id berhasil ditambahkan.")
            else:
                print("Kolom public_id sudah tersedia.")

            # 3. Ambil siswa yang belum mempunyai UUID
            siswa_belum_punya_uuid = conn.execute(
                text("""
                    SELECT id
                    FROM siswa
                    WHERE public_id IS NULL OR public_id = ''
                """)
            ).fetchall()

            jumlah_diperbaiki = 0

            # 4. Buat UUID permanen untuk setiap siswa
            for siswa in siswa_belum_punya_uuid:
                conn.execute(
                    text("""
                        UPDATE siswa
                        SET public_id = :public_id
                        WHERE id = :id
                    """),
                    {
                        "public_id": str(uuid.uuid4()),
                        "id": siswa[0]
                    }
                )

                jumlah_diperbaiki += 1

            print(
                f"UUID berhasil dibuat untuk {jumlah_diperbaiki} siswa."
            )

            # 5. Pastikan tidak ada UUID kosong
            jumlah_kosong = conn.execute(
                text("""
                    SELECT COUNT(*)
                    FROM siswa
                    WHERE public_id IS NULL OR public_id = ''
                """)
            ).scalar()

            if jumlah_kosong:
                raise RuntimeError(
                    "Masih ada siswa tanpa public_id. Perubahan dibatalkan."
                )

            # 6. Buat unique index
            conn.execute(
                text("""
                    CREATE UNIQUE INDEX IF NOT EXISTS uq_siswa_public_id
                    ON siswa(public_id)
                """)
            )

            # 7. Verifikasi hasil
            total_siswa = conn.execute(
                text("SELECT COUNT(*) FROM siswa")
            ).scalar()

            total_uuid = conn.execute(
                text("""
                    SELECT COUNT(DISTINCT public_id)
                    FROM siswa
                """)
            ).scalar()

            if total_siswa != total_uuid:
                raise RuntimeError(
                    "Verifikasi UUID gagal. Perubahan dibatalkan."
                )

        print()
        print("=" * 55)
        print("PERBAIKAN BERHASIL!")
        print("=" * 55)
        print(f"Total siswa       : {total_siswa}")
        print(f"Total UUID unik   : {total_uuid}")
        print(f"UUID baru dibuat  : {jumlah_diperbaiki}")
        print("Database berhasil diverifikasi.")
        print("=" * 55)


if __name__ == "__main__":
    try:
        perbaiki_public_id()
    except Exception as error:
        print()
        print("PERBAIKAN GAGAL!")
        print("Penyebab:", error)
        print("Transaksi database telah dibatalkan jika terjadi error.")
