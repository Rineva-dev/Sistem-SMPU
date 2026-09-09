from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models import db, Peminatan, JurnalPeminatan, User, Guru, Siswa, TahunPelajaran, BulanLiburPeminatan, AbsensiJurnalPeminatan
from functools import wraps
from datetime import datetime

data_peminatan_bp = Blueprint('data_peminatan', __name__)

# ==============================================
# FUNGSI BANTU
# ==============================================
def get_base_tahun(kode_tp):
    """Ubah format '2025/2026-1' atau '2025/2026 Ganjil' jadi '2025/2026'"""
    if not kode_tp:
        return ""
    if '-' in kode_tp:
        kode_tp = kode_tp.split('-')[0]
    if ' ' in kode_tp:
        kode_tp = kode_tp.split(' ')[0]
    return kode_tp.strip()

# ==============================================
# ✅ FUNGSI HITUNG STATUS: SUDAH SESUAI HTML
# ==============================================
def hitung_status_kegiatan(data):
    hari_ini = datetime.today().date()

    # Cek dulu Bulan Libur
    libur = BulanLiburPeminatan.query.filter(
        BulanLiburPeminatan.peminatan_id == data.id,
        BulanLiburPeminatan.bulan == hari_ini.month,
        BulanLiburPeminatan.tahun == hari_ini.year
    ).first()

    if libur:
        return "libur"

    # Hitung berdasarkan rentang tanggal
    if hari_ini < data.tgl_mulai:
        return "belum"
    elif data.tgl_mulai <= hari_ini <= data.tgl_selesai:
        return "aktif"
    else:
        return "selesai"

