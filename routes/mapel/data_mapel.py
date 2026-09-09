from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, MataPelajaran, User
from functools import wraps

mapel_bp = Blueprint('data_mapel', __name__, url_prefix='/mapel')

# --------------------------
# Cek Hak Akses
# --------------------------
def bisa_kelola_mapel(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login.halaman_login'))
        jabatan = session.get('jabatan', '')
        tugas = session.get('tugas_tambahan', '')
        daftar_tugas = [t.strip() for t in tugas.split(',')] if tugas else []
        if jabatan not in ["Admin", "Tata Usaha", "TU", "Waka Kurikulum"] and "Admin Sistem" not in daftar_tugas:
            flash("Anda tidak memiliki hak akses untuk mengelola mata pelajaran", "danger")
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorator

# --------------------------
# Halaman Daftar
# --------------------------
@mapel_bp.route('/')
@bisa_kelola_mapel
def halaman_daftar_mapel():
    user = db.session.get(User, session.get('user_id'))
    daftar_mapel = MataPelajaran.query.order_by(MataPelajaran.nama_pelajaran).all()

    return render_template(
        'index.html',
        active_page='data_mapel',
        sub_page='daftar',
        daftar_mapel=daftar_mapel,
        user=user,
        user_name=session.get('user_name'),
        jabatan=session.get('jabatan'),
        halaman_aktif=session.get('halaman_aktif', 'utama')
    )

@mapel_bp.route('/tambah', methods=['GET', 'POST'])
@bisa_kelola_mapel
def tambah_mapel():
    user = db.session.get(User, session.get('user_id'))
    if request.method == 'POST':
        kode = request.form.get('kode', '').strip().upper()
        nama = request.form.get('nama_pelajaran', '').strip()
        kelompok = request.form.get('kelompok', '').strip()
        keterangan = request.form.get('keterangan', '').strip()

        if not kode or not nama:
            flash("Kode dan Nama Mata Pelajaran wajib diisi!", "danger")
            return redirect(url_for('data_mapel.tambah_mapel'))

        cek = MataPelajaran.query.filter_by(kode=kode).first()
        if cek:
            flash(f"Kode {kode} sudah terdaftar!", "warning")
            return redirect(url_for('data_mapel.tambah_mapel'))

        baru = MataPelajaran(
            kode=kode, nama_pelajaran=nama,
            kelompok=kelompok, keterangan=keterangan
        )
        db.session.add(baru)
        db.session.commit()
        flash(f"Mata pelajaran {nama} berhasil ditambahkan!", "success")
        return redirect(url_for('data_mapel.halaman_daftar_mapel'))

    return render_template(
        'index.html',
        active_page='data_mapel',
        sub_page='tambah',
        mode='tambah',
        user=user,
        user_name=session.get('user_name'),
        jabatan=session.get('jabatan'),
        tugas_tambahan=session.get('tugas_tambahan'),
        logged_in=session.get('logged_in'),
        halaman_aktif=session.get('halaman_aktif', 'utama')
    )

@mapel_bp.route('/ubah/<int:id>', methods=['GET', 'POST'])
@bisa_kelola_mapel
def ubah_mapel(id):
    user = db.session.get(User, session.get('user_id'))
    mapel = MataPelajaran.query.get_or_404(id)

    if request.method == 'POST':
        kode = request.form.get('kode', '').strip().upper()
        nama = request.form.get('nama_pelajaran', '').strip()
        kelompok = request.form.get('kelompok', '').strip()
        keterangan = request.form.get('keterangan', '').strip()

        if not kode or not nama:
            flash("Kode dan Nama Mata Pelajaran wajib diisi!", "danger")
            return redirect(url_for('data_mapel.ubah_mapel', id=id))

        cek = MataPelajaran.query.filter(MataPelajaran.id != id, MataPelajaran.kode == kode).first()
        if cek:
            flash(f"Kode {kode} sudah terpakai!", "warning")
            return redirect(url_for('data_mapel.ubah_mapel', id=id))

        mapel.kode = kode
        mapel.nama_pelajaran = nama
        mapel.kelompok = kelompok
        mapel.keterangan = keterangan
        db.session.commit()
        flash("Data mata pelajaran diperbarui!", "success")
        return redirect(url_for('data_mapel.halaman_daftar_mapel'))

    return render_template(
        'index.html',
        active_page='data_mapel',
        sub_page='ubah',
        mode='ubah',
        mapel=mapel,
        user=user,
        user_name=session.get('user_name'),
        jabatan=session.get('jabatan'),
        tugas_tambahan=session.get('tugas_tambahan'),
        logged_in=session.get('logged_in'),
        halaman_aktif=session.get('halaman_aktif', 'utama')
    )

# --------------------------
# Hapus
# --------------------------
@mapel_bp.route('/hapus/<int:id>', methods=['POST'])
@bisa_kelola_mapel
def hapus_mapel(id):
    mapel = MataPelajaran.query.get_or_404(id)
    db.session.delete(mapel)
    db.session.commit()
    flash(f"Mata pelajaran {mapel.nama_pelajaran} telah dihapus!", "success")
    return redirect(url_for('data_mapel.halaman_daftar_mapel'))