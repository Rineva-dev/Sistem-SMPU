from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
from models import db, TahunPelajaran, User
from datetime import datetime

umum_bp = Blueprint('umum', __name__, url_prefix='/')

# ==========================================
# ✅ FUNGSI PENGECEKAN HAK AKSES TAHUN PELAJARAN
# ==========================================
def bisa_kelola_tahun_pelajaran(user, halaman_aktif='utama'):
    daftar_tugas = []

    if hasattr(user, 'tugas_tambahan') and user.tugas_tambahan:
        if isinstance(user.tugas_tambahan, str):
            daftar_tugas = [t.strip() for t in user.tugas_tambahan.split(',')]
        else:
            daftar_tugas = user.tugas_tambahan

    return (
        user.jabatan in ["Admin", "Kepala Sekolah", "Tata Usaha", "TU", "Waka Kurikulum"]
        or ("Admin Sistem" in daftar_tugas and halaman_aktif == "admin_sistem")
        or ("Waka Kurikulum" in daftar_tugas and halaman_aktif == "waka_kurikulum")
    )

@umum_bp.before_app_request
def load_tahun_aktif():
    """Muat tahun pelajaran yang dipilih ke semua halaman"""
    g.tahun_pelajaran = session.get('tahun_pelajaran')
    if not g.tahun_pelajaran:
        aktif = TahunPelajaran.query.filter_by(aktif=True).first()
        g.tahun_pelajaran = aktif.kode if aktif else ""

# ==========================================
# HALAMAN KELOLA TAHUN PELAJARAN
# ==========================================
@umum_bp.route('/tahun-pelajaran', methods=['GET', 'POST'])
def kelola_tahun_pelajaran():
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None
    if not user:
        flash("Sesi tidak valid, silakan login kembali", "danger")
        return redirect(url_for('login.halaman_login'))

    halaman_aktif = session.get('halaman_aktif', 'utama')

    if not bisa_kelola_tahun_pelajaran(user, halaman_aktif):
        flash("Anda tidak memiliki hak akses untuk mengelola Tahun Pelajaran!", "danger")
        return redirect(url_for('dashboard.index'))

    # --- PROSES FORM POST ---
    if request.method == "POST":
        if "tambah" in request.form:
            tahun_mulai = int(request.form.get("tahun_mulai"))
            tahun_selesai = int(request.form.get("tahun_selesai"))
            semester = int(request.form.get("semester"))
            tanggal_mulai_str = request.form.get("tanggal_mulai")
            tanggal_selesai_str = request.form.get("tanggal_selesai")

            tanggal_mulai = datetime.strptime(tanggal_mulai_str, "%Y-%m-%d").date()
            tanggal_selesai = datetime.strptime(tanggal_selesai_str, "%Y-%m-%d").date()

            kode = f"{tahun_mulai}/{tahun_selesai}-{semester}"
            nama = f"Tahun Pelajaran {tahun_mulai}/{tahun_selesai} - Semester {semester}"

            baru = TahunPelajaran(
                kode=kode,
                nama=nama,
                tahun_mulai=tahun_mulai,
                tahun_selesai=tahun_selesai,
                semester=semester,
                tanggal_mulai=tanggal_mulai,
                tanggal_selesai=tanggal_selesai
            )
            db.session.add(baru)
            db.session.commit()
            flash("Data tahun pelajaran berhasil ditambahkan!", "success")

        elif "perbarui" in request.form:
            id = request.form.get("id")
            tahun_mulai = int(request.form.get("tahun_mulai"))
            tahun_selesai = int(request.form.get("tahun_selesai"))
            semester = int(request.form.get("semester"))
            tanggal_mulai_str = request.form.get("tanggal_mulai")
            tanggal_selesai_str = request.form.get("tanggal_selesai")

            tanggal_mulai = datetime.strptime(tanggal_mulai_str, "%Y-%m-%d").date()
            tanggal_selesai = datetime.strptime(tanggal_selesai_str, "%Y-%m-%d").date()

            tp = TahunPelajaran.query.get_or_404(id)
            kode_baru = f"{tahun_mulai}/{tahun_selesai}-{semester}"
            nama_baru = f"Tahun Pelajaran {tahun_mulai}/{tahun_selesai} - Semester {semester}"

            tp.kode = kode_baru
            tp.nama = nama_baru
            tp.tahun_mulai = tahun_mulai
            tp.tahun_selesai = tahun_selesai
            tp.semester = semester
            tp.tanggal_mulai = tanggal_mulai
            tp.tanggal_selesai = tanggal_selesai

            db.session.commit()
            flash("Perubahan berhasil disimpan!", "success")

        elif "jadikan_aktif" in request.form:
            id = request.form.get("id")
            TahunPelajaran.set_aktif(id)
            flash("Berhasil diaktifkan!", "success")

        return redirect(url_for("umum.kelola_tahun_pelajaran"))

    daftar_tahun = TahunPelajaran.query.order_by(TahunPelajaran.kode.desc()).all()

    return render_template(
        "index.html",
        active_page="tahun_pelajaran",
        sub_page="daftar",
        user=user,
        halaman_aktif=halaman_aktif,
        daftar_tahun=daftar_tahun
    )

# ==========================================
# PROSES GANTI TAHUN PELAJARAN
# ==========================================
@umum_bp.route('/ganti-tahun', methods=['POST'])
def ganti_tahun():
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None
    halaman_aktif = session.get('halaman_aktif', 'utama')

    if not user or not bisa_kelola_tahun_pelajaran(user, halaman_aktif):
        flash("Tidak memiliki hak untuk mengubah tahun pelajaran!", "danger")
        return redirect(request.referrer or url_for('dashboard.index'))

    tahun_baru = request.form.get('tahun_pelajaran')
    if tahun_baru:
        session['tahun_pelajaran'] = tahun_baru
        g.tahun_pelajaran = tahun_baru
        flash(f'Tahun pelajaran berhasil diubah ke {tahun_baru}', 'success')
    else:
        flash('Pilihan tahun pelajaran tidak valid', 'warning')

    return redirect(request.referrer or url_for('dashboard.index'))