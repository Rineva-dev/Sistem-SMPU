from datetime import date
from flask import Flask
from config import Config
from models import db, Siswa, RiwayatSemester, TahunPelajaran

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    # === FUNGSI BUAT/CARI TAHUN PELAJARAN ===
    def get_or_create_tp(kode):
        tp = TahunPelajaran.query.filter_by(kode=kode).first()
        if not tp:
            mulai, selesai = kode.split('/')
            tp = TahunPelajaran(
                kode=kode,
                nama=f"Tahun Pelajaran {kode}",
                tahun_mulai=int(mulai),
                tahun_selesai=int(selesai),
                semester=1,
                aktif=True,
                tanggal_mulai=date(int(mulai), 7, 15),
                tanggal_selesai=date(int(selesai), 6, 15)
            )
            db.session.add(tp)
            db.session.flush()
            print(f"✅ Tahun Pelajaran dibuat: {kode}")
        return tp

    # === SIAPKAN DATA ===
    tp1 = get_or_create_tp("2025/2026")
    tp2 = get_or_create_tp("2026/2027")

    siswa1 = Siswa.query.get(1)
    siswa2 = Siswa.query.get(2)

    if not siswa1 or not siswa2:
        print("❌ Data siswa belum ada! Jalankan cek_dan_tambah.py dulu")
        exit()

    # === HAPUS RIWAYAT LAMA ===
    RiwayatSemester.query.filter_by(siswa_id=1).delete()
    RiwayatSemester.query.filter_by(siswa_id=2).delete()
    print("✅ Riwayat lama dibersihkan")

    # === BUAT RIWAYAT SISWA 1: 2025/2026 ===
    r1 = RiwayatSemester(
        siswa_id=1,
        tahun_pelajaran=tp1.kode,
        semester=1,
        status_awal="Awal Siswa Baru",
        status_akhir="Aktif",
        tingkat_saat_itu="7",
        keaktifan="Aktif"
    )
    db.session.add(r1)
    print(f"✅ Siswa {siswa1.nama} → {tp1.kode} | Awal Siswa Baru | Aktif")

    # === BUAT RIWAYAT SISWA 2: 2026/2027 ===
    r2 = RiwayatSemester(
        siswa_id=2,
        tahun_pelajaran=tp2.kode,
        semester=1,
        status_awal="Awal Siswa Baru",
        status_akhir="Aktif",
        tingkat_saat_itu="7",
        keaktifan="Aktif"
    )
    db.session.add(r2)
    print(f"✅ Siswa {siswa2.nama} → {tp2.kode} | Awal Siswa Baru | Aktif")

    db.session.commit()
    print("\n✅ SELESAI! Buka halaman web sekarang → data muncul!")