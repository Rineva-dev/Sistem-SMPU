
from app import app
from models import db
from sqlalchemy import inspect, text


with app.app_context():
    try:
        inspector = inspect(db.engine)

        kolom_tersedia = {
            kolom['name']
            for kolom in inspector.get_columns('gaji_guru')
        }

        if 'status_penerbitan' not in kolom_tersedia:

            with db.engine.begin() as koneksi:
                koneksi.execute(text("""
                    ALTER TABLE gaji_guru
                    ADD COLUMN status_penerbitan
                    VARCHAR(20)
                    NOT NULL DEFAULT 'draft'
                """))

            print("Berhasil menambahkan kolom status_penerbitan.")

        else:
            print("Kolom status_penerbitan sudah tersedia.")

        print("Migrasi selesai.")

    except Exception as e:
        print(f"Migrasi gagal: {e}")
