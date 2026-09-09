from flask import Blueprint, render_template, session, redirect, url_for
from datetime import datetime, timedelta
from models import db, User, TahunPelajaran, KalenderPendidikan, AgendaKegiatan

bp = Blueprint('dashboard_wakakur', __name__, url_prefix='/dashboard-wakakur')

@bp.route('/')
def halaman_dashboard_wakakur():
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('login.halaman_login'))

    sekarang = datetime.now()
    user_name = user.guru.nama if (user.guru and hasattr(user, 'guru')) else user.username
    daftar_tugas = user.tugas_tambahan.split(',') if (user.tugas_tambahan and isinstance(user.tugas_tambahan, str)) else []

    # Data Tahun Pelajaran & Semester
    tp_aktif = TahunPelajaran.query.filter_by(aktif=True).first()
    semester_aktif = 'ganjil' if (tp_aktif and tp_aktif.semester == 1) else 'genap'

    total_kegiatan = 0
    total_hari_efektif = 0
    hari_menuju_ujian = 0
    persen_kelengkapan_kalender = 0
    persen_disetujui = 0
    kalender_siap = False
    agenda_kurikulum = []

    if tp_aktif:
        total_kegiatan = KalenderPendidikan.query.filter_by(tahun_pelajaran_id=tp_aktif.id).count()

        if semester_aktif == 'ganjil':
            mulai = tp_aktif.tanggal_mulai
            selesai = datetime(tp_aktif.tahun_mulai, 12, 31).date()
        else:
            mulai = datetime(tp_aktif.tahun_selesai, 1, 1).date()
            selesai = tp_aktif.tanggal_selesai

        if mulai and selesai:
            total_hari_efektif = max(0, (selesai - mulai).days)
            if selesai > sekarang.date():
                hari_menuju_ujian = max(0, (selesai - sekarang.date()).days)

        if total_kegiatan > 0:
            persen_kelengkapan_kalender = round(min((total_kegiatan / 15) * 100, 100), 1)
            sudah_disetujui = KalenderPendidikan.query.filter_by(tahun_pelajaran_id=tp_aktif.id, disetujui=True).count()
            persen_disetujui = round((sudah_disetujui / total_kegiatan) * 100, 1)

        kalender_siap = total_kegiatan >= 10

        agenda_kurikulum = AgendaKegiatan.query.filter(
            AgendaKegiatan.tahun_pelajaran == tp_aktif.kode,
            AgendaKegiatan.tanggal_mulai >= (sekarang - timedelta(days=30))
        ).order_by(AgendaKegiatan.tanggal_mulai.asc()).limit(5).all()

        for a in agenda_kurikulum:
            a.tgl_mulai_obj = a.tanggal_mulai

    # ✅ PINDAHKAN INI KE LUAR, SELALU DIJALANKAN
    return render_template(
        'index.html',
        active_page = "dashboard_wakakur",
        halaman_aktif = "waka_kurikulum",

        user = {
            'nama': user_name,
            'jabatan': session.get('role', 'Waka Kurikulum'),
            'tugas_tambahan': ", ".join(daftar_tugas) if daftar_tugas else "-",
            'inisial': session.get('user_initials', 'WK')
        },
        user_name = user_name,
        user_role = session.get('user_role', 'Waka Kurikulum'),
        role = session.get('role', 'Waka Kurikulum'),
        daftar_tugas = daftar_tugas,
        user_initials = session.get('user_initials', 'WK'),

        today_date = sekarang.strftime('%d %B %Y'),
        today_date_long = sekarang.strftime('%A, %d %B %Y'),
        tahun_ajaran = tp_aktif.nama if tp_aktif else 'Belum diatur',
        semester = semester_aktif.capitalize(),

        semester_aktif = semester_aktif,
        tahun_pelajaran_nama = tp_aktif.nama if tp_aktif else 'Belum Ada',
        total_kegiatan = total_kegiatan,
        total_hari_efektif = total_hari_efektif,
        persen_kelengkapan_kalender = persen_kelengkapan_kalender,
        hari_menuju_ujian = hari_menuju_ujian,
        persen_disetujui = persen_disetujui,
        kalender_siap = kalender_siap,
        agenda_kurikulum = agenda_kurikulum
    )