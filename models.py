from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint, CheckConstraint
from datetime import datetime, date, time
from sqlalchemy import String
from werkzeug.security import generate_password_hash, check_password_hash

# ✅ Inisialisasi database
db = SQLAlchemy()


class Guru(db.Model):
    __tablename__ = 'guru'

    nip = db.Column(db.String(50), nullable=True)
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nama = db.Column(db.String(100), nullable=False)
    jenis_kelamin = db.Column(db.String(20), nullable=False)
    tempat_lahir = db.Column(db.String(100))
    tanggal_lahir = db.Column(db.Date)
    jabatan = db.Column(db.String(50), nullable=False)
    tugas_tambahan = db.Column(db.Text)
    sertifikasi = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='Aktif')

    no_hp = db.Column(db.String(20))
    email = db.Column(db.String(100), unique=True, nullable=True)
    
    alamat = db.Column(db.Text)
    dibuat_pada = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi ke akun pengguna
    akun = db.relationship('User', backref='guru', uselist=False)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    guru_id = db.Column(db.Integer, db.ForeignKey('guru.id'), nullable=True, unique=True)
    siswa_id = db.Column(db.Integer, db.ForeignKey('siswa.id'), nullable=True, unique=True)
    jabatan = db.Column(db.String(50))
    tugas_tambahan = db.Column(db.Text)
    aktif = db.Column(db.Boolean, default=True)

    __table_args__ = (
        CheckConstraint(
            "(guru_id IS NOT NULL AND siswa_id IS NULL) OR (guru_id IS NULL AND siswa_id IS NOT NULL) OR (guru_id IS NULL AND siswa_id IS NULL)",
            name='_satu_saja_guru_atau_siswa'
        ),
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# --- TABEL SURAT KELUAR ---
class SuratKeluar(db.Model):
    __tablename__ = 'surat_keluar'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nomor_surat = db.Column(db.String(100), unique=True, nullable=False)
    tanggal_surat = db.Column(db.Date, nullable=False)
    lampiran = db.Column(db.String(200), default='-')
    perihal = db.Column(db.String(255), nullable=False)
    tujuan = db.Column(db.Text, nullable=False)
    tujuan_mentah = db.Column(db.Text, default='', nullable=True)
    tujuan_lokasi = db.Column(db.String(100), default='Tempat', nullable=True)
    isi_surat = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.String(50),
        default='Tersimpan',
        comment='Nilai: Tersimpan, Diajukan, Disetujui, Perlu Perbaikan, Ditolak'
    )
    file_path = db.Column(db.String(255), nullable=True)
    dibuat_pada = db.Column(db.DateTime, default=datetime.utcnow)
    dibuat_oleh = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    qr_code_path = db.Column(db.String(255), nullable=True)

    daftar_penandatangan = db.relationship(
        'PenandatanganSurat',
        back_populates='surat',
        lazy=True,
        cascade='all, delete-orphan'
    )

    pembuat = db.relationship('User', foreign_keys=[dibuat_oleh], backref='surat_keluar_dibuat', lazy=True)


class PenandatanganSurat(db.Model):
    __tablename__ = 'penandatangan_surat'

    id = db.Column(db.Integer, primary_key=True)
    surat_id = db.Column(db.Integer, db.ForeignKey('surat_keluar.id'), nullable=False)
    jenis = db.Column(db.String(50))
    id_guru = db.Column(db.Integer, db.ForeignKey('guru.id'), nullable=True)
    nama = db.Column(db.String(150), nullable=False)
    jabatan = db.Column(db.String(150), nullable=False)
    
    ttd_selesai = db.Column(db.Boolean, default=False)
    qr_code = db.Column(db.String(255), nullable=True)
    tanggal_ttd = db.Column(db.DateTime, nullable=True)

    surat = db.relationship('SuratKeluar', back_populates='daftar_penandatangan')
    guru = db.relationship('Guru', backref='daftar_tanda_tangan')


class AgendaKegiatan(db.Model):
    __tablename__ = 'agenda_kegiatan'

    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(200), nullable=False)
    deskripsi = db.Column(db.Text)
    tanggal_mulai = db.Column(db.DateTime, nullable=False)
    tanggal_selesai = db.Column(db.DateTime)
    lokasi = db.Column(db.String(150))
    penanggung_jawab = db.Column(db.String(100))
    status = db.Column(db.String(20), default='Terjadwal')
    dibuat_oleh = db.Column(db.String(100))
    dibuat_pada = db.Column(db.DateTime, default=datetime.utcnow)
    tahun_pelajaran = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"<Agenda {self.judul}>"


