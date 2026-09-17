from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, g
from datetime import datetime
from models import db, Guru, User  # Tambahkan import yang dibutuhkan

jurnal_mengajar_bp = Blueprint(
    'jurnal_mengajar',
    __name__,
    template_folder='../../templates',  # Sesuaikan path ke folder templates
    url_prefix='/jurnal-mengajar'
)

@jurnal_mengajar_bp.route('/')
def halaman_jurnal():
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))
    
    # Ambil data user seperti di halaman lain
    user_id = session.get('user_id')
    user_db = User.query.get(user_id) if user_id else None
    guru_data = user_db.guru if user_db else None
    
    # Siapkan variabel user untuk sidebar
    user = {
        'nama': session.get('user_name', 'Guru'),
        'gelar_depan': guru_data.gelar_depan if guru_data else None,
        'gelar_belakang': guru_data.gelar_belakang if guru_data else None,
        'jabatan': session.get('role', ''),
        'tugas_tambahan': session.get('daftar_tugas', []),
        'inisial': session.get('user_initials', 'G')
    }
    
    # Tentukan halaman aktif
    halaman_aktif = 'utama'
    active_page = 'jurnal_mengajar'
    
    # TODO: Ganti dengan data asli dari tabel Jadwal/MataPelajaran
    daftar_mapel = [
        {
            "id": 1,
            "nama_mapel": "Matematika",
            "kelas": "X - IPA 1",
            "jadwal": [
                {"hari": "Senin", "waktu_mulai": "07:00", "waktu_selesai": "08:30"},
                {"hari": "Kamis", "waktu_mulai": "09:00", "waktu_selesai": "10:30"}
            ]
        }
    ]
    
    context = {
        'user': user,
        'halaman_aktif': halaman_aktif,
        'active_page': active_page,
        'daftar_mapel': daftar_mapel,
        'tahun_ajaran': g.tahun_pelajaran if hasattr(g, 'tahun_pelajaran') else '2025/2026',
        'semester': 'Genap'
    }
    
    return render_template('sections/guru/jurnal_mengajar.html', **context)


@jurnal_mengajar_bp.route('/simpan', methods=['POST'])
def simpan_jurnal():
    if not session.get('logged_in') or session.get('role') != 'Guru':
        return redirect(url_for('login.halaman_login'))
    
    # ... nanti dilengkapi
    return redirect(url_for('jurnal_mengajar.halaman_jurnal'))


@jurnal_mengajar_bp.route('/riwayat/<int:mapel_id>')
def daftar_jurnal(mapel_id):
    # ... nanti dilengkapi
    return "Riwayat jurnal"