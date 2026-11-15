from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, g, flash
from datetime import datetime
from models import (
    db, Guru, User, MataPelajaran, PengaturanMapelKelas,
    JadwalPelajaran, Kelas, JurnalMengajar, TahunPelajaran,
    Siswa, RiwayatKelas, AbsensiJurnalMengajar
)

jurnal_mengajar_bp = Blueprint(
    'jurnal_mengajar',
    __name__,
    template_folder='../../templates',
    url_prefix='/jurnal-mengajar'
)

def guru_wajib(f):
    from functools import wraps
    @wraps(f)
    def decorator(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login.halaman_login'))
        if session.get('jabatan') != 'Guru' and session.get('role') != 'Guru':
            flash("<i class='fas fa-ban'></i> Halaman ini khusus guru", "danger")
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorator

@jurnal_mengajar_bp.route('/')
@guru_wajib
def halaman_jurnal():
    user_id = session.get('user_id')
    user_db = User.query.get(user_id) if user_id else None
    guru_data = user_db.guru if user_db else None
    
    if not guru_data:
        flash("<i class='fas fa-exclamation-triangle'></i> Data guru tidak ditemukan", "warning")
        return render_template('sections/guru/jurnal_mengajar.html', daftar_mapel=[])
    
    # Siapkan data user
    user = {
        'nama': session.get('user_name', 'Guru'),
        'gelar_depan': guru_data.gelar_depan if guru_data else None,
        'gelar_belakang': guru_data.gelar_belakang if guru_data else None,
        'jabatan': session.get('jabatan', session.get('role', '')),
        'tugas_tambahan': session.get('daftar_tugas', []),
        'inisial': session.get('user_initials', 'G')
    }
    
    halaman_aktif = 'utama'
    active_page = 'jurnal_mengajar'
    
    # Ambil tahun/semester aktif
    from models import TahunPelajaran
    tahun_aktif = TahunPelajaran.query.filter_by(aktif=True).first()
    kode_tahun = request.args.get('tahun') or session.get('tahun_pelajaran')
    if not kode_tahun and tahun_aktif:
        kode_tahun = tahun_aktif.kode
    
    # === KONEKSI DATA JADWAL YANG SUDAH DISETTING ===
    pengaturan_list = PengaturanMapelKelas.query.filter_by(
        guru_id=guru_data.id,
        tahun_pelajaran=kode_tahun
    ).all()
    
    daftar_mapel = []
    sudah_diproses = set()
    
    for aturan in pengaturan_list:

        # Ambil data berdasarkan foreign key secara langsung
        mapel = MataPelajaran.query.get(aturan.mata_pelajaran_id)
        kelas = Kelas.query.get(aturan.kelas_id)

        # Pastikan relasi masih memiliki data yang valid
        if not mapel or not kelas:
            current_app.logger.warning(
                f"Pengaturan mapel-kelas tidak valid: "
                f"ID aturan={aturan.id}, "
                f"mapel_id={aturan.mata_pelajaran_id}, "
                f"kelas_id={aturan.kelas_id}, "
                f"guru_id={guru_data.id}"
            )
            continue

        kunci = (mapel.id, kelas.id)

        if kunci in sudah_diproses:
            continue

        sudah_diproses.add(kunci)
        
        # Ambil jadwal pelajaran untuk mapel + kelas ini
        jadwal_list = JadwalPelajaran.query.filter_by(
            kelas_id=kelas.id,
            mata_pelajaran_id=mapel.id,
            tahun_pelajaran=kode_tahun
        ).order_by(
            db.case(
                (JadwalPelajaran.hari == 'Senin', 1),
                (JadwalPelajaran.hari == 'Selasa', 2),
                (JadwalPelajaran.hari == 'Rabu', 3),
                (JadwalPelajaran.hari == 'Kamis', 4),
                (JadwalPelajaran.hari == 'Jumat', 5),
                else_=99
            ),
            JadwalPelajaran.jam_mulai
        ).all()
        
        # Format jadwal untuk template
        jadwal_formatted = []
        for j in jadwal_list:
            jadwal_formatted.append({
                'hari': j.hari,
                'waktu_mulai': j.jam_mulai,
                'waktu_selesai': j.jam_selesai
            })
        
        # === HITUNG JUMLAH JURNAL & JURNAL TERAKHIR ===
        total_jurnal = JurnalMengajar.query.filter_by(
            guru_id=guru_data.id,
            mata_pelajaran_id=mapel.id,
            kelas_id=kelas.id,
            tahun_pelajaran=kode_tahun
        ).count()

        jurnal_terakhir = JurnalMengajar.query.filter_by(
            guru_id=guru_data.id,
            mata_pelajaran_id=mapel.id,
            kelas_id=kelas.id,
            tahun_pelajaran=kode_tahun
        ).order_by(JurnalMengajar.tanggal.desc()).first()

        daftar_mapel.append({
            'id': mapel.id,
            'nama_mapel': mapel.nama_pelajaran,
            'kode_mapel': mapel.kode,
            'kelas': kelas.nama_kelas,
            'kelas_id': kelas.id,
            'jadwal': jadwal_formatted,
            'total_jurnal': total_jurnal,
            'jurnal_terakhir': {
                'tanggal': jurnal_terakhir.tanggal.strftime('%d/%m/%Y') if jurnal_terakhir else '-',
                'materi': jurnal_terakhir.materi if jurnal_terakhir else '-'
            }
        })
    
    context = {
        'user': user,
        'halaman_aktif': halaman_aktif,
        'active_page': active_page,
        'daftar_mapel': daftar_mapel,
        'tahun_ajaran': kode_tahun,
        'semester': 'Ganjil' if kode_tahun and kode_tahun.endswith('-1') else 'Genap'
    }
    
    return render_template('sections/guru/jurnal_mengajar.html', **context)


@jurnal_mengajar_bp.route('/simpan', methods=['POST'])
@guru_wajib
def simpan_jurnal():

    try:
        # ==========================================
        # 1. IDENTITAS GURU
        # ==========================================
        user_id = session.get('user_id')
        user_db = User.query.get(user_id) if user_id else None
        guru_data = user_db.guru if user_db else None

        if not guru_data:
            flash('Data guru tidak ditemukan.', 'danger')
            return redirect(url_for('jurnal_mengajar.halaman_jurnal'))

        # ==========================================
        # 2. DATA FORM
        # ==========================================
        mapel_id = request.form.get('mapel_id', type=int)
        kelas_id = request.form.get('kelas_id', type=int)

        tanggal_input = (request.form.get('tanggal') or '').strip()
        jam_mulai_input = (request.form.get('jam_mulai') or '').strip()
        jam_selesai_input = (request.form.get('jam_selesai') or '').strip()

        materi = (request.form.get('materi') or '').strip()
        kegiatan = (request.form.get('kegiatan') or '').strip()
        metode = (request.form.get('metode') or '').strip()
        catatan = (request.form.get('catatan') or '').strip()

        halaman_kembali = (
            request.referrer
            or url_for('jurnal_mengajar.halaman_jurnal')
        )

        # ==========================================
        # 3. VALIDASI DATA WAJIB
        # ==========================================
        if not mapel_id or not kelas_id:
            flash('Mata pelajaran atau kelas tidak valid.', 'danger')
            return redirect(halaman_kembali)

        if not tanggal_input:
            flash('Tanggal jurnal wajib diisi.', 'warning')
            return redirect(halaman_kembali)

        if not jam_mulai_input or not jam_selesai_input:
            flash('Jam mulai dan jam selesai wajib diisi.', 'warning')
            return redirect(halaman_kembali)

        if not materi:
            flash('Materi pembelajaran wajib diisi.', 'warning')
            return redirect(halaman_kembali)

        # ==========================================
        # 4. VALIDASI FORMAT TANGGAL
        # ==========================================
        try:
            tanggal_jurnal = datetime.strptime(
                tanggal_input,
                '%Y-%m-%d'
            ).date()
        except (ValueError, TypeError):
            flash('Format tanggal jurnal tidak valid.', 'warning')
            return redirect(halaman_kembali)

        # ==========================================
        # 5. VALIDASI FORMAT JAM
        # ==========================================
        try:
            jam_mulai = datetime.strptime(
                jam_mulai_input,
                '%H:%M'
            ).strftime('%H:%M')

            jam_selesai = datetime.strptime(
                jam_selesai_input,
                '%H:%M'
            ).strftime('%H:%M')

        except (ValueError, TypeError):
            flash('Format jam mulai atau selesai tidak valid.', 'warning')
            return redirect(halaman_kembali)

        # ==========================================
        # 6. TAHUN PELAJARAN
        # ==========================================
        tahun_aktif = TahunPelajaran.query.filter_by(
            aktif=True
        ).first()

        kode_tahun = (
            session.get('tahun_pelajaran')
            or (tahun_aktif.kode if tahun_aktif else None)
        )

        if not kode_tahun:
            flash('Tahun pelajaran aktif tidak ditemukan.', 'danger')
            return redirect(halaman_kembali)

        # ==========================================
        # 7. VALIDASI PENUGASAN GURU
        # ==========================================
        penugasan = PengaturanMapelKelas.query.filter_by(
            guru_id=guru_data.id,
            mata_pelajaran_id=mapel_id,
            kelas_id=kelas_id,
            tahun_pelajaran=kode_tahun
        ).first()

        if not penugasan:
            flash(
                'Anda tidak memiliki penugasan mata pelajaran '
                'untuk kelas tersebut.',
                'danger'
            )
            return redirect(halaman_kembali)

        mapel = MataPelajaran.query.get(mapel_id)
        kelas = Kelas.query.get(kelas_id)

        if not mapel or not kelas:
            flash(
                'Data mata pelajaran atau kelas tidak ditemukan.',
                'danger'
            )
            return redirect(halaman_kembali)

        # ==========================================
        # 8. CEK JURNAL GANDA
        # ==========================================
        jurnal_lama = JurnalMengajar.query.filter_by(
            guru_id=guru_data.id,
            mata_pelajaran_id=mapel_id,
            kelas_id=kelas_id,
            tahun_pelajaran=kode_tahun,
            tanggal=tanggal_jurnal
        ).first()

        if jurnal_lama:
            flash(
                'Jurnal untuk mata pelajaran dan kelas ini '
                'pada tanggal tersebut sudah pernah dibuat.',
                'warning'
            )
            return redirect(halaman_kembali)

        # ==========================================
        # 9. CARI REFERENSI JADWAL
        # ==========================================
        # Tidak lagi memvalidasi hari atau jam berdasarkan jadwal.
        # Jadwal hanya menjadi referensi relasi jurnal.
        jadwal = JadwalPelajaran.query.filter_by(
            guru_id=guru_data.id,
            mata_pelajaran_id=mapel_id,
            kelas_id=kelas_id,
            tahun_pelajaran=kode_tahun
        ).first()

        if not jadwal:
            flash(
                'Referensi jadwal mata pelajaran tidak ditemukan.',
                'danger'
            )
            return redirect(halaman_kembali)

        # ==========================================
        # 10. SIMPAN JURNAL
        # ==========================================
        jurnal = JurnalMengajar(
            jadwal_id=jadwal.id,
            guru_id=guru_data.id,
            mata_pelajaran_id=mapel_id,
            kelas_id=kelas_id,
            tahun_pelajaran=kode_tahun,
            tanggal=tanggal_jurnal,

            # Kolom model menggunakan String(10).
            # Simpan sebagai string HH:MM, bukan datetime.time.
            jam_mulai=jam_mulai,
            jam_selesai=jam_selesai,

            materi=materi,
            kegiatan=kegiatan or None,
            metode=metode or None,
            catatan=catatan or None,
            status='jurnal_tersimpan'
        )


        db.session.add(jurnal)
        db.session.commit()

        current_app.logger.info(
            'Jurnal berhasil disimpan. ID jurnal: %s, Guru: %s, Kelas: %s',
            jurnal.id,
            guru_data.id,
            kelas.nama_kelas
        )

        flash(
            'Jurnal berhasil disimpan. Silakan lanjutkan absensi siswa.',
            'success'
        )

        # Langsung menuju halaman absensi untuk jurnal yang baru dibuat
        return redirect(
            url_for(
                'jurnal_mengajar.absensi_siswa',
                jurnal_id=jurnal.id
            )
        )

    except Exception as e:
        db.session.rollback()

        current_app.logger.exception(
            'Gagal menyimpan jurnal mengajar: %s', e
        )

        flash(
            'Terjadi kesalahan saat menyimpan jurnal. Silakan coba kembali.',
            'danger'
        )

        return redirect(
            request.referrer
            or url_for('jurnal_mengajar.halaman_jurnal')
        )



@jurnal_mengajar_bp.route('/riwayat/<int:mapel_id>')
@guru_wajib
def daftar_jurnal(mapel_id):

    # ==========================================
    # DATA GURU
    # ==========================================
    user_id = session.get('user_id')
    user_db = User.query.get(user_id) if user_id else None
    guru_data = user_db.guru if user_db else None

    if not guru_data:
        flash("Data guru tidak ditemukan.", "danger")
        return redirect(url_for('jurnal_mengajar.halaman_jurnal'))

    # ==========================================
    # TAHUN PELAJARAN
    # ==========================================
    tahun_aktif = TahunPelajaran.query.filter_by(
        aktif=True
    ).first()

    kode_tahun = (
        request.args.get('tahun')
        or session.get('tahun_pelajaran')
        or (tahun_aktif.kode if tahun_aktif else None)
    )

    if not kode_tahun:
        flash("Tahun pelajaran belum ditentukan.", "warning")
        return redirect(url_for('jurnal_mengajar.halaman_jurnal'))

    # ==========================================
    # VALIDASI MAPEL
    # ==========================================
    mapel = MataPelajaran.query.get(mapel_id)

    if not mapel:
        flash("Mata pelajaran tidak ditemukan.", "danger")
        return redirect(url_for('jurnal_mengajar.halaman_jurnal'))

    penugasan = PengaturanMapelKelas.query.filter_by(
        mata_pelajaran_id=mapel_id,
        guru_id=guru_data.id,
        tahun_pelajaran=kode_tahun
    ).first()

    if not penugasan:
        flash(
            "Kamu tidak memiliki penugasan mata pelajaran ini.",
            "danger"
        )
        return redirect(url_for('jurnal_mengajar.halaman_jurnal'))

    # ==========================================
    # AMBIL JURNAL
    # ==========================================
    daftar_jurnal = JurnalMengajar.query.filter_by(
        guru_id=guru_data.id,
        mata_pelajaran_id=mapel_id,
        tahun_pelajaran=kode_tahun
    ).order_by(
        JurnalMengajar.tanggal.desc(),
        JurnalMengajar.id.desc()
    ).all()

    # ==========================================
    # SIAPKAN REKAP JURNAL + ABSENSI
    # ==========================================
    riwayat_data = []

    total_hadir = 0
    total_sakit = 0
    total_izin = 0
    total_alpha = 0
    total_siswa_terdata = 0
    total_absensi_terisi = 0
    total_absensi_belum = 0
    total_sesi_lengkap = 0
    total_sesi_belum = 0
    total_sesi_sebagian = 0

    for jurnal in daftar_jurnal:

        # --------------------------------------
        # Nama kelas
        # --------------------------------------
        kelas = Kelas.query.get(jurnal.kelas_id)
        nama_kelas = kelas.nama_kelas if kelas else '-'

        # --------------------------------------
        # Jumlah siswa dalam kelas pada tahun
        # jurnal tersebut
        # --------------------------------------
        jumlah_siswa = RiwayatKelas.query.filter_by(
            kelas_id=jurnal.kelas_id,
            tahun_pelajaran=jurnal.tahun_pelajaran
        ).count()

        # --------------------------------------
        # Ambil rekap absensi
        # --------------------------------------
        absensi = AbsensiJurnalMengajar.query.filter_by(
            jurnal_id=jurnal.id
        ).all()

        jumlah_hadir = sum(
            1 for a in absensi if a.status == 'hadir'
        )
        jumlah_sakit = sum(
            1 for a in absensi if a.status == 'sakit'
        )
        jumlah_izin = sum(
            1 for a in absensi if a.status == 'izin'
        )
        jumlah_alpha = sum(
            1 for a in absensi if a.status == 'alpha'
        )

        jumlah_terisi = (
            jumlah_hadir
            + jumlah_sakit
            + jumlah_izin
            + jumlah_alpha
        )

        jumlah_belum = max(
            jumlah_siswa - jumlah_terisi,
            0
        )

        # --------------------------------------
        # Status penyelesaian absensi
        # --------------------------------------
        if jumlah_siswa == 0:
            status_absensi = 'tanpa_siswa'
            label_absensi = 'Data siswa kosong'

        elif jumlah_terisi == 0:
            status_absensi = 'belum'
            label_absensi = 'Belum diabsen'

        elif jumlah_terisi < jumlah_siswa:
            status_absensi = 'sebagian'
            label_absensi = 'Belum lengkap'

        else:
            status_absensi = 'lengkap'
            label_absensi = 'Absensi lengkap'

        # Persentase kelengkapan absensi
        persentase = (
            round((jumlah_terisi / jumlah_siswa) * 100)
            if jumlah_siswa > 0
            else 0
        )

        # --------------------------------------
        # Akumulasi statistik halaman
        # --------------------------------------
        total_hadir += jumlah_hadir
        total_sakit += jumlah_sakit
        total_izin += jumlah_izin
        total_alpha += jumlah_alpha

        total_siswa_terdata += jumlah_siswa
        total_absensi_terisi += jumlah_terisi
        total_absensi_belum += jumlah_belum

        if status_absensi == 'lengkap':
            total_sesi_lengkap += 1
        elif status_absensi == 'sebagian':
            total_sesi_sebagian += 1
        else:
            total_sesi_belum += 1

        # --------------------------------------
        # Data untuk template
        # --------------------------------------
        riwayat_data.append({
            'jurnal': jurnal,
            'nama_kelas': nama_kelas,

            'jumlah_siswa': jumlah_siswa,
            'jumlah_terisi': jumlah_terisi,
            'jumlah_belum': jumlah_belum,

            'jumlah_hadir': jumlah_hadir,
            'jumlah_sakit': jumlah_sakit,
            'jumlah_izin': jumlah_izin,
            'jumlah_alpha': jumlah_alpha,

            'persentase': persentase,
            'status_absensi': status_absensi,
            'label_absensi': label_absensi
        })

    # ==========================================
    # DATA USER
    # ==========================================
    user = {
        'nama': session.get('user_name', 'Guru'),
        'gelar_depan': guru_data.gelar_depan,
        'gelar_belakang': guru_data.gelar_belakang,
        'jabatan': session.get(
            'jabatan',
            session.get('role', '')
        ),
        'tugas_tambahan': session.get('daftar_tugas', []),
        'inisial': session.get('user_initials', 'G')
    }

    # ==========================================
    # STATISTIK
    # ==========================================
    total_jurnal = len(daftar_jurnal)

    jurnal_terbaru = (
        daftar_jurnal[0]
        if daftar_jurnal
        else None
    )

    persentase_absensi = (
        round(
            (total_absensi_terisi / total_siswa_terdata) * 100
        )
        if total_siswa_terdata > 0
        else 0
    )

    # ==========================================
    # CONTEXT
    # ==========================================
    context = {
        'user': user,
        'halaman_aktif': 'utama',
        'active_page': 'jurnal_mengajar',

        'mapel': mapel,
        'daftar_jurnal': daftar_jurnal,
        'riwayat_data': riwayat_data,

        'total_jurnal': total_jurnal,
        'jurnal_terbaru': jurnal_terbaru,

        'total_hadir': total_hadir,
        'total_sakit': total_sakit,
        'total_izin': total_izin,
        'total_alpha': total_alpha,

        'total_siswa_terdata': total_siswa_terdata,
        'total_absensi_terisi': total_absensi_terisi,
        'total_absensi_belum': total_absensi_belum,

        'total_sesi_lengkap': total_sesi_lengkap,
        'total_sesi_sebagian': total_sesi_sebagian,
        'total_sesi_belum': total_sesi_belum,

        'persentase_absensi': persentase_absensi,

        'tahun_ajaran': kode_tahun,
        'semester': (
            'Ganjil'
            if kode_tahun.endswith('-1')
            else 'Genap'
        )
    }

    return render_template(
        'sections/guru/riwayat_jurnal.html',
        **context
    )
