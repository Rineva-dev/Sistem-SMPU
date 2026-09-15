from flask import Flask, request, g, session, flash, url_for, redirect
from config import Config
from models import db, TahunPelajaran
from flask_migrate import Migrate

# ✅ Impor filter
from routes import number_format

app = Flask(__name__)
app.config.from_object(Config)

# =========================================================
# 🔑 KONFIGURASI SESI PISAH BERDASARKAN SUBDOMAIN
# =========================================================
app.secret_key = 'ganti_dengan_kunci_rahasia_yang_kuat_dan_acak'

# Domain utama — berlaku untuk semua subdomain
@app.before_request
def atur_domain_sesi():
    host = request.host.lower()
    if host.endswith('.smpuhamzanwadi.sch.id'):
        app.config['SESSION_COOKIE_DOMAIN'] = ".smpuhamzanwadi.sch.id"
    else:

        app.config['SESSION_COOKIE_DOMAIN'] = None
        app.config['SESSION_COOKIE_PATH'] = "/"
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        # Ubah ke True jika sudah pakai HTTPS di produksi
        app.config['SESSION_COOKIE_SECURE'] = False

# =========================================================
# ✅ CARA AMAN: GANTI NAMA COOKIE SEBELUM SESI DIPAKAI
# =========================================================
from flask.sessions import SecureCookieSessionInterface

class SesuaiSubdomainSessionInterface(SecureCookieSessionInterface):
    def get_cookie_name(self, app):
        host = request.host.lower()
        if host.startswith('absensi.'):
            return 'sesi_absensi'
        elif host.startswith('school.'):
            return 'sesi_sekolah'
        return 'sesi_umum'

# Pasang antarmuka sesi khusus — ini yang memisahkan sesi
app.session_interface = SesuaiSubdomainSessionInterface()

# ✅ Daftarkan filter ke Jinja
app.jinja_env.filters['number_format'] = number_format

def nama_singkat(nama, maks_kata=2):
    """
    Ambil maksimal 2 kata pertama, gelar di belakang otomatis dilewati
    Contoh: "Siti Aminah, S.Pd., M.Pd." → "Siti Aminah"
    Contoh: "Budi Santoso Hutagalung" → "Budi Santoso"
    """
    if not nama:
        return "Pengguna"
    
    # Hapus gelar/bagian setelah koma/koma-spasi
    nama_bersih = nama.split(',')[0].strip()
    
    # Pisah per kata
    kata = nama_bersih.split()
    
    # Ambil maks 2 kata pertama
    if len(kata) > maks_kata:
        return ' '.join(kata[:maks_kata])
    
    return nama_bersih

# Daftarkan filter
app.jinja_env.filters['nama_singkat'] = nama_singkat

# ==== SUDAH ADA DI SANA ====
def nama_singkat(nama, maks_kata=2):
    """
    Ambil maksimal 2 kata pertama, gelar di belakang otomatis dilewati
    Contoh: "Siti Aminah, S.Pd., M.Pd." → "Siti Aminah"
    Contoh: "Budi Santoso Hutagalung" → "Budi Santoso"
    """
    if not nama:
        return "Pengguna"
    
    # Hapus gelar/bagian setelah koma/koma-spasi
    nama_bersih = nama.split(',')[0].strip()
    
    # Pisah per kata
    kata = nama_bersih.split()
    
    # Ambil maks 2 kata pertama
    if len(kata) > maks_kata:
        return ' '.join(kata[:maks_kata])
    
    return nama_bersih

# Daftarkan filter
app.jinja_env.filters['nama_singkat'] = nama_singkat

# ✅ === TAMBAHKAN FILTER BARU DI BAWAH INI ===
import re

