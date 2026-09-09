from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from datetime import datetime
from models import db, User, KalenderPendidikan, TahunPelajaran

kalender_bp = Blueprint('kalender', __name__, url_prefix='/')

def bisa_kelola(user, halaman_aktif='utama'):
    daftar_tugas = []

    if hasattr(user, 'tugas_tambahan') and user.tugas_tambahan:
        if isinstance(user.tugas_tambahan, str):
            daftar_tugas = [t.strip() for t in user.tugas_tambahan.split(',')]
        else:
            daftar_tugas = user.tugas_tambahan

    return (
        user.jabatan == "Admin"
        or user.jabatan == "Waka Kurikulum"
        or ("Admin Sistem" in daftar_tugas and halaman_aktif == "admin_sistem")
        or ("Waka Kurikulum" in daftar_tugas and halaman_aktif == "waka_kurikulum")
    )

def bisa_setujui(user):
    return user.jabatan in ["Admin", "Kepala Sekolah"]

def bisa_lihat_kalender(user, halaman_aktif='utama'):
    daftar_tugas = []
    if hasattr(user, 'tugas_tambahan') and user.tugas_tambahan:
        if isinstance(user.tugas_tambahan, str):
            daftar_tugas = [t.strip() for t in user.tugas_tambahan.split(',')]
        else:
            daftar_tugas = user.tugas_tambahan

    return (
        # Semua jabatan utama boleh melihat
        user.jabatan in ["Admin", "Kepala Sekolah", "Tata Usaha", "TU", "Waka Kurikulum", "Guru", "Wali Kelas", "Waka Kesiswaan", "Pembina Ekstrakurikuler"]
        # Bisa melihat jika sedang di halaman tugas tambahan yang sesuai
        or ("Admin Sistem" in daftar_tugas and halaman_aktif == "admin_sistem")
        or ("Waka Kurikulum" in daftar_tugas and halaman_aktif == "waka_kurikulum")
        or ("Wali Kelas" in daftar_tugas and halaman_aktif == "wali_kelas")
        or ("Waka Kesiswaan" in daftar_tugas and halaman_aktif == "waka_kesiswaan")
        or ("Pembina Ekstrakurikuler" in daftar_tugas and halaman_aktif == "pembina_ekskul")
    )

@kalender_bp.route('/kalender-sekolah/')
def halaman_kalender():
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if not user:
        flash("Sesi tidak valid, silakan login kembali", "danger")
        return redirect(url_for('login.halaman_login'))

    halaman_aktif = session.get('halaman_aktif', 'utama')

    # ✅ Baca parameter asal dari URL
    asal = request.args.get('asal', '')

    # ✅ Tentukan halaman aktif sesuai asal akses
    if asal == 'dashboard':
        # Dibuka dari kotak tanggal di dashboard
        if halaman_aktif == 'utama' and user.jabatan == 'Guru':
            active_page = 'dashboard_guru'
        else:
            active_page = 'dashboard'
    else:
        # Dibuka dari menu sidebar atau akses langsung
        active_page = 'kalender'

    tp_dipilih = TahunPelajaran.query.filter_by(kode=g.tahun_pelajaran).first() if g.tahun_pelajaran else None
    daftar_kegiatan = []
    sudah_disetujui = False
    semester_aktif = None

    if tp_dipilih:
        daftar_kegiatan = KalenderPendidikan.query.filter_by(
            tahun_pelajaran_id = tp_dipilih.id
        ).order_by(KalenderPendidikan.tanggal_mulai).all()

        sudah_disetujui = all(keg.disetujui for keg in daftar_kegiatan) if daftar_kegiatan else False
        semester_aktif = 'ganjil' if tp_dipilih.semester == 1 else 'genap'

    return render_template(
        'umum/kalender_pendidikan.html',
        halaman_aktif = halaman_aktif,
        active_page = active_page,  # ✅ Gunakan nilai yang sudah disesuaikan
        user = user,
        tahun_pelajaran = tp_dipilih.nama if tp_dipilih else 'Belum ditentukan',
        semester_aktif = semester_aktif,
        daftar_kegiatan = daftar_kegiatan,
        disetujui = sudah_disetujui,
        bisa_kelola = bisa_kelola(user, halaman_aktif),
        bisa_setujui = bisa_setujui(user)
    )