# --------------------------
# Cek Hak Akses
# --------------------------
def bisa_kelola_peminatan(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login.halaman_login'))
        jabatan = session.get('jabatan', '')
        tugas = session.get('tugas_tambahan', '')
        daftar_tugas = [t.strip() for t in tugas.split(',')] if tugas else []
        if jabatan not in ["Admin", "Tata Usaha", "TU", "Waka Kurikulum", "Waka Kesiswaan", "Pembina Peminatan"] and "Admin Sistem" not in daftar_tugas:
            flash("Anda tidak memiliki hak akses untuk mengelola data ini", "danger")
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorator

# --------------------------
# Halaman Daftar Peminatan
# --------------------------
@data_peminatan_bp.route('/data-peminatan')
@bisa_kelola_peminatan
def halaman():
    user = User.query.get(session.get('user_id'))
    semua_tahun = TahunPelajaran.query.order_by(TahunPelajaran.kode.desc()).all()
    tahun_aktif = TahunPelajaran.query.filter_by(aktif=True).first()

    kode_tahun_dipilih = session.get('tahun_pelajaran') or request.args.get('tahun')
    if not kode_tahun_dipilih and tahun_aktif:
        kode_tahun_dipilih = tahun_aktif.kode

    tp_dipilih = TahunPelajaran.query.filter_by(kode=kode_tahun_dipilih).first()
    tgl_min = tp_dipilih.tanggal_mulai.strftime('%Y-%m-%d') if tp_dipilih else ""
    tgl_max = tp_dipilih.tanggal_selesai.strftime('%Y-%m-%d') if tp_dipilih else ""

    daftar_peminatan = []
    if kode_tahun_dipilih:
        daftar_peminatan = Peminatan.query.filter_by(
            tahun_pelajaran=kode_tahun_dipilih
        ).order_by(Peminatan.nama).all()

    for p in daftar_peminatan:
        p.status_otomatis = hitung_status_kegiatan(p)

    daftar_guru = Guru.query.order_by(Guru.nama).all()
    semua_siswa = Siswa.query.filter_by(status='Aktif').order_by(Siswa.nama).all()

    return render_template('index.html',
                            user=user,
                            user_name=session.get('user_name'),
                            jabatan=session.get('jabatan'),
                            daftar_tugas=[t.strip() for t in session.get('tugas_tambahan','').split(',')],
                            halaman_aktif=session.get('halaman_aktif', 'utama'),
                            active_page='data_peminatan',
                            tahun_dipilih=kode_tahun_dipilih,
                            semua_tahun=semua_tahun,
                            daftar_peminatan=daftar_peminatan,
                            daftar_guru=daftar_guru,
                            semua_siswa=semua_siswa,
                            tgl_min=tgl_min,
                            tgl_max=tgl_max)

# --------------------------
# Tambah Peminatan
# --------------------------
@data_peminatan_bp.route('/data-peminatan/tambah', methods=['POST'])
@bisa_kelola_peminatan
def tambah():
    nama = request.form.get('nama', '').strip()
    pembina_id = request.form.get('pembina_id') or None
    keterangan = request.form.get('keterangan', '').strip()

    tgl_mulai_str = request.form.get('tgl_mulai')
    tgl_selesai_str = request.form.get('tgl_selesai')
    tgl_mulai = datetime.strptime(tgl_mulai_str, '%Y-%m-%d').date() if tgl_mulai_str else None
    tgl_selesai = datetime.strptime(tgl_selesai_str, '%Y-%m-%d').date() if tgl_selesai_str else None

    kode_tahun_dipilih = request.form.get('tahun_pelajaran', '').strip()
    if not kode_tahun_dipilih:
        kode_tahun_dipilih = (request.args.get('tahun') or session.get('tahun_pelajaran', '')).strip()

    if not kode_tahun_dipilih:
        flash("Pilih Tahun Pelajaran terlebih dahulu!", "warning")
        return redirect(url_for('data_peminatan.halaman'))

    if not nama:
        flash('Nama peminatan tidak boleh kosong!', 'danger')
        return redirect(url_for('data_peminatan.halaman', tahun=kode_tahun_dipilih))

    cek = Peminatan.query.filter_by(nama=nama, tahun_pelajaran=kode_tahun_dipilih).first()
    if cek:
        flash(f'Peminatan {nama} sudah ada di periode ini!', 'warning')
        return redirect(url_for('data_peminatan.halaman', tahun=kode_tahun_dipilih))

    baru = Peminatan(
        nama=nama, pembina_id=pembina_id, keterangan=keterangan,
        tgl_mulai=tgl_mulai, tgl_selesai=tgl_selesai,
        tahun_pelajaran=kode_tahun_dipilih
    )

    tp_aktif = TahunPelajaran.query.filter_by(kode=kode_tahun_dipilih).first()
    if tp_aktif:
        if tgl_mulai:
            if tgl_mulai < tp_aktif.tanggal_mulai or tgl_mulai > tp_aktif.tanggal_selesai:
                flash(f'Tanggal mulai harus antara {tp_aktif.tanggal_mulai.strftime("%d/%m/%Y")} - {tp_aktif.tanggal_selesai.strftime("%d/%m/%Y")}', 'danger')
                return redirect(url_for('data_peminatan.halaman', tahun=kode_tahun_dipilih))
        if tgl_selesai:
            if tgl_selesai < tp_aktif.tanggal_mulai or tgl_selesai > tp_aktif.tanggal_selesai:
                flash(f'Tanggal selesai harus antara {tp_aktif.tanggal_mulai.strftime("%d/%m/%Y")} - {tp_aktif.tanggal_selesai.strftime("%d/%m/%Y")}', 'danger')
                return redirect(url_for('data_peminatan.halaman', tahun=kode_tahun_dipilih))
        if tgl_mulai and tgl_selesai and tgl_selesai < tgl_mulai:
            flash('Tanggal selesai tidak boleh lebih awal dari tanggal mulai!', 'danger')
            return redirect(url_for('data_peminatan.halaman', tahun=kode_tahun_dipilih))

    db.session.add(baru)
    db.session.commit()
    flash('Data berhasil ditambahkan!', 'success')
    return redirect(url_for('data_peminatan.halaman', tahun=kode_tahun_dipilih))

# --------------------------
# Ubah Peminatan
# --------------------------
@data_peminatan_bp.route('/data-peminatan/ubah/<int:id>', methods=['POST'])
@bisa_kelola_peminatan
def ubah(id):
    peminatan = Peminatan.query.get_or_404(id)
    nama = request.form.get('nama', '').strip()
    pembina_id = request.form.get('pembina_id') or None
    keterangan = request.form.get('keterangan', '').strip()

    tgl_mulai_str = request.form.get('tgl_mulai')
    tgl_selesai_str = request.form.get('tgl_selesai')
    peminatan.tgl_mulai = datetime.strptime(tgl_mulai_str, '%Y-%m-%d').date() if tgl_mulai_str else None
    peminatan.tgl_selesai = datetime.strptime(tgl_selesai_str, '%Y-%m-%d').date() if tgl_selesai_str else None

    kode_tahun_dipilih = request.form.get('tahun_pelajaran', '').strip()
    if not kode_tahun_dipilih:
        kode_tahun_dipilih = (request.args.get('tahun') or session.get('tahun_pelajaran', '')).strip()

    if not kode_tahun_dipilih:
        flash("Pilih Tahun Pelajaran terlebih dahulu!", "warning")
        return redirect(url_for('data_peminatan.halaman'))

    if not nama:
        flash('Nama peminatan tidak boleh kosong!', 'danger')
        return redirect(url_for('data_peminatan.halaman', tahun=kode_tahun_dipilih))

    cek = Peminatan.query.filter(
        Peminatan.nama == nama,
        Peminatan.tahun_pelajaran == kode_tahun_dipilih,
        Peminatan.id != id
    ).first()
    if cek:
        flash(f'Peminatan {nama} sudah digunakan di periode ini!', 'warning')
        return redirect(url_for('data_peminatan.halaman', tahun=kode_tahun_dipilih))

    peminatan.nama = nama
    peminatan.pembina_id = pembina_id

    tp_aktif = TahunPelajaran.query.filter_by(kode=kode_tahun_dipilih).first()
    if tp_aktif:
        if peminatan.tgl_mulai:
            if peminatan.tgl_mulai < tp_aktif.tanggal_mulai or peminatan.tgl_mulai > tp_aktif.tanggal_selesai:
                flash(f'Tanggal mulai harus antara {tp_aktif.tanggal_mulai.strftime("%d/%m/%Y")} - {tp_aktif.tanggal_selesai.strftime("%d/%m/%Y")}', 'danger')
                return redirect(url_for('data_peminatan.halaman', tahun=kode_tahun_dipilih))
        if peminatan.tgl_selesai:
            if peminatan.tgl_selesai < tp_aktif.tanggal_mulai or peminatan.tgl_selesai > tp_aktif.tanggal_selesai:
                flash(f'Tanggal selesai harus antara {tp_aktif.tanggal_mulai.strftime("%d/%m/%Y")} - {tp_aktif.tanggal_selesai.strftime("%d/%m/%Y")}', 'danger')
                return redirect(url_for('data_peminatan.halaman', tahun=kode_tahun_dipilih))
        if peminatan.tgl_mulai and peminatan.tgl_selesai and peminatan.tgl_selesai < peminatan.tgl_mulai:
            flash('Tanggal selesai tidak boleh lebih awal dari tanggal mulai!', 'danger')
            return redirect(url_for('data_peminatan.halaman', tahun=kode_tahun_dipilih))

    db.session.commit()
    flash('Data berhasil diperbarui!', 'success')
    return redirect(url_for('data_peminatan.halaman', tahun=kode_tahun_dipilih))

# ==============================================
# AMBIL DATA ANGGOTA
# ==============================================
@data_peminatan_bp.route('/data-peminatan/<int:id>/anggota')
@bisa_kelola_peminatan
def ambil_anggota(id):
    peminatan = Peminatan.query.get_or_404(id)
    daftar = []
    for siswa in peminatan.anggota:
        daftar.append({
            "id": siswa.id,
            "nisn": siswa.nisn or '-',
            "nama": siswa.nama,
            "kelas": getattr(siswa, 'kelas', '-'),
            "rombel": getattr(siswa, 'rombel', '-')
        })
    return jsonify({"anggota": daftar})

# --------------------------
# Simpan Anggota
# --------------------------
@data_peminatan_bp.route('/data-peminatan/anggota/<int:id>', methods=['POST'])
@bisa_kelola_peminatan
def simpan_anggota(id):
    peminatan = Peminatan.query.get_or_404(id)
    id_anggota_baru = request.form.getlist('anggota_id[]')

    peminatan.anggota.clear()
    for sid in id_anggota_baru:
        siswa = Siswa.query.get(sid)
        if siswa:
            peminatan.anggota.append(siswa)
    db.session.commit()
    flash('Anggota berhasil diperbarui!', 'success')
    return redirect(request.referrer or url_for('data_peminatan.halaman'))

# --------------------------
# Hapus Peminatan
# --------------------------
@data_peminatan_bp.route('/data-peminatan/hapus/<int:id>', methods=['POST'])
@bisa_kelola_peminatan
def hapus(id):
    peminatan = Peminatan.query.get_or_404(id)
    kode_tahun = request.args.get('tahun') or session.get('tahun_pelajaran')
    db.session.delete(peminatan)
    db.session.commit()
    flash('Data dihapus untuk periode ini saja. Arsip periode lain tidak terganggu!', 'info')
    return redirect(url_for('data_peminatan.halaman', tahun=kode_tahun))

# ==============================================
# ✅ HALAMAN JURNAL KEGIATAN
# ==============================================
@data_peminatan_bp.route('/data-peminatan/<int:peminatan_id>/jurnal')
@bisa_kelola_peminatan
def halaman_jurnal(peminatan_id):
    peminatan = Peminatan.query.get_or_404(peminatan_id)
    daftar_jurnal = JurnalPeminatan.query.filter_by(peminatan_id=peminatan_id).order_by(JurnalPeminatan.tanggal_kegiatan.desc()).all()
    user = User.query.get(session.get('user_id'))
    
    nama_bulan = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember']
    daftar_bulan_libur = BulanLiburPeminatan.query.filter_by(peminatan_id=peminatan_id).all()
    for item in daftar_bulan_libur:
        item.nama_bulan = nama_bulan[item.bulan - 1]
    
    semua_tahun = TahunPelajaran.query.order_by(TahunPelajaran.kode.desc()).all()
    kode_tahun_dipilih = request.args.get('tahun') or session.get('tahun_pelajaran')

    return render_template('ekstrakurikuler/jurnal_peminatan.html',
                            user=user,
                            peminatan=peminatan,
                            daftar_jurnal=daftar_jurnal,
                            daftar_bulan_libur=daftar_bulan_libur,
                            halaman_aktif=session.get('halaman_aktif', 'utama'),
                            active_page='data_peminatan',
                            tahun_dipilih=kode_tahun_dipilih,
                            semua_tahun=semua_tahun,
                            user_name=session.get('user_name'),
                            jabatan=session.get('jabatan'),
                            daftar_tugas=[t.strip() for t in session.get('tugas_tambahan','').split(',')])

# ==============================================
# ✅ TAMBAH JURNAL -> LANGSUNG KE ABSENSI
# ==============================================
@data_peminatan_bp.route('/data-peminatan/<int:peminatan_id>/jurnal/tambah', methods=['POST'])
@bisa_kelola_peminatan
def tambah_jurnal(peminatan_id):
    peminatan = Peminatan.query.get_or_404(peminatan_id)

    tgl_str = request.form.get('tanggal_kegiatan')
    if not tgl_str:
        flash('Tanggal kegiatan wajib diisi!', 'danger')
        return redirect(url_for('data_peminatan.halaman_jurnal', peminatan_id=peminatan_id))
    
    tanggal_kegiatan = datetime.strptime(tgl_str, '%Y-%m-%d').date()

    jurnal = JurnalPeminatan(
        peminatan_id=peminatan_id,
        tanggal_kegiatan = tanggal_kegiatan,
        waktu_mulai = request.form.get('waktu_mulai') or None,
        waktu_selesai = request.form.get('waktu_selesai') or None,
        uraian_kegiatan = request.form.get('uraian_kegiatan', '').strip(),
        hasil_kegiatan = request.form.get('hasil_kegiatan', '').strip() or None,
        kendala = request.form.get('kendala', '').strip() or None,
        catatan_pembina = request.form.get('catatan_pembina', '').strip() or None,
        jumlah_hadir = 0,
        terlambat = 0,
        izin = 0,
        sakit = 0,
        alpha = 0,
        dibuat_oleh = session['user_id']
    )

    db.session.add(jurnal)
    db.session.commit()
    flash('✅ Jurnal berhasil dicatat! Silakan isi kehadiran siswa.', 'success')
    
    return redirect(url_for('data_peminatan.halaman_absensi', jurnal_id=jurnal.id))

# ==============================================
# ✅ FITUR ATUR BULAN LIBUR
# ==============================================
@data_peminatan_bp.route('/data-peminatan/libur/daftar', methods=['GET'])
@bisa_kelola_peminatan
def daftar_bulan_libur():
    peminatan_id = request.args.get('peminatan_id', type=int)
    if not peminatan_id:
        return jsonify([])
    data = BulanLiburPeminatan.query.filter_by(peminatan_id=peminatan_id).all()
    return jsonify([{'bulan': d.bulan, 'tahun': d.tahun, 'keterangan': d.keterangan} for d in data])

@data_peminatan_bp.route('/data-peminatan/libur/simpan', methods=['POST'])
@bisa_kelola_peminatan
def simpan_bulan_libur():
    data = request.get_json()
    peminatan_id = data.get('peminatan_id')
    daftar = data.get('daftar', [])

    for item in daftar:
        thn, bln = item['bulan_tahun'].split('-')
        ada = BulanLiburPeminatan.query.filter_by(
            peminatan_id=peminatan_id, tahun=int(thn), bulan=int(bln)
        ).first()
        if not ada:
            baru = BulanLiburPeminatan(
                peminatan_id=peminatan_id,
                bulan=int(bln),
                tahun=int(thn),
                keterangan=item.get('keterangan', '')
            )
            db.session.add(baru)

    db.session.commit()
    return jsonify({"sukses": True, "pesan": "Tersimpan"})

@data_peminatan_bp.route('/hapus-bulan-libur-peminatan/<int:id>', methods=['GET'])
@bisa_kelola_peminatan
def hapus_bulan_libur(id):
    data = BulanLiburPeminatan.query.get_or_404(id)
    peminatan_id = data.peminatan_id
    db.session.delete(data)
    db.session.commit()
    flash('✅ Dibatalkan', 'success')
    return redirect(url_for('data_peminatan.halaman_jurnal', peminatan_id=peminatan_id))

# ==============================================
# ✅ HALAMAN ISI/EDIT ABSENSI SISWA
# ==============================================
@data_peminatan_bp.route('/data-peminatan/jurnal/<int:jurnal_id>/absensi')
@bisa_kelola_peminatan
def halaman_absensi(jurnal_id):
    jurnal = JurnalPeminatan.query.get_or_404(jurnal_id)
    peminatan = jurnal.peminatan
    user = User.query.get(session.get('user_id'))
    semua_tahun = TahunPelajaran.query.order_by(TahunPelajaran.kode.desc()).all()
    kode_tahun_dipilih = request.args.get('tahun') or session.get('tahun_pelajaran')
    daftar_anggota = peminatan.anggota
    absensi_tercatat = {a.siswa_id: a.status for a in jurnal.daftar_absensi}

    data_absensi = []
    for siswa in daftar_anggota:
        nama_kelas = "-"
        if hasattr(siswa, 'kelas_sekarang') and siswa.kelas_sekarang:
            nama_kelas = siswa.kelas_sekarang.nama_kelas

        data_absensi.append({
            'id': siswa.id,
            'nisn': siswa.nisn,
            'nama_lengkap': siswa.nama,
            'kelas': nama_kelas,
            'status': absensi_tercatat.get(siswa.id, 'hadir')
        })

    return render_template('ekstrakurikuler/absensi_peminatan.html',
                            user=user,
                            jurnal=jurnal,
                            peminatan=peminatan,
                            daftar_anggota=data_absensi,
                            user_name=session.get('user_name'),
                            jabatan=session.get('jabatan'),
                            daftar_tugas=[t.strip() for t in session.get('tugas_tambahan','').split(',')],
                            halaman_aktif=session.get('halaman_aktif', 'utama'),
                            active_page='data_peminatan',
                            tahun_dipilih=kode_tahun_dipilih,
                            semua_tahun=semua_tahun)

# ==============================================
# ✅ PROSES SIMPAN ABSENSI
# ==============================================
@data_peminatan_bp.route('/data-peminatan/jurnal/<int:jurnal_id>/simpan-absensi', methods=['POST'])
@bisa_kelola_peminatan
def simpan_absensi(jurnal_id):
    jurnal = JurnalPeminatan.query.get_or_404(jurnal_id)

    AbsensiJurnalPeminatan.query.filter_by(jurnal_id=jurnal_id).delete()

    total_hadir = 0
    total_sakit = 0
    total_izin = 0
    total_alpha = 0

    for siswa in jurnal.peminatan.anggota:
        status = request.form.get(f'status_{siswa.id}', 'hadir')
        
        baru = AbsensiJurnalPeminatan(
            jurnal_id=jurnal_id,
            siswa_id=siswa.id,
            status=status
        )
        db.session.add(baru)

        if status == 'hadir': total_hadir += 1
        elif status == 'sakit': total_sakit += 1
        elif status == 'izin': total_izin += 1
        elif status == 'alpha': total_alpha += 1

    jurnal.jumlah_hadir = total_hadir
    jurnal.sakit = total_sakit
    jurnal.izin = total_izin
    jurnal.alpha = total_alpha

    db.session.commit()
    flash('✅ Kehadiran siswa berhasil disimpan!', 'success')
    return redirect(url_for('data_peminatan.halaman_jurnal', peminatan_id=jurnal.peminatan_id))