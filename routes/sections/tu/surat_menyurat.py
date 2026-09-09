from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from models import db, Guru, User, SuratKeluar, PenandatanganSurat, PenerimaSuratDiajukan

surat_bp = Blueprint('surat_menyurat', __name__, url_prefix='/surat-menyurat')

# --------------------------
# ✅ PENGATURAN UNGGAH FILE
# --------------------------
UPLOAD_FOLDER_MASUK = 'static/uploads/surat_masuk'
UPLOAD_FOLDER_KELUAR = 'static/uploads/surat_keluar'
QR_FOLDER = 'static/assets/qr_surat'

os.makedirs(UPLOAD_FOLDER_MASUK, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_KELUAR, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --------------------------
# ✅ FUNGSI BANTU: AMBIL DAFTAR JABATAN & TUGAS
# --------------------------
def dapatkan_daftar_penandatangan():
    """Ambil semua jabatan dan tugas tambahan dari data Guru"""
    semua_guru = Guru.query.filter_by(status='Aktif').all()
    daftar = {}

    # Kelompokkan berdasarkan jabatan utama
    for g in semua_guru:
        jabatan = g.jabatan.strip()
        if jabatan not in daftar:
            daftar[jabatan] = []
        daftar[jabatan].append({
            'id': g.id,
            'nama': g.nama,
            'jabatan': jabatan
        })

        # Kelompokkan juga berdasarkan tugas tambahan
        if g.tugas_tambahan:
            for tugas in [t.strip() for t in g.tugas_tambahan.split(',')]:
                if tugas not in daftar:
                    daftar[tugas] = []
                daftar[tugas].append({
                    'id': g.id,
                    'nama': g.nama,
                    'jabatan': tugas
                })

    return daftar

def dapatkan_daftar_jabatan():
    return dapatkan_daftar_penandatangan()

# --------------------------
# ✅ FUNGSI BANTU: BUAT NILAI JENIS SESUAI FORMAT DROPDOWN
# --------------------------
def buat_nilai_jenis(id_guru_int, jabatan_bersih, jenis_dari_form=None):
    """
    Hasilkan nilai 'jenis' yang persis sama dengan opsi di HTML
    Jika dikirim 'jenis_dari_form', gunakan itu terlebih dahulu
    """
    # Jika ada nilai langsung dari dropdown, gunakan itu
    if jenis_dari_form:
        return jenis_dari_form.strip()

    # Jika tidak ada, baru gunakan logika lama
    if id_guru_int:
        guru = Guru.query.get(id_guru_int)
        if guru:
            jabatan = guru.jabatan.strip()
            return jabatan.replace(' ', '_')
        return ""

    jabatan_bersih = jabatan_bersih.strip()
    peta = {
        "Ketua Panitia": "khusus-ketua",
        "Sekretaris Panitia": "khusus-sekretaris",
        "Bendahara Panitia": "khusus-bendahara",
        "Supervisor": "khusus-supervisor"
    }
    if jabatan_bersih in peta:
        return peta[jabatan_bersih]
    else:
        return jabatan_bersih.replace(' ', '_')

# --------------------------
# RUTE UTAMA
# --------------------------
@surat_bp.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    # ✅ AMBIL DATA USER ASLI DARI DATABASE
    user = User.query.get(session.get('user_id'))

    halaman_aktif = session.get('halaman_aktif', 'utama')
    role = session.get('role', session.get('jabatan', ''))
    user_id = session.get('user_id')

    surat_masuk = SuratKeluar.query.join(
        PenandatanganSurat
    ).filter(
        PenandatanganSurat.id_guru == user_id,
        SuratKeluar.status.in_(['Diajukan', 'Disetujui', 'Perlu Perbaikan', 'Ditolak'])
    ).order_by(SuratKeluar.tanggal_surat.desc()).all()

    surat_keluar = SuratKeluar.query.filter_by(dibuat_oleh=user_id).order_by(SuratKeluar.tanggal_surat.desc()).all()

    for surat in surat_keluar + surat_masuk:
        qr_surat = surat.qr_code_path or None
        surat.daftar_ttd = [
            {
                "nama": t.nama,
                "jabatan": t.jabatan,
                "nip": t.guru.nip if (t.guru and t.guru.nip) else "-",
                "ttd_selesai": t.ttd_selesai,
                "tanggal_ttd": t.tanggal_ttd.strftime('%d %b %Y %H:%M') if t.tanggal_ttd else None,
                "qr_code": t.qr_code
            }
            for t in surat.daftar_penandatangan
        ]

    jumlah_masuk = len(surat_masuk)
    jumlah_keluar = len(surat_keluar)
    jumlah_belum_proses = SuratKeluar.query.filter_by(dibuat_oleh=user_id, status='Diajukan').count()

    context = {
        'active_page': 'surat_menyurat',
        'sub_page': 'daftar',
        'halaman_aktif': halaman_aktif,
        'role': role,
        'user': user,
        'jumlah_masuk': jumlah_masuk,
        'jumlah_keluar': jumlah_keluar,
        'jumlah_belum_proses': jumlah_belum_proses,
        'surat_masuk': surat_masuk,
        'surat_keluar': surat_keluar
    }

    return render_template('index.html', **context) 

# ------------------------------
# ✅ RUTE TAMBAH SURAT KELUAR (DIPERBAIKI)
# ------------------------------
@surat_bp.route('/tambah-keluar', methods=['GET', 'POST'])
def tambah_keluar():
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    # ✅ AMBIL DATA USER
    user = User.query.get(session.get('user_id'))

    if request.method == 'POST':
        # Ambil data utama surat
        nomor_surat = request.form.get('nomor_surat', '').strip()
        tanggal_surat_str = request.form.get('tanggal_surat', '').strip()
        lampiran = request.form.get('lampiran', '').strip() or '-'
        perihal = request.form.get('perihal', '').strip()
        tujuan = request.form.get('tujuan', '').strip()
        isi_surat = request.form.get('isi_surat', '').strip() or None
        status = request.form.get('status', 'Tersimpan')

        # Validasi dasar
        if not all([nomor_surat, tanggal_surat_str, perihal, tujuan]):
            flash('Nomor, tanggal, perihal, dan tujuan wajib diisi!', 'danger')
            return redirect(request.url)

        try:
            tanggal_surat = datetime.strptime(tanggal_surat_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Format tanggal tidak valid! Gunakan format YYYY-MM-DD.', 'danger')
            return redirect(request.url)

        status_valid = ['Tersimpan', 'Diajukan', 'Disetujui', 'Perlu Perbaikan', 'Ditolak']
        if status not in status_valid:
            flash('Status surat tidak valid!', 'danger')
            return redirect(request.url)

        # Proses upload file
        nama_file_simpan = None
        if 'file_surat' in request.files:
            file = request.files['file_surat']
            if file and file.filename != '':
                if not allowed_file(file.filename):
                    flash('Jenis file tidak diperbolehkan! Hanya PDF, JPG, PNG.', 'danger')
                    return redirect(request.url)
                file.seek(0, os.SEEK_END)
                ukuran = file.tell()
                file.seek(0)
                if ukuran > MAX_FILE_SIZE:
                    flash('Ukuran file terlalu besar! Maksimal 2MB.', 'danger')
                    return redirect(request.url)

                ekstensi = file.filename.rsplit('.', 1)[1].lower()
                nama_aman = secure_filename(f"{nomor_surat.replace('/', '-')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ekstensi}")
                path_simpan = os.path.join(UPLOAD_FOLDER_KELUAR, nama_aman)
                file.save(path_simpan)
                nama_file_simpan = f"uploads/surat_keluar/{nama_aman}"

        tujuan_mentah = request.form.get('tujuan_isi', '').strip()
        tujuan_lokasi = request.form.get('tujuan_lokasi', 'Tempat').strip()

        try:
            surat_baru = SuratKeluar(
                nomor_surat=nomor_surat,
                tanggal_surat=tanggal_surat,
                lampiran=lampiran,
                perihal=perihal,
                tujuan=tujuan,
                tujuan_mentah=tujuan_mentah,
                tujuan_lokasi=tujuan_lokasi,    
                isi_surat=isi_surat,
                status=status,
                file_path=nama_file_simpan,
                dibuat_oleh=session.get('user_id')
            )
            db.session.add(surat_baru)
            db.session.flush()

            jenis_ttd = request.form.getlist('jenis_ttd[]')
            id_guru_ttd = request.form.getlist('id_guru_ttd[]')
            nama_ttd = request.form.getlist('nama_ttd[]')
            jabatan_ttd = request.form.getlist('jabatan_ttd[]')

            jumlah_diajukan = 0
            jumlah_berhasil = 0

            for j, id_g, n, jb in zip(jenis_ttd, id_guru_ttd, nama_ttd, jabatan_ttd):
                nama_bersih = n.strip()
                jabatan_bersih = jb.strip()

                if not nama_bersih or not jabatan_bersih:
                    continue

                id_guru_int = None
                if id_g:
                    id_g = str(id_g).strip()
                    if id_g.isdigit() and int(id_g) > 0:
                        id_guru_int = int(id_g)

                # ✅ Gunakan fungsi buat nilai jenis yang benar
                nilai_jenis = buat_nilai_jenis(id_guru_int, jabatan_bersih, jenis_dari_form=j)

                ttd = PenandatanganSurat(
                    surat_id=surat_baru.id,
                    jenis=nilai_jenis,
                    id_guru=id_guru_int,
                    nama=nama_bersih,
                    jabatan=jabatan_bersih
                )
                db.session.add(ttd)

                if status == 'Diajukan':
                    jumlah_diajukan += 1
                    if id_guru_int:
                        guru = Guru.query.get(id_guru_int)
                        if not guru:
                            flash(f"❌ ID {id_guru_int} tidak terdaftar sebagai guru", "danger")
                            continue
                        akun_penerima = User.query.filter_by(guru_id=id_guru_int, aktif=True).first()
                        if akun_penerima:
                            penerima = PenerimaSuratDiajukan(
                                surat_id=surat_baru.id,
                                user_id=akun_penerima.id,
                                nama=nama_bersih,
                                jabatan=jabatan_bersih,
                                status_tinjau='Menunggu'
                            )
                            db.session.add(penerima)
                            jumlah_berhasil += 1
                            flash(f"✅ Berhasil diajukan ke: {nama_bersih}", "success")
                        else:
                            flash(f"⚠️ {nama_bersih} terdaftar tapi belum punya akun aktif", "warning")
                    else:
                        flash(f"ℹ️ {nama_bersih} diisi manual / tidak terdaftar", "info")

            db.session.commit()

            if status == 'Diajukan':
                if jumlah_diajukan == 0:
                    flash('Tidak ada penandatangan yang dipilih!', 'warning')
                elif jumlah_berhasil == 0:
                    flash('Surat disimpan, tetapi tidak ada penandatangan yang memiliki akun sistem untuk menerima.', 'warning')
                else:
                    flash(f'Surat berhasil diajukan ke {jumlah_berhasil} penandatangan!', 'success')
            else:
                flash('Surat berhasil disimpan ke arsip!', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Gagal menyimpan surat: {str(e)}', 'danger')
            return redirect(request.url)

        return redirect(url_for('surat_menyurat.index'))

    daftar_jabatan_tugas = dapatkan_daftar_penandatangan()
    context = {
        'active_page': 'surat_menyurat',
        'sub_page': 'tambah_keluar',
        'halaman_aktif': session.get('halaman_aktif', 'utama'),
        'role': session.get('role', session.get('jabatan', '')),
        'user': user,
        'daftar_jabatan_tugas': daftar_jabatan_tugas
    }
    return render_template('index.html', **context)

# ------------------------------
# RUTE LAINNYA TETAP SAMA
# ------------------------------
@surat_bp.route('/tambah-masuk', methods=['GET', 'POST'])
def tambah_masuk():
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    # ✅ AMBIL DATA USER
    user = User.query.get(session.get('user_id'))

    if request.method == 'POST':
        nomor_surat = request.form.get('nomor_surat', '').strip()
        tanggal_surat = request.form.get('tanggal_surat', '').strip()
        tanggal_terima = request.form.get('tanggal_terima', '').strip()
        pengirim = request.form.get('pengirim', '').strip()
        perihal = request.form.get('perihal', '').strip()
        status = request.form.get('status', 'Diproses')

        nama_file_simpan = None
        if 'file_surat' in request.files:
            file = request.files['file_surat']
            if file and file.filename != '':
                if not allowed_file(file.filename):
                    flash('Jenis file tidak diperbolehkan!', 'danger')
                    return redirect(request.url)
                file.seek(0, os.SEEK_END)
                ukuran = file.tell()
                file.seek(0)
                if ukuran > MAX_FILE_SIZE:
                    flash('Ukuran file terlalu besar! Maksimal 2MB.', 'danger')
                    return redirect(request.url)

                ekstensi = file.filename.rsplit('.', 1)[1].lower()
                nama_aman = secure_filename(f"{nomor_surat.replace('/', '-')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ekstensi}")
                path_simpan = os.path.join(UPLOAD_FOLDER_MASUK, nama_aman)
                file.save(path_simpan)
                nama_file_simpan = f"uploads/surat_masuk/{nama_aman}"

        flash('Surat masuk berhasil disimpan!', 'success')
        return redirect(url_for('surat_menyurat.index'))

    context = {
        'active_page': 'surat_menyurat',
        'sub_page': 'tambah_masuk',
        'halaman_aktif': session.get('halaman_aktif', 'utama'),
        'role': session.get('role', session.get('jabatan', '')),
        'user': user
    }
    return render_template('index.html', **context)


@surat_bp.route('/ubah/<jenis>/<int:id>', methods=['GET', 'POST'])
def ubah(jenis, id):
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    # ✅ AMBIL DATA USER
    user = User.query.get(session.get('user_id'))

    if jenis not in ['masuk', 'keluar']:
        flash('Jenis surat tidak valid', 'danger')
        return redirect(url_for('surat_menyurat.index'))

    if request.method == 'POST':
        flash(f'Surat {jenis} berhasil diperbarui', 'success')
        return redirect(url_for('surat_menyurat.index'))

    context = {
        'active_page': 'surat_menyurat',
        'sub_page': f'ubah_{jenis}',
        'id': id,
        'halaman_aktif': session.get('halaman_aktif', 'utama'),
        'role': session.get('role', session.get('jabatan', '')),
        'user': user
    }
    return render_template('index.html', **context)


@surat_bp.route('/detail/<jenis>/<int:id>')
def detail(jenis, id):
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    # ✅ AMBIL DATA USER
    user = User.query.get(session.get('user_id'))

    if jenis not in ['masuk', 'keluar']:
        flash('Jenis surat tidak valid', 'danger')
        return redirect(url_for('surat_menyurat.index'))

    context = {
        'active_page': 'surat_menyurat',
        'sub_page': f'detail_{jenis}',
        'id': id,
        'halaman_aktif': session.get('halaman_aktif', 'utama'),
        'role': session.get('role', session.get('jabatan', '')),
        'user': user
    }
    return render_template('index.html', **context)


@surat_bp.route('/cetak/<jenis>/<int:id>')
def cetak(jenis, id):
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    # ✅ AMBIL DATA USER
    user = User.query.get(session.get('user_id'))

    if jenis not in ['masuk', 'keluar']:
        flash('Jenis surat tidak valid', 'danger')
        return redirect(url_for('surat_menyurat.index'))

    context = {
        'active_page': 'surat_menyurat',
        'sub_page': f'cetak_{jenis}',
        'id': id,
        'halaman_aktif': session.get('halaman_aktif', 'utama'),
        'role': session.get('role', session.get('jabatan', '')),
        'user': user
    }
    return render_template('index.html', **context)

# ------------------------------
# ✅ RUTE UBAH SURAT KELUAR (DIPERBAIKI)
# ------------------------------
@surat_bp.route('/ubah-surat-keluar/<int:id>', methods=['GET', 'POST'])
def ubah_surat_keluar(id):
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    # ✅ AMBIL DATA USER
    user = User.query.get(session.get('user_id'))

    surat = SuratKeluar.query.get_or_404(id)

    if surat.dibuat_oleh != session.get('user_id'):
        flash('Anda tidak berhak mengubah surat ini!', 'danger')
        return redirect(url_for('surat_menyurat.index'))

    if not surat.tujuan_mentah and surat.tujuan:
        baris = [b.rstrip() for b in surat.tujuan.split('\n')]
        baris_bersih = []
        for b in baris:
            if b.strip():
                baris_bersih.append(b)

        if len(baris_bersih) >= 2:
            if baris_bersih[1].startswith('Yth. '):
                isi = []
                idx = 1
                while idx < len(baris_bersih) and not baris_bersih[idx].strip().startswith('di '):
                    teks = baris_bersih[idx].replace('Yth. ', '', 1).lstrip()
                    isi.append(teks)
                    idx += 1
                surat.tujuan_mentah = '\n'.join(isi).strip()

            for b in baris_bersih:
                if b.strip().startswith('di '):
                    lokasi = b.strip().replace('di ', '').replace('_', '').strip()
                    surat.tujuan_lokasi = lokasi if lokasi else 'Tempat'
                    break
            else:
                surat.tujuan_lokasi = 'Tempat'

    daftar_jabatan_tugas = dapatkan_daftar_penandatangan()

    daftar_ttd = []
    for ttd in surat.daftar_penandatangan:
        daftar_ttd.append({
            'jenis': ttd.jenis,
            'id_guru': ttd.id_guru,
            'nama': ttd.nama,
            'jabatan': ttd.jabatan,
            'nip': ttd.guru.nip if ttd.guru and ttd.guru.nip else "-",
            'ttd_selesai': ttd.ttd_selesai,
            'tanggal_ttd': ttd.tanggal_ttd,
            'qr_code': ttd.qr_code
        })

    if request.method == 'POST':
        try:
            nomor_surat = request.form['nomor_surat'].strip()
            tanggal_surat_str = request.form['tanggal_surat'].strip()
            lampiran = request.form.get('lampiran', '').strip() or '-'
            perihal = request.form['perihal'].strip()
            tujuan = request.form['tujuan'].strip()
            tujuan_mentah = request.form.get('tujuan_isi', '').strip()
            tujuan_lokasi = request.form.get('tujuan_lokasi', 'Tempat').strip()
            isi_surat = request.form['isi_surat'].strip()
            status_baru = request.form.get('status', 'Tersimpan')

            try:
                tanggal_surat = datetime.strptime(tanggal_surat_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Format tanggal tidak valid!', 'danger')
                return redirect(request.url)

            status_valid = ['Tersimpan', 'Diajukan', 'Disetujui', 'Perlu Perbaikan', 'Ditolak']
            if status_baru not in status_valid:
                flash('Status surat tidak valid!', 'danger')
                return redirect(request.url)

            surat.nomor_surat = nomor_surat
            surat.tanggal_surat = tanggal_surat
            surat.lampiran = lampiran
            surat.perihal = perihal
            surat.tujuan = tujuan
            surat.tujuan_mentah = tujuan_mentah
            surat.tujuan_lokasi = tujuan_lokasi
            surat.isi_surat = isi_surat
            surat.status = status_baru

            if 'file_surat' in request.files:
                file = request.files['file_surat']
                if file and file.filename != '':
                    if not allowed_file(file.filename):
                        flash('Jenis file tidak diperbolehkan!', 'danger')
                        return redirect(request.url)
                    file.seek(0, os.SEEK_END)
                    ukuran = file.tell()
                    file.seek(0)
                    if ukuran > MAX_FILE_SIZE:
                        flash('Ukuran file maksimal 2MB!', 'danger')
                        return redirect(request.url)

                    ekstensi = file.filename.rsplit('.', 1)[1].lower()
                    nama_aman = secure_filename(f"{surat.nomor_surat.replace('/', '-')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ekstensi}")
                    path_simpan = os.path.join(UPLOAD_FOLDER_KELUAR, nama_aman)
                    file.save(path_simpan)
                    surat.file_path = f"uploads/surat_keluar/{nama_aman}"

            # Hapus data lama
            PenandatanganSurat.query.filter_by(surat_id=surat.id).delete()
            PenerimaSuratDiajukan.query.filter_by(surat_id=surat.id).delete()

            jenis_ttd = request.form.getlist('jenis_ttd[]')
            id_guru_ttd = request.form.getlist('id_guru_ttd[]')
            nama_ttd = request.form.getlist('nama_ttd[]')
            jabatan_ttd = request.form.getlist('jabatan_ttd[]')

            jumlah_diajukan = 0
            jumlah_berhasil = 0

            for j, id_g, n, jb in zip(jenis_ttd, id_guru_ttd, nama_ttd, jabatan_ttd):
                nama_bersih = n.strip()
                jabatan_bersih = jb.strip()

                if not nama_bersih or not jabatan_bersih:
                    continue

                # ✅ Ini yang diperbaiki: cek jika id_g tidak kosong
                id_guru_int = None
                if id_g and id_g.strip() != "":  # Tambah pengecekan "tidak kosong"
                    if id_g.isdigit() and int(id_g) > 0:
                        id_guru_int = int(id_g)

                # ✅ Gunakan parameter tambahan jenis_dari_form=j
                nilai_jenis = buat_nilai_jenis(id_guru_int, jabatan_bersih, jenis_dari_form=j)

                ttd = PenandatanganSurat(
                    surat_id=surat.id,
                    jenis=nilai_jenis,
                    id_guru=id_guru_int,
                    nama=nama_bersih,
                    jabatan=jabatan_bersih
                )
                db.session.add(ttd)

                if status_baru == 'Diajukan':
                    jumlah_diajukan += 1
                    if id_guru_int:
                        guru = Guru.query.get(id_guru_int)
                        if not guru:
                            flash(f"❌ ID {id_guru_int} tidak terdaftar sebagai guru", "danger")
                            continue
                        akun_penerima = User.query.filter_by(guru_id=id_guru_int, aktif=True).first()
                        if akun_penerima:
                            penerima = PenerimaSuratDiajukan(
                                surat_id=surat.id,
                                user_id=akun_penerima.id,
                                nama=nama_bersih,
                                jabatan=jabatan_bersih,
                                status_tinjau='Menunggu'
                            )
                            db.session.add(penerima)
                            jumlah_berhasil += 1
                            flash(f"✅ Berhasil diajukan ke: {nama_bersih}", "success")
                        else:
                            flash(f"⚠️ {nama_bersih} terdaftar tapi belum punya akun aktif", "warning")
                    else:
                        flash(f"ℹ️ {nama_bersih} diisi manual, tidak diajukan", "info")

            db.session.commit()

            if status_baru == 'Diajukan':
                if jumlah_diajukan == 0:
                    flash('Tidak ada penandatangan yang dipilih!', 'warning')
                elif jumlah_berhasil == 0:
                    flash('Surat disimpan, tetapi tidak ada penandatangan yang memiliki akun sistem untuk menerima.', 'warning')
                else:
                    flash(f'Surat berhasil diperbarui dan diajukan ke {jumlah_berhasil} penandatangan!', 'success')
            else:
                flash('Surat berhasil diperbarui dan disimpan sebagai draf.', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Gagal memperbarui surat: {str(e)}', 'danger')
            return redirect(request.url)

        return redirect(url_for('surat_menyurat.index'))

    context = {
        'active_page': 'surat_menyurat',
        'sub_page': 'ubah_keluar',
        'halaman_aktif': session.get('halaman_aktif', 'utama'),
        'role': session.get('role', session.get('jabatan', '')),
        'user': user,
        'surat': surat,
        'daftar_jabatan_tugas': daftar_jabatan_tugas,
        'daftar_ttd': daftar_ttd
    }

    return render_template('index.html', **context)