# ==========================================
# ✅ RUTE TAMBAH / UBAH / HAPUS / SETUJUI - TETAP SAMA
# ==========================================
@kalender_bp.route('/tambah', methods=['POST'])
def tambah_kegiatan():
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None
    halaman_aktif = session.get('halaman_aktif', 'utama')

    if not user or not bisa_kelola(user, halaman_aktif):
        flash("Anda tidak memiliki hak akses!", "danger")
        return redirect(url_for('kalender.halaman_kalender'))

    tp_dipilih = TahunPelajaran.query.filter_by(kode=g.tahun_pelajaran).first()
    if not tp_dipilih:
        flash("Silakan pilih Tahun Pelajaran terlebih dahulu!", "warning")
        return redirect(url_for('kalender.halaman_kalender'))

    nama = request.form.get('nama_kegiatan', '').strip()
    tgl_mulai = request.form.get('tanggal_mulai')
    tgl_selesai = request.form.get('tanggal_selesai')
    semester = request.form.get('semester', '').strip()
    jenis = request.form.get('jenis', '').strip()

    if not all([nama, tgl_mulai, tgl_selesai, semester, jenis]):
        flash("Semua kolom wajib diisi!", "danger")
        return redirect(url_for('kalender.halaman_kalender'))

    if tgl_selesai < tgl_mulai:
        flash("Tanggal selesai tidak boleh lebih awal!", "danger")
        return redirect(url_for('kalender.halaman_kalender'))

    baru = KalenderPendidikan(
        nama_kegiatan = nama,
        tanggal_mulai = datetime.strptime(tgl_mulai, '%Y-%m-%d'),
        tanggal_selesai = datetime.strptime(tgl_selesai, '%Y-%m-%d'),
        semester = semester,
        jenis = jenis,
        tahun_pelajaran_id = tp_dipilih.id
    )

    db.session.add(baru)
    db.session.commit()
    flash("Kegiatan berhasil ditambahkan!", "success")
    return redirect(url_for('kalender.halaman_kalender'))

@kalender_bp.route('/ubah/<int:id>', methods=['POST'])
def ubah_kegiatan(id):
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None
    halaman_aktif = session.get('halaman_aktif', 'utama')

    if not user or not bisa_kelola(user, halaman_aktif):
        flash("Anda tidak memiliki hak akses!", "danger")
        return redirect(url_for('kalender.halaman_kalender'))

    kegiatan = KalenderPendidikan.query.get_or_404(id)

    kegiatan.nama_kegiatan = request.form.get('nama_kegiatan', '').strip()
    kegiatan.tanggal_mulai = datetime.strptime(request.form.get('tanggal_mulai'), '%Y-%m-%d')
    kegiatan.tanggal_selesai = datetime.strptime(request.form.get('tanggal_selesai'), '%Y-%m-%d')
    kegiatan.semester = request.form.get('semester', '').strip()
    kegiatan.jenis = request.form.get('jenis', '').strip()

    if kegiatan.tanggal_selesai < kegiatan.tanggal_mulai:
        flash("Tanggal tidak valid!", "danger")
        return redirect(url_for('kalender.halaman_kalender'))

    db.session.commit()
    flash("Kegiatan berhasil diperbarui!", "success")
    return redirect(url_for('kalender.halaman_kalender'))

@kalender_bp.route('/hapus/<int:id>', methods=['POST'])
def hapus_kegiatan(id):
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None
    halaman_aktif = session.get('halaman_aktif', 'utama')

    if not user or not bisa_kelola(user, halaman_aktif):
        flash("Anda tidak memiliki hak akses!", "danger")
        return redirect(url_for('kalender.halaman_kalender'))

    kegiatan = KalenderPendidikan.query.get_or_404(id)
    db.session.delete(kegiatan)
    db.session.commit()
    flash("Kegiatan berhasil dihapus!", "success")
    return redirect(url_for('kalender.halaman_kalender'))

@kalender_bp.route('/setujui', methods=['POST'])
def setujui_kalender():
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None
    if not user or not bisa_setujui(user):
        flash("Hanya Kepala Sekolah yang bisa menyetujui!", "danger")
        return redirect(url_for('kalender.halaman_kalender'))

    tp_dipilih = TahunPelajaran.query.filter_by(kode=g.tahun_pelajaran).first()
    if not tp_dipilih:
        flash("Tahun pelajaran belum dipilih!", "warning")
        return redirect(url_for('kalender.halaman_kalender'))

    KalenderPendidikan.query.filter_by(tahun_pelajaran_id=tp_dipilih.id).update({"disetujui": True})
    db.session.commit()

    flash("Kalender pendidikan telah disetujui dan berlaku!", "success")
    return redirect(url_for('kalender.halaman_kalender'))