from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
from models import db, TahunPelajaran, User, RiwayatKelas
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

def validasi_data_tahun_pelajaran(form):
    try:
        tahun_mulai = int(form.get("tahun_mulai", ""))
        tahun_selesai = int(form.get("tahun_selesai", ""))
        semester = int(form.get("semester", ""))

        tanggal_mulai = datetime.strptime(
            form.get("tanggal_mulai", ""), "%Y-%m-%d"
        ).date()

        tanggal_selesai = datetime.strptime(
            form.get("tanggal_selesai", ""), "%Y-%m-%d"
        ).date()

    except (ValueError, TypeError):
        raise ValueError("Data tahun pelajaran atau tanggal tidak valid.")

    if tahun_selesai != tahun_mulai + 1:
        raise ValueError("Tahun selesai harus satu tahun setelah tahun mulai.")

    if semester not in (1, 2):
        raise ValueError("Semester hanya boleh 1 (Ganjil) atau 2 (Genap).")

    if tanggal_mulai > tanggal_selesai:
        raise ValueError("Tanggal mulai tidak boleh melewati tanggal selesai.")

    kode = f"{tahun_mulai}/{tahun_selesai}-{semester}"
    nama = (
        f"Tahun Pelajaran {tahun_mulai}/{tahun_selesai} "
        f"- Semester {semester}"
    )

    return {
        "kode": kode,
        "nama": nama,
        "tahun_mulai": tahun_mulai,
        "tahun_selesai": tahun_selesai,
        "semester": semester,
        "tanggal_mulai": tanggal_mulai,
        "tanggal_selesai": tanggal_selesai
    }

@umum_bp.before_app_request
def load_tahun_aktif():
    """
    Memisahkan tahun pelajaran operasional dan tahun pilihan pengguna.
    """

    # 1. Tahun pelajaran operasional sekolah dari database
    tahun_operasional = TahunPelajaran.query.filter_by(
        aktif=True
    ).first()

    g.tahun_pelajaran_aktif = (
        tahun_operasional.kode if tahun_operasional else ""
    )

    # 2. Tahun pelajaran pilihan pengguna untuk melihat data
    tahun_pilihan = session.get('tahun_pelajaran')

    # Pastikan tahun pilihan masih terdaftar
    if tahun_pilihan:
        tersedia = TahunPelajaran.query.filter_by(
            kode=tahun_pilihan
        ).first()

        if not tersedia:
            tahun_pilihan = None
            session.pop('tahun_pelajaran', None)

    # 3. Jika belum memilih, gunakan tahun operasional
    g.tahun_pelajaran = (
        tahun_pilihan or g.tahun_pelajaran_aktif
    )

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

        # ==========================================
        # TAMBAH TAHUN PELAJARAN
        # ==========================================
        if "tambah" in request.form:
            try:
                data = validasi_data_tahun_pelajaran(request.form)

                duplikat = TahunPelajaran.query.filter_by(
                    kode=data["kode"]
                ).first()

                if duplikat:
                    raise ValueError(
                        f"Tahun pelajaran {data['kode']} sudah tersedia."
                    )

                baru = TahunPelajaran(
                    kode=data["kode"],
                    nama=data["nama"],
                    tahun_mulai=data["tahun_mulai"],
                    tahun_selesai=data["tahun_selesai"],
                    semester=data["semester"],
                    tanggal_mulai=data["tanggal_mulai"],
                    tanggal_selesai=data["tanggal_selesai"],
                    aktif=False
                )

                db.session.add(baru)
                db.session.commit()

                flash("Tahun pelajaran berhasil ditambahkan!", "success")

            except ValueError as e:
                db.session.rollback()
                flash(str(e), "danger")

            except Exception:
                db.session.rollback()
                flash("Gagal menambahkan tahun pelajaran.", "danger")

        # ==========================================
        # EDIT TAHUN PELAJARAN
        # ==========================================
        elif "perbarui" in request.form:
            try:
                id_tp = request.form.get("id")

                if not id_tp or not id_tp.isdigit():
                    raise ValueError("ID tahun pelajaran tidak valid.")

                tp = db.session.get(TahunPelajaran, int(id_tp))

                if not tp:
                    raise ValueError("Tahun pelajaran tidak ditemukan.")

                data = validasi_data_tahun_pelajaran(request.form)

                # Identitas periode tidak boleh diubah jika sudah
                # memiliki riwayat siswa.
                sudah_digunakan = RiwayatKelas.query.filter_by(
                    tahun_pelajaran=tp.kode
                ).first()

                identitas_berubah = (
                    tp.kode != data["kode"]
                    or tp.tahun_mulai != data["tahun_mulai"]
                    or tp.tahun_selesai != data["tahun_selesai"]
                    or tp.semester != data["semester"]
                )

                if sudah_digunakan and identitas_berubah:
                    raise ValueError(
                        "Identitas periode tidak dapat diubah karena "
                        "sudah memiliki riwayat siswa."
                    )

                duplikat = TahunPelajaran.query.filter(
                    TahunPelajaran.kode == data["kode"],
                    TahunPelajaran.id != tp.id
                ).first()

                if duplikat:
                    raise ValueError(
                        f"Tahun pelajaran {data['kode']} sudah tersedia."
                    )

                tp.kode = data["kode"]
                tp.nama = data["nama"]
                tp.tahun_mulai = data["tahun_mulai"]
                tp.tahun_selesai = data["tahun_selesai"]
                tp.semester = data["semester"]
                tp.tanggal_mulai = data["tanggal_mulai"]
                tp.tanggal_selesai = data["tanggal_selesai"]

                db.session.commit()

                flash("Perubahan tahun pelajaran berhasil disimpan!", "success")

            except ValueError as e:
                db.session.rollback()
                flash(str(e), "danger")

            except Exception:
                db.session.rollback()
                flash("Gagal memperbarui tahun pelajaran.", "danger")

        # ==========================================
        # AKTIFKAN TAHUN PELAJARAN
        # ==========================================
        elif "jadikan_aktif" in request.form:
            id_tp = request.form.get("id")

            try:
                if not id_tp or not id_tp.isdigit():
                    raise ValueError("ID tahun pelajaran tidak valid.")

                TahunPelajaran.set_aktif(int(id_tp))

                flash(
                    "Tahun pelajaran berhasil diaktifkan!",
                    "success"
                )

            except ValueError as e:
                flash(str(e), "danger")

            except Exception:
                db.session.rollback()
                flash(
                    "Terjadi kesalahan saat mengaktifkan tahun pelajaran.",
                    "danger"
                )

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

    tahun_baru = request.form.get('tahun_pelajaran', '').strip()

    if not tahun_baru:
        flash("Silakan pilih tahun pelajaran.", "warning")
        return redirect(request.referrer or url_for('dashboard.index'))

    # Pastikan periode benar-benar terdaftar
    tp = TahunPelajaran.query.filter_by(kode=tahun_baru).first()

    if not tp:
        flash("Tahun pelajaran tidak ditemukan.", "danger")
        return redirect(request.referrer or url_for('dashboard.index'))

    # Hanya mengubah periode tampilan pengguna,
    # bukan mengubah periode operasional sekolah.
    session['tahun_pelajaran'] = tp.kode
    g.tahun_pelajaran = tp.kode

    flash(f"Tahun pelajaran berhasil diubah ke {tp.kode}.", "success")

    return redirect(request.referrer or url_for('dashboard.index'))