class TahunPelajaran(db.Model):
    __tablename__ = 'tahun_pelajaran'

    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(20), unique=True, nullable=False)
    nama = db.Column(db.String(80), nullable=False)
    tahun_mulai = db.Column(db.Integer, nullable=False)
    tahun_selesai = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    aktif = db.Column(db.Boolean, default=False)
    tanggal_mulai = db.Column(db.Date, nullable=False)
    tanggal_selesai = db.Column(db.Date, nullable=False)

    @staticmethod
    def set_aktif(id):
        TahunPelajaran.query.update({"aktif": False})
        tp = TahunPelajaran.query.get(id)
        if tp:
            tp.aktif = True
        db.session.commit()

    def __repr__(self):
        return f"<TahunPelajaran {self.kode}>"


class KalenderPendidikan(db.Model):
    __tablename__ = 'kalender_pendidikan'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nama_kegiatan = db.Column(db.String(200), nullable=False)
    tanggal_mulai = db.Column(db.Date, nullable=False)
    tanggal_selesai = db.Column(db.Date, nullable=False)
    semester = db.Column(db.String(10), nullable=False)
    jenis = db.Column(db.String(30), nullable=False)
    tahun_pelajaran_id = db.Column(db.Integer, db.ForeignKey('tahun_pelajaran.id'), nullable=False)
    disetujui = db.Column(db.Boolean, default=False)

    tahun_pelajaran = db.relationship('TahunPelajaran', backref=db.backref('daftar_kegiatan', lazy=True))

    def __repr__(self):
        return f"<KalenderPendidikan {self.nama_kegiatan}>"