def nama_singkat_dropdown(nama_lengkap):
    """
    Singkatkan nama sesuai aturan:
    - Hilangkan gelar depan sementara, proses nama, lalu gabung lagi
    - Jika kata pertama ≥4 huruf → ambil 1 kata
    - Jika kata pertama ≤3 huruf → ambil 2 kata
    - Gelar depan tetap ditampilkan
    """
    if not nama_lengkap:
        return "Pengguna"
    
    nama_lengkap = nama_lengkap.strip()

    gelar_depan = r"^(Dr\.|Drg\.|Prof\.|Ir\.|Sdr\.|H\.|K\.H\.|Alm\.|Almh\.|Drs\.|M\.|Bpk\.|Ibu\.|Ny\.|Tn\.)\s+"
    
    gelar = ""
    nama_murni = nama_lengkap

    cocok = re.match(gelar_depan, nama_lengkap)
    if cocok:
        gelar = cocok.group(0)
        nama_murni = nama_lengkap[cocok.end():]

    kata = nama_murni.split()
    if not kata:
        return gelar + "Pengguna"

    kata1 = kata[0].strip(".,")
    if len(kata1) >= 4:

        nama_terambil = kata[0]
    else:
        nama_terambil = " ".join(kata[:2])

    return f"{gelar}{nama_terambil}"


# ✅ Daftarkan filter baru ke Jinja
app.jinja_env.filters['nama_singkat_dropdown'] = nama_singkat_dropdown

# Inisialisasi Database
db.init_app(app)
migrate = Migrate(app, db)

# ==========================================
# 🔍 DETEKSI SISTEM — DARI SUBDOMAIN
# ==========================================
@app.before_request
def sebelum_permintaan():
    # =========================================================
    # LEWATI STATIC
    # =========================================================
    if request.path.startswith("/static"):
        return

    # =========================================================
    # ✅ TENTUKAN SISTEM DARI SUBDOMAIN
    # =========================================================
    host = request.host.lower()
    if host.startswith('absensi.'):
        g.sistem_mode = 'absensi'
    elif host.startswith('school.'):
        g.sistem_mode = 'sekolah'
    else:
        # Fallback: deteksi dari path jika bukan subdomain
        if (
            request.path.startswith('/absensi-guru') or 
            request.path.startswith('/login-absensi') or 
            request.path.startswith('/logout-absensi')
        ):
            g.sistem_mode = 'absensi'
        else:
            g.sistem_mode = 'sekolah'

    # =========================================================
    # HALAMAN LOGIN / LOGOUT — TIDAK PERLU CEK LOGIN
    # =========================================================
    if (
        request.path in [
            '/login',
            '/login-absensi',
            '/proses-login',
            '/logout-absensi'
        ]
    ):
        if g.sistem_mode == 'absensi':
            aktif = TahunPelajaran.query.filter_by(aktif=True).first()
            g.tahun_pelajaran = aktif.kode if aktif else "2025/2026"
        else:
            if "tahun_pelajaran" not in session:
                aktif = TahunPelajaran.query.filter_by(aktif=True).first()
                session["tahun_pelajaran"] = aktif.kode if aktif else "2025/2026"
            g.tahun_pelajaran = session["tahun_pelajaran"]
        return

    # =========================================================
    # CEK SESI SESUAI SISTEM
    # =========================================================
    if g.sistem_mode == 'absensi':
        sudah_login = (
            session.get('absensi_logged_in') is True
            and session.get('absensi_sistem_mode') == 'absensi'
            and session.get('absensi_user_id') is not None
        )
    else:
        sudah_login = (
            session.get('logged_in') is True
            and session.get('sistem_mode') == 'sekolah'
            and session.get('user_id') is not None
        )

    # =========================================================
    # JIKA BELUM LOGIN → ARAHKAN KE LOGIN SESUAI SUBDOMAIN
    # =========================================================
    if not sudah_login:
    # ⚠️ JANGAN mengalihkan jika SUDAH di halaman login
        if g.sistem_mode == 'absensi':
            if request.endpoint != 'absensi.login_absensi':
                flash('Silakan login terlebih dahulu untuk sistem absensi.', 'absensi_warning')
                return redirect(url_for('absensi.login_absensi'))
        else:
            if request.endpoint != 'login.halaman_login':
                flash('Silakan login terlebih dahulu untuk sistem utama.', 'warning')
                return redirect(url_for('login.halaman_login'))
            

    # =========================================================
    # SET TAHUN PELAJARAN
    # =========================================================
    if g.sistem_mode == 'absensi':
        aktif = TahunPelajaran.query.filter_by(aktif=True).first()
        g.tahun_pelajaran = aktif.kode if aktif else "2025/2026"
    else:
        if "tahun_pelajaran" not in session:
            aktif = TahunPelajaran.query.filter_by(aktif=True).first()
            session["tahun_pelajaran"] = aktif.kode if aktif else "2025/2026"
        g.tahun_pelajaran = session["tahun_pelajaran"]

        # =========================================================
    # ✅ AMBIL FOTO PROFIL & SIMPAN KE SESI
    # =========================================================
    from models import User, Guru  # Pastikan model sudah diimpor di atas, ini cadangan saja
    if g.sistem_mode == 'absensi':
        user_id = session.get('absensi_user_id')
    else:
        user_id = session.get('user_id')

    if user_id:
        akun = User.query.get(user_id)
        if akun and akun.guru:
            session['foto_profil'] = akun.guru.foto_profil
        else:
            session.pop('foto_profil', None)
    else:
        session.pop('foto_profil', None)

