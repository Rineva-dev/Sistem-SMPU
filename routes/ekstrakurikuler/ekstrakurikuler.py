from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models import db, Ekstrakurikuler, JurnalEkskul, User, Guru, Siswa, TahunPelajaran, BulanLiburEkskul, AbsensiJurnalEkskul, RiwayatKelas
from functools import wraps
from datetime import datetime

data_ekskul_bp = Blueprint('data_ekskul', __name__)

# ==============================================
# FUNGSI BANTU: SAMA PERSIS DENGAN MODUL KELAS
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
# ✅ FUNGSI HITUNG STATUS: SAMA PERSIS DENGAN PEMINATAN
# ==============================================
def hitung_status_kegiatan(data):
    hari_ini = datetime.today().date()

    # Cek dulu Bulan Libur
    libur = BulanLiburEkskul.query.filter(
        BulanLiburEkskul.ekskul_id == data.id,
        BulanLiburEkskul.bulan == hari_ini.month,
        BulanLiburEkskul.tahun == hari_ini.year
    ).first()

    if libur:
        return "libur"

    # Hitung berdasarkan rentang tanggal
    if hari_ini < data.tgl_mulai:
        return "belum"
    elif data.tgl_mulai <= hari_ini <= data.tgl_selesai:
        return "aktif"
    else:
        return "berhenti"