class PenerimaSuratDiajukan(db.Model):
    __tablename__ = 'penerima_surat_diajukan'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    surat_id = db.Column(db.Integer, db.ForeignKey('surat_keluar.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    nama = db.Column(db.String(100), nullable=False)
    jabatan = db.Column(db.String(100), nullable=False)
    sudah_dibaca = db.Column(db.Boolean, default=False)
    status_tinjau = db.Column(db.String(20), default='Menunggu')

    surat = db.relationship('SuratKeluar', backref=db.backref('daftar_penerima_diajukan', lazy=True, cascade='all, delete-orphan'))
    pengguna = db.relationship('User', backref='surat_diajukan_kepadaku', lazy=True)

# ==========================================
# ✅ TABEL KELAS / ROMBEL
# ==========================================
class Kelas(db.Model):
    __tablename__ = 'kelas'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nama_kelas = db.Column(db.String(50), nullable=False)
    jenjang = db.Column(db.String(1), nullable=False)
    
    # ✅ KUNCI: Hanya simpan format dasar seperti "2025/2026"
    tahun_pelajaran = db.Column(
        db.String(20), 
        nullable=False, 
        index=True
    )
    
    wali_kelas_id = db.Column(db.Integer, db.ForeignKey('guru.id'), nullable=True)

    wali_kelas = db.relationship('Guru', backref=db.backref('kelas_diampu', lazy=True))
    daftar_siswa = db.relationship('Siswa', back_populates='kelas_sekarang', foreign_keys='Siswa.kelas_id', lazy=True)

    # ✅ HITUNG AMAN: TIDAK mengubah data apa pun
    def hitung_jumlah_siswa(self, kode_semester=None):
        """Hitung siswa sesuai semester yang dipilih"""
        if kode_semester:
            return RiwayatKelas.query.filter(
                RiwayatKelas.kelas_id == self.id,
                RiwayatKelas.tahun_pelajaran == kode_semester
            ).count()
        dasar = self.tahun_pelajaran
        return RiwayatKelas.query.filter(
            RiwayatKelas.kelas_id == self.id,
            RiwayatKelas.tahun_pelajaran.like(f"{dasar}%")
        ).count()

    __table_args__ = (
        db.UniqueConstraint('nama_kelas', 'tahun_pelajaran', name='_kelas_tahun_uc'),
    )

    def __repr__(self):
        return f"<Kelas {self.jenjang} {self.nama_kelas} - {self.tahun_pelajaran}>"

class PengaturanMapelKelas(db.Model):
    __tablename__ = 'pengaturan_mapel_kelas'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    kelas_id = db.Column(db.Integer, db.ForeignKey('kelas.id'), nullable=False)
    mata_pelajaran_id = db.Column(db.Integer, db.ForeignKey('mata_pelajaran.id'), nullable=False)
    guru_id = db.Column(db.Integer, db.ForeignKey('guru.id'), nullable=True)
    jumlah_jp = db.Column(db.Integer, nullable=False, default=0)
    tahun_pelajaran = db.Column(db.String(30), nullable=False)

    kelas = db.relationship('Kelas', backref='pengaturan_mapel')
    mata_pelajaran = db.relationship('MataPelajaran')
    guru = db.relationship('Guru')

# ==========================================
# ✅ TAMBAHKAN FUNGSI posisi_di_tahun() KE CLASS SISWA
# ==========================================

class Siswa(db.Model):
    __tablename__ = 'siswa'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nis = db.Column(db.String(20), unique=True, nullable=False)
    nisn = db.Column(db.String(20), unique=True, nullable=True)
    nik = db.Column(db.String(20), nullable=True)
    nama = db.Column(db.String(100), nullable=False)
    jenis_kelamin = db.Column(db.String(20), nullable=False)
    agama = db.Column(db.String(30), nullable=True)
    tempat_lahir = db.Column(db.String(100))
    tanggal_lahir = db.Column(db.Date)
    
    # ✅ Tingkat siswa: hanya berisi '7', '8', atau '9'
    tingkat = db.Column(db.String(1), nullable=True, index=True)

    # ✅ Kelas/rombel yang sedang ditempati saat ini
    kelas_id = db.Column(db.Integer, db.ForeignKey('kelas.id'), nullable=True, index=True)
    
    alamat = db.Column(db.Text)
    no_hp = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    tahun_masuk = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default='Aktif')

    nama_ayah = db.Column(db.String(100), nullable=True)
    nama_ibu = db.Column(db.String(100), nullable=True)
    no_hp_ortu = db.Column(db.String(20), nullable=True)
    pekerjaan_ayah = db.Column(db.String(50), nullable=True)
    pekerjaan_ibu = db.Column(db.String(50), nullable=True)

    # ✅ Kolom untuk sistem pendaftaran
    jenis_pendaftaran = db.Column(db.String(20), nullable=True)  # 'baru' / 'pindahan'
    tanggal_diterima = db.Column(db.Date, nullable=True)
    tahun_diterima = db.Column(db.Integer, nullable=True)
    diterima_di_kelas = db.Column(db.Integer, db.ForeignKey('kelas.id'), nullable=True)
    
    # ✅ Data sekolah asal
    sekolah_sd = db.Column(db.String(255), nullable=True)
    tahun_lulus_sd = db.Column(db.Integer, nullable=True)
    alamat_sekolah_sd = db.Column(db.Text, nullable=True)
    
    sekolah_asal_pindah = db.Column(db.String(255), nullable=True)
    tahun_pindah = db.Column(db.Integer, nullable=True)
    alamat_sekolah_pindah = db.Column(db.Text, nullable=True)

    dibuat_pada = db.Column(db.DateTime, default=datetime.utcnow)

    # ✅ Relasi yang sudah diperbaiki dan tidak bentrok
    akun = db.relationship('User', backref='siswa', uselist=False)
    kelas_sekarang = db.relationship('Kelas', back_populates='daftar_siswa', foreign_keys=[kelas_id])
    kelas_awal = db.relationship('Kelas', foreign_keys=[diterima_di_kelas])

    tanggal_non_aktif = db.Column(db.Date, nullable=True)
    alasan_non_aktif = db.Column(db.String(255), nullable=True)
    jenis_non_aktif = db.Column(db.String(20), nullable=True)  # 'Berhenti' atau 'Pindah'
    sekolah_tujuan = db.Column(db.String(100), nullable=True)

    # ✅ FUNGSI BARU: Ambil posisi siswa di tahun pelajaran tertentu
    def posisi_di_tahun(self, kode_tahun):
        """
        Mengembalikan data tingkat dan kelas siswa pada tahun pelajaran yang dipilih
        """
        if not kode_tahun:
            return None
        return RiwayatKelas.query.filter_by(
            siswa_id=self.id,
            tahun_pelajaran=kode_tahun
        ).first()

    def __repr__(self):
        return f"<Siswa {self.nama} - Tingkat {self.tingkat}>"
    
# ==========================================
# ✅ TABEL RIWAYAT KELAS
# ==========================================
class RiwayatKelas(db.Model):
    __tablename__ = 'riwayat_kelas'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    siswa_id = db.Column(db.Integer, db.ForeignKey('siswa.id'), nullable=False)
    tahun_pelajaran = db.Column(db.String(20), nullable=False)
    tingkat = db.Column(db.String(1), nullable=False)  # 7, 8, 9
    kelas_id = db.Column(db.Integer, db.ForeignKey('kelas.id'), nullable=True)

    # Cegah siswa memiliki 2 posisi di tahun yang sama
    __table_args__ = (
        db.UniqueConstraint('siswa_id', 'tahun_pelajaran', name='_siswa_tahun_unik'),
    )

    # Relasi
    siswa = db.relationship('Siswa', backref=db.backref('riwayat_kelas', lazy=True, cascade='all, delete-orphan'))
    kelas = db.relationship('Kelas', backref=db.backref('anggota_riwayat', lazy=True))

    def __repr__(self):
        return f"<RiwayatKelas {self.siswa_id} - {self.tahun_pelajaran} - Tingkat {self.tingkat}>"
    
# ==========================================
# ✅ TABEL MATA PELAJARAN
# ==========================================
class MataPelajaran(db.Model):
    __tablename__ = 'mata_pelajaran'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    kode = db.Column(db.String(20), nullable=False)
    nama_pelajaran = db.Column(db.String(100), nullable=False)
    kelompok = db.Column(db.String(50))
    keterangan = db.Column(db.Text)

    __table_args__ = (
        db.UniqueConstraint('kode', name='_kode_mapel_unik'),
    )

    def __repr__(self):
        return f"<MataPelajaran {self.kode} - {self.nama_pelajaran}>"

class JadwalPelajaran(db.Model):
    __tablename__ = 'jadwal_pelajaran'
    id = db.Column(db.Integer, primary_key=True)
    kelas_id = db.Column(db.Integer, db.ForeignKey('kelas.id'), nullable=False)
    tahun_pelajaran = db.Column(db.String(50), nullable=False)
    hari = db.Column(db.String(20), nullable=False)
    jam_mulai = db.Column(db.String(10), nullable=False)
    jam_selesai = db.Column(db.String(10), nullable=False)
    mata_pelajaran_id = db.Column(db.Integer, db.ForeignKey('mata_pelajaran.id'), nullable=False)
    guru_id = db.Column(db.Integer, db.ForeignKey('guru.id'), nullable=False) # Otomatis dari PengaturanMapelKelas

    __table_args__ = (
        db.UniqueConstraint('kelas_id', 'tahun_pelajaran', 'hari', 'jam_mulai', name='_jadwal_unik'),
    )

    kelas = db.relationship('Kelas', backref=db.backref('jadwal', lazy=True))
    mapel = db.relationship('MataPelajaran', backref=db.backref('jadwal', lazy=True))
    guru = db.relationship('Guru', backref=db.backref('jadwal', lazy=True))

# ==========================================
# ✅ TABEL KEUANGAN UNTUK BENDAHARA
# ==========================================
class TransaksiKeuangan(db.Model):
    __tablename__ = 'transaksi_keuangan'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    jenis = db.Column(db.String(20), nullable=False) # 'masuk' atau 'keluar'
    keterangan = db.Column(db.String(200), nullable=False)
    nominal = db.Column(db.BigInteger, nullable=False)
    tanggal = db.Column(db.Date, nullable=False)
    bulan = db.Column(db.Integer, nullable=False)
    tahun = db.Column(db.Integer, nullable=False)
    tahun_pelajaran = db.Column(db.String(20), nullable=True)
    dibuat_pada = db.Column(db.DateTime, default=datetime.utcnow)

class PembayaranSiswa(db.Model):
    __tablename__ = 'pembayaran_siswa'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    siswa_id = db.Column(db.Integer, db.ForeignKey('siswa.id'), nullable=False)
    tahun_pelajaran = db.Column(db.String(20), nullable=False)
    bulan = db.Column(db.String(20), nullable=False)
    jumlah = db.Column(db.BigInteger, nullable=False)
    status = db.Column(db.String(20), default='Belum Lunas') # 'Lunas' / 'Belum Lunas'
    dibuat_pada = db.Column(db.DateTime, default=datetime.utcnow)

    siswa = db.relationship('Siswa', backref=db.backref('pembayaran', lazy=True))

# ==========================================
# ✅ TABEL PENGATURAN JENIS & NOMINAL PEMBAYARAN
# Pondasi utama: SPP, Pembangunan, Kelas Unggulan, Media, Peminatan, Ekskul, dll
# ==========================================
class JenisPembayaran(db.Model):
    __tablename__ = 'jenis_pembayaran'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nama = db.Column(db.String(100), nullable=False)
    # ✅ SUDAH BENAR: tidak ada unique=True di sini
    kode = db.Column(db.String(50), nullable=False, index=True)
    pola_waktu = db.Column(db.String(50), nullable=False) 
    nominal = db.Column(db.BigInteger, nullable=False, default=0)
    keterangan = db.Column(db.Text, nullable=True)
    tahun_pelajaran = db.Column(db.String(20), nullable=False, index=True)
    aktif = db.Column(db.Boolean, default=True)
    dibuat_pada = db.Column(db.DateTime, default=datetime.utcnow)

    tgl_berlaku_mulai = db.Column(db.Date, default=date.today)
    tgl_berlaku_sampai = db.Column(db.Date, nullable=True)

    # ✅ SUDAH BENAR: Kunci unik gabungan
    __table_args__ = (
        db.UniqueConstraint('kode', 'tahun_pelajaran', name='_kode_tahun_pembayaran_uc'),
    )

    def __repr__(self):
        return f"<JenisPembayaran {self.nama} - {self.tahun_pelajaran}>"
    
# ==========================================
# ✅ TABEL TAGIHAN PER SISWA
# Menghubungkan jenis bayaran dengan siswa yang bersangkutan
# ==========================================
class TagihanSiswa(db.Model):
    __tablename__ = 'tagihan_siswa'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    siswa_id = db.Column(db.Integer, db.ForeignKey('siswa.id'), nullable=False)
    jenis_pembayaran_id = db.Column(db.Integer, db.ForeignKey('jenis_pembayaran.id'), nullable=False)
    bulan = db.Column(db.String(20), nullable=True)
    semester = db.Column(db.Integer, nullable=True)
    tahun_pelajaran = db.Column(db.String(20), nullable=False)
    nominal_tagihan = db.Column(db.BigInteger, nullable=False)
    sudah_dibayar = db.Column(db.BigInteger, default=0)
    status = db.Column(db.String(20), default='Belum Lunas', index=True)
    tanggal_jatuh_tempo = db.Column(db.Date, nullable=True)
    tanggal_lunas = db.Column(db.Date, nullable=True)
    dibuat_pada = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def sisa_tagihan(self):
        return (self.nominal_tagihan or 0) - (self.sudah_dibayar or 0)

    @property
    def jumlah_kali_bayar(self):
        return len(self.riwayat)

    @property
    def is_lunas(self):
        return self.sisa_tagihan <= 0

    @property
    def daftar_tanggal_bayar(self):
        return [r.tanggal_bayar for r in self.riwayat if r.tanggal_bayar]

    siswa = db.relationship('Siswa', backref=db.backref('daftar_tagihan', lazy=True, cascade='all, delete-orphan'))
    jenis = db.relationship('JenisPembayaran', backref=db.backref('tagihan', lazy=True))

    # ✅ DI PERBAIKI: pakai back_populates
    riwayat = db.relationship(
        'RiwayatPembayaran',
        back_populates='tagihan',
        lazy=True,
        cascade='all, delete-orphan',
        order_by='desc(RiwayatPembayaran.tanggal_bayar)'
    )

    def __repr__(self):
        return f"<TagihanSiswa {self.id} — Rp {self.nominal_tagihan:,} — {self.status}>"
    
# ==========================================
# ✅ TABEL RIWAYAT PEMBAYARAN
# Bukti saat bendahara mencatat uang masuk
# ==========================================
class RiwayatPembayaran(db.Model):
    __tablename__ = 'riwayat_pembayaran'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tagihan_id = db.Column(db.Integer, db.ForeignKey('tagihan_siswa.id'), nullable=False)
    jumlah_bayar = db.Column(db.BigInteger, nullable=False)
    metode = db.Column(db.String(50), default='Tunai')
    tanggal_bayar = db.Column(db.DateTime, nullable=False, default=datetime.now)
    dicatat_oleh = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    keterangan = db.Column(db.Text, nullable=True)
    nomor_bukti = db.Column(db.String(50), unique=True, nullable=True)
    dibuat_pada = db.Column(db.DateTime, default=datetime.utcnow)

    # ✅ DI PERBAIKI: saling merujuk dengan back_populates
    tagihan = db.relationship(
        'TagihanSiswa',
        back_populates='riwayat',
        lazy=True
    )
    pencatat = db.relationship('User', backref=db.backref('pembayaran_dicatat', lazy=True))

    def __repr__(self):
        return f"<RiwayatBayar {self.id} - Rp {self.jumlah_bayar:,}>"

# ==========================================
# ✅ TABEL PENGHUBUNG: EKSKUL <-> SISWA (MANY-TO-MANY)
# ==========================================
ekskul_anggota = db.Table(
    'ekskul_anggota',
    db.Column('ekskul_id', db.Integer, db.ForeignKey('ekstrakurikuler.id'), primary_key=True),
    db.Column('siswa_id', db.Integer, db.ForeignKey('siswa.id'), primary_key=True)
)

class Ekstrakurikuler(db.Model):
    __tablename__ = 'ekstrakurikuler'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nama = db.Column(db.String(100), nullable=False)
    pembina_id = db.Column(db.Integer, db.ForeignKey('guru.id'), nullable=True)
    keterangan = db.Column(db.Text, nullable=True)
    dibuat_pada = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ✅ TETAP PAKAI TANGGAL SAJA
    tgl_mulai = db.Column(db.Date, nullable=False)
    tgl_selesai = db.Column(db.Date, nullable=False)

    tahun_pelajaran = db.Column(db.String(20), nullable=False, index=True)

    # ✅ HAPUS KOLOM MANUAL INI:
    # aktif = db.Column(db.Boolean, default=True)
    # status_kegiatan = db.Column(db.String(20), default='aktif')

    anggota = db.relationship('Siswa', secondary=ekskul_anggota, backref='ekstrakurikuler')
    pembina = db.relationship('Guru', backref='ekstrakurikuler_dibina')

    __table_args__ = (
        db.UniqueConstraint('nama', 'tahun_pelajaran', name='_nama_ekskul_tahun_uc'),
    )

    def __repr__(self):
        return f"<Ekstrakurikuler {self.nama} - {self.tahun_pelajaran}>"

# ==========================================
# ✅ TABEL JURNAL KEGIATAN EKSKUL
# ==========================================
class JurnalEkskul(db.Model):
    __tablename__ = 'jurnal_ekskul'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ekskul_id = db.Column(db.Integer, db.ForeignKey('ekstrakurikuler.id'), nullable=False)
    tanggal_kegiatan = db.Column(db.Date, nullable=False)
    waktu_mulai = db.Column(db.String(10))
    waktu_selesai = db.Column(db.String(10))
    uraian_kegiatan = db.Column(db.Text, nullable=False)
    hasil_kegiatan = db.Column(db.Text, nullable=True)
    kendala = db.Column(db.Text, nullable=True)
    catatan_pembina = db.Column(db.Text, nullable=True)
    jumlah_hadir = db.Column(db.Integer, nullable=True)
    terlambat = db.Column(db.Integer, nullable=True)
    izin = db.Column(db.Integer, nullable=True)
    sakit = db.Column(db.Integer, nullable=True)
    alpha = db.Column(db.Integer, nullable=True)
    dibuat_oleh = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    dibuat_pada = db.Column(db.DateTime, default=datetime.utcnow)
    diperbarui_pada = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relasi
    ekskul = db.relationship('Ekstrakurikuler', backref=db.backref('jurnal', lazy=True, cascade='all, delete-orphan'))
    pencatat = db.relationship('User', backref='jurnal_ekskul_dicatat', lazy=True)

    def __repr__(self):
        return f"<Jurnal {self.tanggal_kegiatan} - {self.ekskul.nama}>"

peminatan_anggota = db.Table(
    'peminatan_anggota',
    db.Column('peminatan_id', db.Integer, db.ForeignKey('peminatan.id'), primary_key=True),
    db.Column('siswa_id', db.Integer, db.ForeignKey('siswa.id'), primary_key=True)
)

class Peminatan(db.Model):
    __tablename__ = 'peminatan' # Tambahkan nama tabel secara eksplisit

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    tahun_pelajaran = db.Column(db.String(20), nullable=False, index=True)
    
    # ✅ PERBAIKI: Merujuk ke tabel Guru, bukan User
    pembina_id = db.Column(db.Integer, db.ForeignKey('guru.id'), nullable=True)
    
    tgl_mulai = db.Column(db.Date, nullable=False)
    tgl_selesai = db.Column(db.Date, nullable=False)
    keterangan = db.Column(db.Text, nullable=True)

    # ✅ PERBAIKI: Relasi ke Guru, persis seperti Ekstrakurikuler
    pembina = db.relationship('Guru', backref='peminatan_dibina', foreign_keys=[pembina_id])
    anggota = db.relationship('Siswa', secondary=peminatan_anggota, backref='peminatan_diikuti')

    # ✅ Tambah aturan unik persis seperti Ekskul
    __table_args__ = (
        db.UniqueConstraint('nama', 'tahun_pelajaran', name='_nama_peminatan_tahun_uc'),
    )

# ==========================================
# ✅ TABEL BULAN LIBUR EKSTRAKURIKULER
# ==========================================
class BulanLiburEkskul(db.Model):
    __tablename__ = 'bulan_libur_ekskul'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ekskul_id = db.Column(db.Integer, db.ForeignKey('ekstrakurikuler.id'), nullable=False)
    bulan = db.Column(db.Integer, nullable=False)   # 1 s.d. 12
    tahun = db.Column(db.Integer, nullable=False)    # misal 2025
    keterangan = db.Column(db.Text, nullable=True)
    dibuat_pada = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi balik ke Ekstrakurikuler
    ekskul = db.relationship('Ekstrakurikuler', backref=db.backref('bulan_libur', lazy=True, cascade='all, delete-orphan'))

    # Cegah bulan & tahun sama terdaftar ganda untuk satu ekskul
    __table_args__ = (
        db.UniqueConstraint('ekskul_id', 'bulan', 'tahun', name='_ekskul_bulan_tahun_unik'),
    )

    def __repr__(self):
        return f"<BulanLibur {self.bulan}/{self.tahun} - Ekskul {self.ekskul_id}>"

# ==========================================
# ✅ TABEL ABSENSI SISWA PER JURNAL
# ==========================================
class AbsensiJurnalEkskul(db.Model):
    __tablename__ = 'absensi_jurnal_ekskul'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    jurnal_id = db.Column(db.Integer, db.ForeignKey('jurnal_ekskul.id'), nullable=False)
    siswa_id = db.Column(db.Integer, db.ForeignKey('siswa.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='hadir') 
    # Isi: hadir / sakit / izin / alpha

    # Relasi
    jurnal = db.relationship('JurnalEkskul', backref=db.backref('daftar_absensi', lazy=True, cascade='all, delete-orphan'))
    siswa = db.relationship('Siswa', backref='absensi_ekskul')

    # Cegah siswa tercatat ganda di jurnal yang sama
    __table_args__ = (
        db.UniqueConstraint('jurnal_id', 'siswa_id', name='_jurnal_siswa_unik'),
    )

    def __repr__(self):
        return f"<Absensi Jurnal {self.jurnal_id} - Siswa {self.siswa_id}: {self.status}>"

# ==========================================
# ✅ TABEL JURNAL KEGIATAN PEMINATAN
# ==========================================
class JurnalPeminatan(db.Model):
    __tablename__ = 'jurnal_peminatan'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    peminatan_id = db.Column(db.Integer, db.ForeignKey('peminatan.id'), nullable=False)
    tanggal_kegiatan = db.Column(db.Date, nullable=False)
    waktu_mulai = db.Column(db.String(10))
    waktu_selesai = db.Column(db.String(10))
    uraian_kegiatan = db.Column(db.Text, nullable=False)
    hasil_kegiatan = db.Column(db.Text, nullable=True)
    kendala = db.Column(db.Text, nullable=True)
    catatan_pembina = db.Column(db.Text, nullable=True)
    jumlah_hadir = db.Column(db.Integer, nullable=True)
    terlambat = db.Column(db.Integer, nullable=True)
    izin = db.Column(db.Integer, nullable=True)
    sakit = db.Column(db.Integer, nullable=True)
    alpha = db.Column(db.Integer, nullable=True)
    dibuat_oleh = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    dibuat_pada = db.Column(db.DateTime, default=datetime.utcnow)
    diperbarui_pada = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relasi
    peminatan = db.relationship('Peminatan', backref=db.backref('jurnal', lazy=True, cascade='all, delete-orphan'))
    pencatat = db.relationship('User', backref='jurnal_peminatan_dicatat', lazy=True)

    def __repr__(self):
        return f"<JurnalPeminatan {self.tanggal_kegiatan} - {self.peminatan.nama}>"


# ==========================================
# ✅ TABEL BULAN LIBUR PEMINATAN
# ==========================================
class BulanLiburPeminatan(db.Model):
    __tablename__ = 'bulan_libur_peminatan'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    peminatan_id = db.Column(db.Integer, db.ForeignKey('peminatan.id'), nullable=False)
    bulan = db.Column(db.Integer, nullable=False)   # 1 s.d. 12
    tahun = db.Column(db.Integer, nullable=False)    # misal 2025
    keterangan = db.Column(db.Text, nullable=True)
    dibuat_pada = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi balik ke Peminatan
    peminatan = db.relationship('Peminatan', backref=db.backref('bulan_libur', lazy=True, cascade='all, delete-orphan'))

    # Cegah bulan & tahun sama terdaftar ganda untuk satu peminatan
    __table_args__ = (
        db.UniqueConstraint('peminatan_id', 'bulan', 'tahun', name='_peminatan_bulan_tahun_unik'),
    )

    def __repr__(self):
        return f"<BulanLiburPeminatan {self.bulan}/{self.tahun} - Peminatan {self.peminatan_id}>"


# ==========================================
# ✅ TABEL ABSENSI SISWA PER JURNAL PEMINATAN
# ==========================================
class AbsensiJurnalPeminatan(db.Model):
    __tablename__ = 'absensi_jurnal_peminatan'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    jurnal_id = db.Column(db.Integer, db.ForeignKey('jurnal_peminatan.id'), nullable=False)
    siswa_id = db.Column(db.Integer, db.ForeignKey('siswa.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='hadir') 
    # Isi: hadir / sakit / izin / alpha

    # Relasi
    jurnal = db.relationship('JurnalPeminatan', backref=db.backref('daftar_absensi', lazy=True, cascade='all, delete-orphan'))
    siswa = db.relationship('Siswa', backref='absensi_peminatan')

    # Cegah siswa tercatat ganda di jurnal yang sama
    __table_args__ = (
        db.UniqueConstraint('jurnal_id', 'siswa_id', name='_jurnal_peminatan_siswa_unik'),
    )

    def __repr__(self):
        return f"<AbsensiJurnalPeminatan {self.jurnal_id} - Siswa {self.siswa_id}: {self.status}>"

# ==========================================
# ✅ TABEL ABSENSI GURU
# ==========================================
class AbsensiGuru(db.Model):
    __tablename__ = 'absensi_guru'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    guru_id = db.Column(db.Integer, db.ForeignKey('guru.id'), nullable=False)
    tanggal = db.Column(db.Date, nullable=False)
    jam_masuk = db.Column(db.String(10), nullable=True)
    jam_pulang = db.Column(db.String(10), nullable=True) 
    status = db.Column(db.String(20), nullable=False, default='hadir')
    keterangan = db.Column(db.Text, nullable=True)
    dibuat_pada = db.Column(db.DateTime, default=datetime.utcnow)
    diperbarui_pada = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    guru = db.relationship('Guru', backref=db.backref('daftar_absensi', lazy=True))

    __table_args__ = (
        db.UniqueConstraint('guru_id', 'tanggal', name='_guru_tanggal_unik'),
    )

    def __repr__(self):
        return f"<AbsensiGuru {self.tanggal} - {self.guru.nama}: {self.status}>"

# ==========================================
# ✅ TABEL GAJI GURU
# ==========================================
class GajiGuru(db.Model):
    __tablename__ = 'gaji_guru'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    guru_id = db.Column(db.Integer, db.ForeignKey('guru.id'), nullable=False)
    bulan = db.Column(db.Integer, nullable=False)   # 1-12
    tahun = db.Column(db.Integer, nullable=False)
    
    # Komponen Penerimaan
    gaji_pokok = db.Column(db.Numeric(12,2), default=0)
    tunjangan_jabatan = db.Column(db.Numeric(12,2), default=0)
    tunjangan_fungsional = db.Column(db.Numeric(12,2), default=0)
    tunjangan_lain = db.Column(db.Numeric(12,2), default=0)
    bonus = db.Column(db.Numeric(12,2), default=0)
    
    # Komponen Potongan
    potongan_wajib = db.Column(db.Numeric(12,2), default=0)
    pph = db.Column(db.Numeric(12,2), default=0)
    potongan_terlambat = db.Column(db.Numeric(12,2), default=0)
    pinjaman = db.Column(db.Numeric(12,2), default=0)
    
    # Hasil Perhitungan (bisa disimpan atau dihitung otomatis)
    total_penerimaan = db.Column(db.Numeric(12,2), default=0)
    total_potongan = db.Column(db.Numeric(12,2), default=0)
    gaji_bersih = db.Column(db.Numeric(12,2), default=0)
    
    # Status & Bukti
    status = db.Column(db.String(20), default='dibayar')  # dibayar / belum
    tanggal_dibayar = db.Column(db.Date)
    kode_verifikasi = db.Column(db.String(20))

    # Relasi ke Guru
    guru = db.relationship('Guru', backref=db.backref('daftar_gaji', lazy=True, cascade='all, delete-orphan'))

    # Cegah gaji ganda di bulan yang sama
    __table_args__ = (
        db.UniqueConstraint('guru_id', 'bulan', 'tahun', name='_gaji_bulan_tahun_unik'),
    )

    def __repr__(self):
        return f"<GajiGuru {self.guru.nama} - {self.bulan}/{self.tahun}: Rp {self.gaji_bersih:,}>"

# ==========================================
# ✅ TABEL 1: PENGATURAN JAM KERJA ABSENSI
# Menyimpan jam masuk, terlambat, pulang standar & khusus Jumat
# ==========================================
class PengaturanJamKerja(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jam_masuk = db.Column(db.Time, nullable=True)
    batas_terlambat = db.Column(db.Time, nullable=True)       # ✅ SERAGAM: batas_terlambat
    jam_tutup_absensi = db.Column(db.Time, nullable=True)
    jam_pulang = db.Column(db.Time, nullable=True)
    jam_masuk_jumat = db.Column(db.Time, nullable=True)
    jam_pulang_jumat = db.Column(db.Time, nullable=True)
    diperbarui_pada = db.Column(db.DateTime, default=datetime.utcnow)
    diperbarui_oleh = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    @staticmethod
    def ambil_atau_buat():
        obj = PengaturanJamKerja.query.order_by(PengaturanJamKerja.id.desc()).first()
        if not obj:
            from datetime import time
            obj = PengaturanJamKerja(
                jam_masuk=time(7, 15),
                batas_terlambat=time(7, 30),       # ✅ SAMA: batas_terlambat
                jam_tutup_absensi=time(9, 0),
                jam_pulang=time(15, 0),
                jam_masuk_jumat=time(7, 0),
                jam_pulang_jumat=time(11, 30)
            )
            db.session.add(obj)
            db.session.commit()
        return obj
    
# ==========================================
# ✅ TABEL 2: TANGGAL PENGECUALIAN
# Untuk hari tertentu pulang lebih awal karena kegiatan
# ==========================================
class TanggalPengecualian(db.Model):
    __tablename__ = 'tanggal_pengecualian'
    
    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.Date, nullable=False, unique=True)
    
    jam_masuk = db.Column(db.Time, nullable=False)
    jam_pulang = db.Column(db.Time, nullable=False)
    
    keterangan = db.Column(db.String(200), nullable=True)  # misal: "Upacara", "Kegiatan Sekolah"
    dibuat_pada = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('tanggal', name='_tanggal_pengecualian_unik'),
    )
    
    def __repr__(self):
        return f"<Pengecualian {self.tanggal} Pulang={self.jam_pulang} — {self.keterangan}>"