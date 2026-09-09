from flask import Blueprint, render_template, session, redirect, url_for
from datetime import datetime
# ✅ Impor db dan modelnya, sama persis seperti di agenda.py
from models import db, AgendaKegiatan

dashboard_guru_bp = Blueprint('dashboard_guru', __name__)

@dashboard_guru_bp.route('/dashboard-guru')
def halaman_dashboard_guru():
    # Cek login dan peran
    if not session.get('logged_in') or session.get('role') != 'Guru':
        return redirect(url_for('login.halaman_login'))

    sekarang = datetime.now()

    daftar_agenda = AgendaKegiatan.query.order_by(AgendaKegiatan.tanggal_mulai.asc()).all()

    agenda_sekolah = []
    for a in daftar_agenda:

        if a.status != "Dibatalkan":
            if a.tanggal_mulai > sekarang:
                status = "Terjadwal"
            elif a.tanggal_selesai and a.tanggal_selesai < sekarang:
                status = "Selesai"
            else:
                status = "Berlangsung"
        else:
            status = "Dibatalkan"

        agenda_sekolah.append({
            'id': a.id,
            'judul': a.judul,
            'deskripsi': a.deskripsi,
            'tanggal_mulai': a.tanggal_mulai.isoformat(),
            'tanggal_selesai': a.tanggal_selesai.isoformat() if a.tanggal_selesai else a.tanggal_mulai.isoformat(),
            'lokasi': a.lokasi or "",
            'penanggung_jawab': a.penanggung_jawab or "",
            'status': status,
            'tgl_mulai_obj': a.tanggal_mulai,
            'tgl_selesai_obj': a.tanggal_selesai
        })

    # ✅ Sederhana saja: Semua Guru yang login boleh melihat kalender
    bisa_lihat_kalender = True

    context = {
        'active_page': 'dashboard_guru',
        'halaman_aktif': 'utama',
        'role': session.get('role'),
        'user_name': session.get('user_name'),
        # ✅ Tambahkan ini
        'user': {
            'jabatan': session.get('jabatan'),
            'nama': session.get('user_name'),
            'inisial': session.get('user_initials'),
            'tugas_tambahan': session.get('tugas_tambahan')
        },
        'today_date': sekarang.strftime('%d %b %Y'),
        'today_date_long': sekarang.strftime('%A, %d %B %Y'),
        'daftar_tugas': session.get('daftar_tugas', []),
        'agenda_sekolah': agenda_sekolah,
        'jumlah_mapel_diampu': 0,
        'jumlah_siswa_diajar': 0,
        'persen_kehadiran_mengajar': 0,
        'jumlah_jam_minggu': 0,
        'semester': 'Genap',
        'jadwal_hari_ini': [],
        'pengumuman': [],
        # ✅ Variabel dikirim ke template
        'bisa_lihat_kalender': bisa_lihat_kalender
    }

    return render_template('index.html', **context)