# ==========================================
# 📋 IMPOR & DAFTARKAN SEMUA BLUEPRINT
# ==========================================
from routes.login import login_bp
from routes.sections.dashboard import dashboard_bp
from routes.sections.data_guru import data_guru_bp
from routes.pengguna import pengguna_bp
from routes.sections.dashboard_dev import dev_bp
from routes.sections.tu.surat_menyurat import surat_bp as surat_tu_bp
from routes.surat import surat_bp as surat_global_bp
from routes.sections.kepsek.dashboard_kepsek import dashboard_kepsek_bp
from routes.sections.kepsek.agenda import agenda_bp
from routes.sections.guru.dashboard_guru import dashboard_guru_bp
from routes.umum import umum_bp
from routes.kalender_pendidikan import kalender_bp
from routes.sections.waka_kurikulum.dashboard_wakakur import bp as dashboard_wakakur_bp
from routes.siswa.data_siswa import data_siswa_bp
from routes.kelas.kelas import kelas_bp
from routes.ekstrakurikuler.ekstrakurikuler import data_ekskul_bp
from routes.ekstrakurikuler.peminatan import data_peminatan_bp
from routes.mapel.data_mapel import mapel_bp
from routes.sections.tu.laporan_administrasi import laporan_admin_bp
from routes.sections.admin.dashboard_admin import dashboard_admin_bp
from routes.sections.bendahara.bendahara import bendahara_bp

# --- ✅ BLUEPRINT SISTEM ABSENSI GURU ---
from routes.absensi.absensi import absensi_bp
from routes.absensi.absensi_guru import absensi_guru_bp
from routes.absensi.monitoring_absensi import monitoring_bp
from routes.profil import profil_bp

# --- Daftarkan Sistem Utama ---
app.register_blueprint(login_bp)
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(data_guru_bp)
app.register_blueprint(pengguna_bp)
app.register_blueprint(dev_bp, url_prefix='')
app.register_blueprint(surat_tu_bp)
app.register_blueprint(surat_global_bp)
app.register_blueprint(dashboard_kepsek_bp)
app.register_blueprint(agenda_bp)
app.register_blueprint(dashboard_guru_bp)
app.register_blueprint(umum_bp)
app.register_blueprint(kalender_bp)
app.register_blueprint(dashboard_wakakur_bp)
app.register_blueprint(data_siswa_bp)
app.register_blueprint(kelas_bp)
app.register_blueprint(mapel_bp)
app.register_blueprint(laporan_admin_bp)
app.register_blueprint(dashboard_admin_bp)
app.register_blueprint(bendahara_bp)
app.register_blueprint(data_ekskul_bp)
app.register_blueprint(data_peminatan_bp)
app.register_blueprint(absensi_bp)
app.register_blueprint(absensi_guru_bp, url_prefix='/absensi-guru')
app.register_blueprint(monitoring_bp)
app.register_blueprint(profil_bp)

# ✅ SISTEM ABSENSI — beri nama BERBEDA agar tidak bentrok
from routes.profil import profil_bp as absensi_profil_bp
app.register_blueprint(absensi_profil_bp, name='absensi_profil', url_prefix='/absensi-guru')

# ==========================================
# 📅 LOGIKA TAHUN PELAJARAN GLOBAL
# ==========================================
@app.context_processor
def tambah_model_ke_template():
    return dict(TahunPelajaran=TahunPelajaran)

# Buat tabel database jika belum ada
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)