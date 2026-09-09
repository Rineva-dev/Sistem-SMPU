from flask import Blueprint, render_template, session, redirect, url_for, request
from models import TahunPelajaran, User

# === DEFINISI BLUEPRINT ===
laporan_admin_bp = Blueprint(
    'laporan_administrasi',
    __name__,
    url_prefix='/laporan-administrasi'
)

# === FUNGSI BANTU: SAMA PERSIS DENGAN HALAMAN KELAS ===
def get_base_tahun(kode_tp):
    """Ubah format '2025/2026-1' atau '2025/2026 Ganjil' jadi '2025/2026'"""
    if not kode_tp:
        return ""
    if '-' in kode_tp:
        kode_tp = kode_tp.split('-')[0]
    if ' ' in kode_tp:
        kode_tp = kode_tp.split(' ')[0]
    return kode_tp.strip()

# === RUTE UTAMA HALAMAN LAPORAN ===
@laporan_admin_bp.route('/')
def halaman_laporan():
    """
    Menampilkan daftar menu laporan administrasi untuk Tata Usaha
    """
    # Cek apakah sudah login
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    # ✅ AMBIL DATA PENGGUNA ASLI DARI DATABASE (SAMA PERSIS DENGAN RUTE KELAS)
    user = User.query.get(session.get('user_id'))

    # Cek hak akses
    daftar_jabatan_izin = ["Tata Usaha", "TU", "Kepala Sekolah", "Admin"]
    jabatan_sekarang = session.get('jabatan', session.get('role', ''))
    if jabatan_sekarang not in daftar_jabatan_izin:
        return "Anda tidak memiliki izin mengakses halaman ini!", 403

    # ✅ AMBIL TAHUN PELAJARAN: SAMA LOGIKANYA DENGAN HALAMAN KELAS
    tahun_aktif = TahunPelajaran.query.filter_by(aktif=True).first()
    kode_tahun_dipilih = request.args.get('tahun') or session.get('tahun_pelajaran')
    if not kode_tahun_dipilih and tahun_aktif:
        kode_tahun_dipilih = tahun_aktif.kode
    dasar_tahun = get_base_tahun(kode_tahun_dipilih) if kode_tahun_dipilih else ""

    # ✅ KIRIM DATA LENGKAP & BENAR KE TEMPLATE
    context = {
        'active_page': 'laporan_sekolah',
        'halaman_aktif': session.get('halaman_aktif', 'utama'),
        'role': jabatan_sekarang,
        'user': user,  # <-- KIRIM OBJEK ASLI DARI TABEL USER, BUKAN BUATAN SENDIRI
        'tahun_dipilih': kode_tahun_dipilih,
        'dasar_tahun': dasar_tahun
    }

    return render_template('index.html', **context)