# --------------------------
# Cek Hak Akses
# --------------------------
def bisa_kelola_ekskul(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login.halaman_login'))
        jabatan = session.get('jabatan', '')
        tugas = session.get('tugas_tambahan', '')
        daftar_tugas = [t.strip() for t in tugas.split(',')] if tugas else []
        if jabatan not in ["Admin", "Tata Usaha", "TU", "Waka Kesiswaan", "Pembina Ekstrakurikuler"] and "Admin Sistem" not in daftar_tugas:
            flash("Anda tidak memiliki hak akses untuk mengelola data ini", "danger")
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorator

# --------------------------
# Halaman Daftar Ekskul
# --------------------------
@data_ekskul_bp.route('/data-ekskul')
@bisa_kelola_ekskul
def halaman():
    user = User.query.get(session.get('user_id'))
    semua_tahun = TahunPelajaran.query.order_by(TahunPelajaran.kode.desc()).all()
    tahun_aktif = TahunPelajaran.query.filter_by(aktif=True).first()

    # ✅ UTAMAKAN pilihan yang sudah disimpan dari header
    kode_tahun_dipilih = session.get('tahun_pelajaran') or request.args.get('tahun')
    if not kode_tahun_dipilih and tahun_aktif:
        kode_tahun_dipilih = tahun_aktif.kode

    # ✅ AMBIL DATA TAHUN PELAJARAN YANG DIPILIH UNTUK BATAS TANGGAL
    tp_dipilih = TahunPelajaran.query.filter_by(kode=kode_tahun_dipilih).first()
    tgl_min = ""
    tgl_max = ""
    if tp_dipilih:
        tgl_min = tp_dipilih.tanggal_mulai.strftime('%Y-%m-%d')
        tgl_max = tp_dipilih.tanggal_selesai.strftime('%Y-%m-%d')

    # ✅ Tampilkan ekskul KHUSUS untuk periode yang dipilih
    daftar_ekskul = []
    if kode_tahun_dipilih:
        daftar_ekskul = Ekstrakurikuler.query.filter_by(
            tahun_pelajaran=kode_tahun_dipilih
        ).order_by(Ekstrakurikuler.nama).all()

    for ek in daftar_ekskul:
        ek.status_kegiatan = hitung_status_kegiatan(ek)

    daftar_guru = Guru.query.order_by(Guru.nama).all()
    semua_siswa = []
    if kode_tahun_dipilih:
        semua_siswa = Siswa.query.join(RiwayatKelas).filter(
            RiwayatKelas.tahun_pelajaran == kode_tahun_dipilih,
            Siswa.status == 'Aktif'
        ).order_by(Siswa.nama).all()

    return render_template('index.html',
                            user=user,
                            user_name=session.get('user_name'),
                            jabatan=session.get('jabatan'),
                            daftar_tugas=[t.strip() for t in session.get('tugas_tambahan','').split(',')],
                            halaman_aktif=session.get('halaman_aktif', 'utama'),
                            active_page='data_ekskul',
                            tahun_dipilih=kode_tahun_dipilih,
                            semua_tahun=semua_tahun,
                            daftar_ekskul=daftar_ekskul,
                            daftar_guru=daftar_guru,
                            semua_siswa=semua_siswa,
                            tgl_min=tgl_min,
                            tgl_max=tgl_max)

# --------------------------
# Tambah Ekskul
# --------------------------
@data_ekskul_bp.route('/data-ekskul/tambah', methods=['POST'])
@bisa_kelola_ekskul
def tambah():
    nama = request.form.get('nama', '').strip()
    pembina_id = request.form.get('pembina_id')
    keterangan = request.form.get('keterangan', '').strip()

    # ✅ UBAH TEKS TANGGAL JADI OBJEK TANGGAL
    tgl_mulai_str = request.form.get('tgl_mulai')
    tgl_selesai_str = request.form.get('tgl_selesai')

    tgl_mulai = datetime.strptime(tgl_mulai_str, '%Y-%m-%d').date() if tgl_mulai_str else None
    tgl_selesai = datetime.strptime(tgl_selesai_str, '%Y-%m-%d').date() if tgl_selesai_str else None

    kode_tahun_dipilih = request.form.get('tahun_pelajaran', '').strip()

    if not kode_tahun_dipilih:
        kode_tahun_dipilih = (request.args.get('tahun') or session.get('tahun_pelajaran', '')).strip()

    if not kode_tahun_dipilih:
        flash("Pilih Tahun Pelajaran terlebih dahulu!", "warning")
        return redirect(url_for('data_ekskul.halaman'))

    if not nama:
        flash('Nama ekstrakurikuler tidak boleh kosong!', 'danger')
        return redirect(url_for('data_ekskul.halaman', tahun=kode_tahun_dipilih))

    cek = Ekstrakurikuler.query.filter_by(nama=nama, tahun_pelajaran=kode_tahun_dipilih).first()
    if cek:
        flash(f'Ekstrakurikuler {nama} sudah ada di periode ini!', 'warning')
        return redirect(url_for('data_ekskul.halaman', tahun=kode_tahun_dipilih))

    ekskul_baru = Ekstrakurikuler(
        nama=nama, pembina_id=pembina_id, keterangan=keterangan,
        tgl_mulai=tgl_mulai, tgl_selesai=tgl_selesai,
        tahun_pelajaran=kode_tahun_dipilih
    )

        # ✅ CEK TANGGAL HARUS SESUAI PERIODE SEMESTER
    tp_aktif = TahunPelajaran.query.filter_by(kode=kode_tahun_dipilih).first()
    if tp_aktif:
        # Cek batas tanggal mulai
        if tgl_mulai:
            if tgl_mulai < tp_aktif.tanggal_mulai or tgl_mulai > tp_aktif.tanggal_selesai:
                flash(f'Tanggal mulai harus antara {tp_aktif.tanggal_mulai.strftime("%d/%m/%Y")} - {tp_aktif.tanggal_selesai.strftime("%d/%m/%Y")}', 'danger')
                return redirect(url_for('data_ekskul.halaman', tahun=kode_tahun_dipilih))
        
        # Cek batas tanggal selesai
        if tgl_selesai:
            if tgl_selesai < tp_aktif.tanggal_mulai or tgl_selesai > tp_aktif.tanggal_selesai:
                flash(f'Tanggal selesai harus antara {tp_aktif.tanggal_mulai.strftime("%d/%m/%Y")} - {tp_aktif.tanggal_selesai.strftime("%d/%m/%Y")}', 'danger')
                return redirect(url_for('data_ekskul.halaman', tahun=kode_tahun_dipilih))
        
        # Cek urutan tanggal
        if tgl_mulai and tgl_selesai and tgl_selesai < tgl_mulai:
            flash('Tanggal selesai tidak boleh lebih awal dari tanggal mulai!', 'danger')
            return redirect(url_for('data_ekskul.halaman', tahun=kode_tahun_dipilih))
        
    db.session.add(ekskul_baru)
    db.session.commit()
    flash('Data berhasil ditambahkan!', 'success')
    return redirect(url_for('data_ekskul.halaman', tahun=kode_tahun_dipilih))

# --------------------------
# Ubah Ekskul
# --------------------------
@data_ekskul_bp.route('/data-ekskul/ubah/<int:id>', methods=['POST'])
@bisa_kelola_ekskul
def ubah(id):
    ekskul = Ekstrakurikuler.query.get_or_404(id)
    nama = request.form.get('nama', '').strip()
    pembina_id = request.form.get('pembina_id')
    keterangan = request.form.get('keterangan', '').strip()

    # ✅ UBAH TEKS TANGGAL JADI OBJEK TANGGAL
    tgl_mulai_str = request.form.get('tgl_mulai')
    tgl_selesai_str = request.form.get('tgl_selesai')

    ekskul.tgl_mulai = datetime.strptime(tgl_mulai_str, '%Y-%m-%d').date() if tgl_mulai_str else None
    ekskul.tgl_selesai = datetime.strptime(tgl_selesai_str, '%Y-%m-%d').date() if tgl_selesai_str else None
    
    # ==================================================
    # ✅ BAGIAN INI YANG DIPERBAIKI
    # ==================================================
    kode_tahun_dipilih = request.form.get('tahun_pelajaran', '').strip()

    if not kode_tahun_dipilih:
        kode_tahun_dipilih = (request.args.get('tahun') or session.get('tahun_pelajaran', '')).strip()

    if not kode_tahun_dipilih:
        flash("Pilih Tahun Pelajaran terlebih dahulu!", "warning")
        return redirect(url_for('data_ekskul.halaman'))

    if not nama:
        flash('Nama ekstrakurikuler tidak boleh kosong!', 'danger')
        return redirect(url_for('data_ekskul.halaman', tahun=kode_tahun_dipilih))

    cek = Ekstrakurikuler.query.filter(
        Ekstrakurikuler.nama == nama,
        Ekstrakurikuler.tahun_pelajaran == kode_tahun_dipilih,
        Ekstrakurikuler.id != id
    ).first()
    if cek:
        flash(f'Ekstrakurikuler {nama} sudah digunakan di periode ini!', 'warning')
        return redirect(url_for('data_ekskul.halaman', tahun=kode_tahun_dipilih))

    ekskul.nama = nama
    ekskul.pembina_id = pembina_id

    tp_aktif = TahunPelajaran.query.filter_by(kode=kode_tahun_dipilih).first()
    if tp_aktif:
        if ekskul.tgl_mulai:
            if ekskul.tgl_mulai < tp_aktif.tanggal_mulai or ekskul.tgl_mulai > tp_aktif.tanggal_selesai:
                flash(f'Tanggal mulai harus antara {tp_aktif.tanggal_mulai.strftime("%d/%m/%Y")} - {tp_aktif.tanggal_selesai.strftime("%d/%m/%Y")}', 'danger')
                return redirect(url_for('data_ekskul.halaman', tahun=kode_tahun_dipilih))

        if ekskul.tgl_selesai:
            if ekskul.tgl_selesai < tp_aktif.tanggal_mulai or ekskul.tgl_selesai > tp_aktif.tanggal_selesai:
                flash(f'Tanggal selesai harus antara {tp_aktif.tanggal_mulai.strftime("%d/%m/%Y")} - {tp_aktif.tanggal_selesai.strftime("%d/%m/%Y")}', 'danger')
                return redirect(url_for('data_ekskul.halaman', tahun=kode_tahun_dipilih))

        if ekskul.tgl_mulai and ekskul.tgl_selesai and ekskul.tgl_selesai < ekskul.tgl_mulai:
            flash('Tanggal selesai tidak boleh lebih awal dari tanggal mulai!', 'danger')
            return redirect(url_for('data_ekskul.halaman', tahun=kode_tahun_dipilih))
        
    db.session.commit()
    flash('Data berhasil diperbarui!', 'success')
    return redirect(url_for('data_ekskul.halaman', tahun=kode_tahun_dipilih))


# ==============================================
# ✅ FITUR SALIN EKSKUL KE PERIODE BERIKUTNYA
# ==============================================
@data_ekskul_bp.route('/data-ekskul/salin', methods=['POST'])
@bisa_kelola_ekskul
def salin_ekskul():
    dari_periode = request.form.get('dari_periode')
    ke_periode = request.form.get('ke_periode')

    if not dari_periode or not ke_periode:
        flash("Pilih periode asal dan tujuan terlebih dahulu!", "warning")
        return redirect(url_for('data_ekskul.halaman'))

    if dari_periode == ke_periode:
        flash("Periode asal dan tujuan tidak boleh sama!", "danger")
        return redirect(url_for('data_ekskul.halaman', tahun=ke_periode))

    daftar_sumber = Ekstrakurikuler.query.filter_by(tahun_pelajaran=dari_periode).all()
    berhasil = 0

    for ekskul in daftar_sumber:
        # Cek apakah sudah ada di periode tujuan
        cek_ada = Ekstrakurikuler.query.filter_by(
            nama=ekskul.nama, tahun_pelajaran=ke_periode
        ).first()
        if not cek_ada:
            baru = Ekstrakurikuler(
                nama=ekskul.nama,
                pembina_id=ekskul.pembina_id,
                
                keterangan=ekskul.keterangan,
                tahun_pelajaran=ke_periode
            )
            db.session.add(baru)
            berhasil += 1

    db.session.commit()
    flash(f"Berhasil menyalin {berhasil} jenis ekstrakurikuler ke periode {ke_periode}. Data periode asal tetap aman sebagai arsip!", "success")
    return redirect(url_for('data_ekskul.halaman', tahun=ke_periode))

@data_ekskul_bp.route('/data-ekskul/<int:id>/anggota')
@bisa_kelola_ekskul
def ambil_anggota(id):
    ekskul = Ekstrakurikuler.query.get_or_404(id)
    daftar = []
    for siswa in ekskul.anggota:
        riwayat = RiwayatKelas.query.filter_by(
            siswa_id=siswa.id,
            tahun_pelajaran=ekskul.tahun_pelajaran
        ).first()

        if riwayat and riwayat.kelas:
            nama_kelas = riwayat.kelas.nama_kelas
            nama_rombel = getattr(riwayat.kelas, 'rombel', '-')
        else:
            nama_kelas = '-'
            nama_rombel = '-'

        daftar.append({
            "id": siswa.id,
            "nisn": siswa.nisn or '-',
            "nama": siswa.nama,
            "kelas": nama_kelas,
            "rombel": nama_rombel
        })
    return jsonify(daftar)

# --------------------------
# Simpan Anggota
# --------------------------
@data_ekskul_bp.route('/data-ekskul/anggota/<int:id>', methods=['POST'])
@bisa_kelola_ekskul
def simpan_anggota(id):
    ekskul = Ekstrakurikuler.query.get_or_404(id)
    id_anggota_baru = request.form.getlist('anggota_id[]')

    ekskul.anggota.clear()
    for sid in id_anggota_baru:
        siswa = Siswa.query.get(sid)
        if siswa:
            ekskul.anggota.append(siswa)
    db.session.commit()
    flash('Anggota berhasil diperbarui!', 'success')
    
    return redirect(url_for('data_ekskul.halaman', tahun=ekskul.tahun_pelajaran))

# --------------------------
# Hapus Ekskul
# --------------------------
@data_ekskul_bp.route('/data-ekskul/hapus/<int:id>', methods=['POST'])
@bisa_kelola_ekskul
def hapus(id):
    ekskul = Ekstrakurikuler.query.get_or_404(id)
    kode_tahun = request.args.get('tahun') or session.get('tahun_pelajaran')
    db.session.delete(ekskul)
    db.session.commit()
    flash('Data dihapus untuk periode ini saja. Arsip periode lain tidak terganggu!', 'info')
    return redirect(url_for('data_ekskul.halaman', tahun=kode_tahun))

# ==============================================
# ✅ HALAMAN JURNAL KEGIATAN
# ==============================================
@data_ekskul_bp.route('/data-ekskul/<int:ekskul_id>/jurnal')
@bisa_kelola_ekskul
def halaman_jurnal(ekskul_id):
    ekskul = Ekstrakurikuler.query.get_or_404(ekskul_id)
    daftar_jurnal = JurnalEkskul.query.filter_by(ekskul_id=ekskul_id).order_by(JurnalEkskul.tanggal_kegiatan.desc()).all()
    user = User.query.get(session.get('user_id'))
    
    # ✅ AMBIL DAFTAR BULAN LIBUR
    nama_bulan = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember']
    daftar_bulan_libur = BulanLiburEkskul.query.filter_by(ekskul_id=ekskul_id).all()
    for item in daftar_bulan_libur:
        item.nama_bulan = nama_bulan[item.bulan - 1]
    
    # ✅ Sertakan variabel agar filter TP & menu aktif tetap berjalan
    semua_tahun = TahunPelajaran.query.order_by(TahunPelajaran.kode.desc()).all()
    kode_tahun_dipilih = request.args.get('tahun') or session.get('tahun_pelajaran')

    return render_template('ekstrakurikuler/jurnal_ekskul.html',
                            user=user,
                            ekskul=ekskul,
                            daftar_jurnal=daftar_jurnal,
                            daftar_bulan_libur=daftar_bulan_libur,
                            halaman_aktif=session.get('halaman_aktif', 'utama'),
                            active_page='data_ekskul',
                            tahun_dipilih=kode_tahun_dipilih,
                            semua_tahun=semua_tahun,
                            user_name=session.get('user_name'),
                            jabatan=session.get('jabatan'),
                            daftar_tugas=[t.strip() for t in session.get('tugas_tambahan','').split(',')])

# ==============================================
# ✅ TAMBAH JURNAL
# ==============================================
# ==============================================
# ✅ TAMBAH JURNAL -> LANGSUNG KE ABSENSI
# ==============================================
@data_ekskul_bp.route('/data-ekskul/<int:ekskul_id>/jurnal/tambah', methods=['POST'])
@bisa_kelola_ekskul
def tambah_jurnal(ekskul_id):
    ekskul = Ekstrakurikuler.query.get_or_404(ekskul_id)

    tgl_str = request.form.get('tanggal_kegiatan')
    if not tgl_str:
        flash('Tanggal kegiatan wajib diisi!', 'danger')
        return redirect(url_for('data_ekskul.halaman_jurnal', ekskul_id=ekskul_id))
    
    tanggal_kegiatan = datetime.strptime(tgl_str, '%Y-%m-%d').date()

    jurnal = JurnalEkskul(
        ekskul_id=ekskul_id,
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
    
    # ✅ SETELAH SIMPAN -> LANGSUNG KE HALAMAN ABSENSI
    return redirect(url_for('data_ekskul.halaman_absensi', jurnal_id=jurnal.id))

# ==============================================
# ✅ FITUR ATUR BULAN LIBUR
# ==============================================
@data_ekskul_bp.route('/data-ekskul/libur/daftar', methods=['GET'])
@bisa_kelola_ekskul
def daftar_bulan_libur():
    ekskul_id = request.args.get('ekskul_id', type=int)
    if not ekskul_id:
        return jsonify([])
    data = BulanLiburEkskul.query.filter_by(ekskul_id=ekskul_id).all()
    return jsonify([{'bulan': d.bulan, 'tahun': d.tahun, 'keterangan': d.keterangan} for d in data])

@data_ekskul_bp.route('/data-ekskul/libur/simpan', methods=['POST'])
@bisa_kelola_ekskul
def simpan_bulan_libur():
    data = request.get_json()
    ekskul_id = data.get('ekskul_id')
    daftar = data.get('daftar', [])

    for item in daftar:
        thn, bln = item['bulan_tahun'].split('-')
        # Cek dulu agar tidak error jika ada celah
        ada = BulanLiburEkskul.query.filter_by(
            ekskul_id=ekskul_id, tahun=int(thn), bulan=int(bln)
        ).first()
        if not ada:
            baru = BulanLiburEkskul(
                ekskul_id=ekskul_id,
                bulan=int(bln),
                tahun=int(thn),
                keterangan=item.get('keterangan', '')
            )
            db.session.add(baru)

    db.session.commit()
    return jsonify({"sukses": True, "pesan": "Tersimpan"})

@data_ekskul_bp.route('/hapus-bulan-libur/<int:id>', methods=['GET'])
@bisa_kelola_ekskul
def hapus_bulan_libur(id):
    data = BulanLiburEkskul.query.get_or_404(id)
    ekskul_id = data.ekskul_id
    db.session.delete(data)
    db.session.commit()
    flash('✅ Dibatalkan', 'success')
    return redirect(url_for('data_ekskul.halaman_jurnal', ekskul_id=ekskul_id))

# ==============================================
# ✅ HALAMAN ISI/EDIT ABSENSI SISWA
# ==============================================
@data_ekskul_bp.route('/data-ekskul/jurnal/<int:jurnal_id>/absensi')
@bisa_kelola_ekskul
def halaman_absensi(jurnal_id):
    jurnal = JurnalEkskul.query.get_or_404(jurnal_id)
    ekskul = jurnal.ekskul
    user = User.query.get(session.get('user_id'))
    semua_tahun = TahunPelajaran.query.order_by(TahunPelajaran.kode.desc()).all()
    kode_tahun_dipilih = request.args.get('tahun') or session.get('tahun_pelajaran')
    daftar_anggota = ekskul.anggota
    absensi_tercatat = {a.siswa_id: a.status for a in jurnal.daftar_absensi}

    data_absensi = []
    for siswa in daftar_anggota:
        nama_kelas = "-"
        if siswa.kelas_sekarang:
            nama_kelas = siswa.kelas_sekarang.nama_kelas

        data_absensi.append({
            'id': siswa.id,
            'nisn': siswa.nisn,
            'nama_lengkap': siswa.nama,
            'kelas': nama_kelas,
            'status': absensi_tercatat.get(siswa.id, 'hadir')
        })

    return render_template('ekstrakurikuler/absensi_ekskul.html',
                            user=user,
                            jurnal=jurnal,
                            ekskul=ekskul,
                            daftar_anggota=data_absensi,
                            user_name=session.get('user_name'),
                            jabatan=session.get('jabatan'),
                            daftar_tugas=[t.strip() for t in session.get('tugas_tambahan','').split(',')],
                            halaman_aktif=session.get('halaman_aktif', 'utama'),
                            active_page='data_ekskul',
                            tahun_dipilih=kode_tahun_dipilih,
                            semua_tahun=semua_tahun)

# ==============================================
# ✅ PROSES SIMPAN ABSENSI
# ==============================================
@data_ekskul_bp.route('/data-ekskul/jurnal/<int:jurnal_id>/simpan-absensi', methods=['POST'])
@bisa_kelola_ekskul
def simpan_absensi(jurnal_id):
    jurnal = JurnalEkskul.query.get_or_404(jurnal_id)

    AbsensiJurnalEkskul.query.filter_by(jurnal_id=jurnal_id).delete()

    total_hadir = 0
    total_sakit = 0
    total_izin = 0
    total_alpha = 0

    for siswa in jurnal.ekskul.anggota:
        status = request.form.get(f'status_{siswa.id}', 'hadir')
        
        baru = AbsensiJurnalEkskul(
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
    return redirect(url_for('data_ekskul.halaman_jurnal', ekskul_id=jurnal.ekskul_id))