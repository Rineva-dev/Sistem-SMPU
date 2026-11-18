
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, session, flash
)
from datetime import date
from calendar import monthrange

from sqlalchemy.orm import selectinload

from models import (
    db, User, Guru, Kelas, Siswa,
    TahunPelajaran, RiwayatKelas,
    JurnalMengajar, AbsensiJurnalMengajar
)


rekap_kehadiran_bp = Blueprint(
    'rekap_kehadiran',
    __name__,
    url_prefix='/wali-kelas'
)


@rekap_kehadiran_bp.route('/rekap-kehadiran')
def index():
    # =========================================
    # 1. VALIDASI LOGIN DAN WORKSPACE
    # =========================================
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    if session.get('halaman_aktif') != 'wali_kelas':
        flash("Silakan masuk ke workspace Wali Kelas.", "warning")
        return redirect(url_for('dashboard.pindah_halaman'))

    user = db.session.get(User, session.get('user_id'))

    if not user or not user.guru_id:
        flash("Akun belum terhubung dengan data guru.", "danger")
        return redirect(url_for('dashboard_wali.index'))

    guru = db.session.get(Guru, user.guru_id)

    if not guru:
        flash("Data guru tidak ditemukan.", "danger")
        return redirect(url_for('dashboard_wali.index'))

    # =========================================
    # 2. TAHUN PELAJARAN AKTIF
    # =========================================
    tahun_aktif = (
        TahunPelajaran.query
        .filter_by(aktif=True)
        .order_by(TahunPelajaran.id.desc())
        .first()
    )

    if not tahun_aktif:
        flash("Tahun pelajaran aktif belum tersedia.", "warning")
        return redirect(url_for('dashboard_wali.index'))

    kode_tp = tahun_aktif.kode
    tahun_dasar = kode_tp.split('-')[0].strip()

    # =========================================
    # 3. KELAS BINAAN WALI KELAS
    # =========================================
    daftar_kelas = (
        Kelas.query
        .filter(
            Kelas.wali_kelas_id == guru.id,
            Kelas.tahun_pelajaran == tahun_dasar
        )
        .order_by(Kelas.nama_kelas.asc())
        .all()
    )

    if not daftar_kelas:
        return render_template(
            'sections/wali_kelas/rekap_kehadiran.html',
            guru=guru,
            tahun_pelajaran=tahun_aktif,
            daftar_kelas=[],
            kelas_terpilih=None,
            daftar_siswa=[],
            statistik={
                'hadir': 0,
                'sakit': 0,
                'izin': 0,
                'alpha': 0,
                'total': 0
            },
            tanggal_mulai='',
            tanggal_selesai='',
            active_page='rekap_kehadiran_wali',
            halaman_aktif='wali_kelas'
        )

    # =========================================
    # 4. FILTER KELAS DAN TANGGAL
    # =========================================
    kelas_id = request.args.get('kelas_id', type=int)

    kelas_terpilih = next(
        (k for k in daftar_kelas if k.id == kelas_id),
        daftar_kelas[0]
    )

    hari_ini = date.today()
    awal_bulan = hari_ini.replace(day=1)
    akhir_bulan = hari_ini.replace(
        day=monthrange(hari_ini.year, hari_ini.month)[1]
    )

    tanggal_mulai_input = request.args.get('mulai', '')
    tanggal_selesai_input = request.args.get('sampai', '')

    try:
        tanggal_mulai = (
            date.fromisoformat(tanggal_mulai_input)
            if tanggal_mulai_input
            else awal_bulan
        )
        tanggal_selesai = (
            date.fromisoformat(tanggal_selesai_input)
            if tanggal_selesai_input
            else akhir_bulan
        )
    except ValueError:
        flash("Format tanggal tidak valid.", "warning")
        tanggal_mulai = awal_bulan
        tanggal_selesai = akhir_bulan

    if tanggal_mulai > tanggal_selesai:
        tanggal_mulai, tanggal_selesai = (
            tanggal_selesai,
            tanggal_mulai
        )

    # =========================================
    # 5. AMBIL SISWA KELAS TERPILIH
    # =========================================
    daftar_siswa = (
        Siswa.query
        .join(
            RiwayatKelas,
            RiwayatKelas.siswa_id == Siswa.id
        )
        .filter(
            RiwayatKelas.tahun_pelajaran == kode_tp,
            RiwayatKelas.kelas_id == kelas_terpilih.id
        )
        .order_by(Siswa.nama.asc())
        .all()
    )

    # =========================================
    # 6. AMBIL JURNAL DAN DATA KEHADIRAN
    # =========================================
    daftar_jurnal = (
        JurnalMengajar.query
        .options(
            selectinload(JurnalMengajar.daftar_absensi)
        )
        .filter(
            JurnalMengajar.kelas_id == kelas_terpilih.id,
            JurnalMengajar.tahun_pelajaran == kode_tp,
            JurnalMengajar.tanggal >= tanggal_mulai,
            JurnalMengajar.tanggal <= tanggal_selesai
        )
        .order_by(
            JurnalMengajar.tanggal.desc(),
            JurnalMengajar.jam_mulai.desc()
        )
        .all()
    )

    # =========================================
    # 7. HITUNG REKAP SETIAP SISWA
    # =========================================
    rekap = {}

    for siswa in daftar_siswa:
        rekap[siswa.id] = {
            'siswa': siswa,
            'hadir': 0,
            'sakit': 0,
            'izin': 0,
            'alpha': 0,
            'total': 0,
            'persentase': 0
        }

    statistik = {
        'hadir': 0,
        'sakit': 0,
        'izin': 0,
        'alpha': 0,
        'total': 0
    }

    riwayat = []

    for jurnal in daftar_jurnal:
        for absensi in jurnal.daftar_absensi:
            if absensi.siswa_id not in rekap:
                continue

            status = (absensi.status or '').lower()

            if status not in ('hadir', 'sakit', 'izin', 'alpha'):
                continue

            rekap[absensi.siswa_id][status] += 1
            rekap[absensi.siswa_id]['total'] += 1

            statistik[status] += 1
            statistik['total'] += 1

            riwayat.append({
                'tanggal': jurnal.tanggal,
                'jam_mulai': jurnal.jam_mulai,
                'jam_selesai': jurnal.jam_selesai,
                'mata_pelajaran': jurnal.mata_pelajaran.nama_pelajaran if jurnal.mata_pelajaran else '-',
                'guru': jurnal.guru.nama
                    if jurnal.guru else '-',
                'siswa': absensi.siswa,
                'status': status,
                'keterangan': absensi.keterangan
            })

    daftar_rekap = list(rekap.values())

    for item in daftar_rekap:
        total = item['total']

        item['persentase'] = (
            round(item['hadir'] / total * 100, 1)
            if total else 0
        )

    daftar_rekap.sort(
        key=lambda item: item['siswa'].nama.lower()
    )

    # =========================================
    # 8. RENDER HALAMAN
    # =========================================
    return render_template(
        'sections/wali_kelas/rekap_kehadiran.html',
        user={
            'jabatan': session.get('jabatan', ''),
            'tugas_tambahan': session.get('tugas_tambahan', '')
        },
        guru=guru,
        tahun_pelajaran=tahun_aktif,
        daftar_kelas=daftar_kelas,
        kelas_terpilih=kelas_terpilih,
        daftar_siswa=daftar_rekap,
        daftar_jurnal=daftar_jurnal,
        riwayat=riwayat,
        statistik=statistik,
        tanggal_mulai=tanggal_mulai.isoformat(),
        tanggal_selesai=tanggal_selesai.isoformat(),
        active_page='rekap_kehadiran_wali',
        halaman_aktif='wali_kelas'
    )
