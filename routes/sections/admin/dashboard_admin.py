from flask import Blueprint, render_template, session, redirect, url_for, request
from datetime import datetime
from models import User, TahunPelajaran, Siswa, Guru, Kelas

dashboard_admin_bp = Blueprint('dashboard_admin', __name__)

# ==============================================
# FUNGSI SAMA PERSIS DENGAN DATA_SISWA & KELAS
# ==============================================
def get_base_tahun(kode_tp):
    """Ubah format '2025/2026-1' jadi '2025/2026'"""
    if not kode_tp:
        return ""
    if '-' in kode_tp:
        kode_tp = kode_tp.split('-')[0]
    if ' ' in kode_tp:
        kode_tp = kode_tp.split(' ')[0]
    return kode_tp.strip()


@dashboard_admin_bp.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    user = User.query.get(session.get('user_id'))
    session['halaman_aktif'] = 'admin_sistem'

    # ==============================================
    # ✅ URUTAN AMBIL TAHUN SAMA PERSIS DENGAN HALAMAN SISWA
    # ==============================================
    kode_tahun_aktif = request.args.get('tahun') or session.get('tahun_pelajaran')
    if not kode_tahun_aktif:
        tahun_aktif_db = TahunPelajaran.query.filter_by(aktif=True).first()
        kode_tahun_aktif = tahun_aktif_db.kode if tahun_aktif_db else None

    # ==============================================
    # ✅ PROSES NAMA TAMPILAN & DASAR TAHUN
    # ==============================================
    nama_tahun = "Tidak Diketahui"
    nama_semester = "-"
    dasar_tahun = get_base_tahun(kode_tahun_aktif)

    if kode_tahun_aktif:
        tahun_obj = TahunPelajaran.query.filter_by(kode=kode_tahun_aktif).first()
        if tahun_obj:
            potong = tahun_obj.nama.replace('Tahun Pelajaran ', '').split(' - ')
            if len(potong) == 2:
                nomor_semester = potong[1].replace('Semester ', '')
                nama_semester = 'Ganjil' if nomor_semester == '1' else 'Genap'
                nama_tahun = potong[0]
            else:
                nama_tahun = tahun_obj.nama

    # ==============================================
    # ✅ HITUNG DATA PAKAI dasar_tahun (COCOK DATABASE)
    # ==============================================
    total_siswa = Siswa.query.filter_by(status='Aktif')
    total_kelas = Kelas.query

    if dasar_tahun:
        total_siswa = total_siswa.filter(Siswa.tahun_diterima.like(f"{dasar_tahun}%"))
        total_kelas = total_kelas.filter_by(tahun_pelajaran=dasar_tahun)

    total_siswa = total_siswa.count()
    total_guru = Guru.query.count()
    total_kelas = total_kelas.count()
    data_belum_lengkap = 3

    context = {
        'active_page': 'dashboard',
        'halaman_aktif': 'admin_sistem',
        'user': user,
        'user_name': session.get('user_name', 'Pengguna'),
        'user_role': session.get('jabatan', 'Admin Sistem'),
        'today_date': datetime.now().strftime('%d %B %Y'),
        'today_date_long': datetime.now().strftime('%A, %d %B %Y'),
        'tahun_ajaran': nama_tahun,
        'semester': nama_semester,
        'total_siswa': total_siswa,
        'total_guru': total_guru,
        'total_kelas': total_kelas,
        'data_belum_lengkap': data_belum_lengkap,
        'riwayat_perubahan': [
            {'waktu': '08.15', 'uraian': f'Penambahan data siswa tahun {nama_tahun}'},
            {'waktu': '07.40', 'uraian': 'Pembaruan data guru'},
            {'waktu': '07.10', 'uraian': f'Pengaturan tahun pelajaran {nama_tahun} - {nama_semester}'}
        ]
    }

    return render_template('sections/dashboard/dashboard_admin.html', **context)