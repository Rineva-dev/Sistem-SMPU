from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, g, flash
from datetime import datetime
from models import (
    db, Guru, User, MataPelajaran, PengaturanMapelKelas,
    JadwalPelajaran, Kelas, JurnalMengajar  # Pastikan model JurnalMengajar sudah ada
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
        mapel = aturan.mata_pelajaran
        kelas = aturan.kelas
        
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
    user_id = session.get('user_id')
    user_db = User.query.get(user_id)
    guru_data = user_db.guru if user_db else None
    
    if not guru_data:
        flash("<i class='fas fa-exclamation-triangle'></i> Data guru tidak ditemukan", "danger")
        return redirect(url_for('jurnal_mengajar.halaman_jurnal'))
    
    mapel_id = request.form.get('mapel_id')
    tanggal = request.form.get('tanggal')
    jam_pelajaran = request.form.get('jam_pelajaran')
    materi = request.form.get('materi', '').strip()
    kegiatan = request.form.get('kegiatan', '').strip()
    metode = request.form.get('metode', '').strip()
    kehadiran = request.form.get('kehadiran', '').strip()
    catatan = request.form.get('catatan', '').strip()
    
    if not mapel_id or not tanggal or not jam_pelajaran or not materi:
        flash("<i class='fas fa-times-circle'></i> Tanggal, Jam Pelajaran, dan Materi wajib diisi!", "danger")
        return redirect(url_for('jurnal_mengajar.halaman_jurnal'))
    
    # Ambil info kelas dari pengaturan mapel
    kode_tahun = session.get('tahun_pelajaran')
    aturan = PengaturanMapelKelas.query.filter_by(
        mata_pelajaran_id=mapel_id,
        guru_id=guru_data.id,
        tahun_pelajaran=kode_tahun
    ).first()
    
    kelas_id = aturan.kelas_id if aturan else None
    
    # Simpan jurnal
    jurnal_baru = JurnalMengajar(
        guru_id=guru_data.id,
        mata_pelajaran_id=mapel_id,
        kelas_id=kelas_id,
        tanggal=datetime.strptime(tanggal, '%Y-%m-%d').date(),
        jam_pelajaran=jam_pelajaran,
        materi=materi,
        kegiatan=kegiatan,
        metode=metode,
        kehadiran=kehadiran,
        catatan=catatan,
        tahun_pelajaran=kode_tahun
    )
    
    db.session.add(jurnal_baru)
    db.session.commit()
    
    flash("<i class='fas fa-check-circle'></i> Jurnal mengajar berhasil disimpan!", "success")
    return redirect(url_for('jurnal_mengajar.daftar_jurnal', mapel_id=mapel_id))

@jurnal_mengajar_bp.route('/riwayat/<int:mapel_id>')
@guru_wajib
def daftar_jurnal(mapel_id):
    user_id = session.get('user_id')
    user_db = User.query.get(user_id)
    guru_data = user_db.guru if user_db else None
    
    kode_tahun = request.args.get('tahun') or session.get('tahun_pelajaran')
    
    daftar_jurnal = JurnalMengajar.query.filter_by(
        guru_id=guru_data.id,
        mata_pelajaran_id=mapel_id,
        tahun_pelajaran=kode_tahun
    ).order_by(JurnalMengajar.tanggal.desc()).all()
    
    mapel = MataPelajaran.query.get(mapel_id)
    
    return render_template(
        'sections/guru/riwayat_jurnal.html',
        daftar_jurnal=daftar_jurnal,
        mapel=mapel,
        tahun_ajaran=kode_tahun,
        active_page='jurnal_mengajar',
        halaman_aktif='utama'
    )