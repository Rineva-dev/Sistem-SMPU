
from datetime import date

from flask import (
    Blueprint, render_template, session,
    redirect, url_for, request, flash
)

from sqlalchemy import or_

from models import (
    db, User, Guru, Kelas, TahunPelajaran,
    RiwayatKelas, Siswa, CatatanPerkembanganSiswa
)


catatan_perkembangan_bp = Blueprint(
    'catatan_perkembangan',
    __name__,
    url_prefix='/wali-kelas'
)


# =========================================================
# KONFIGURASI KATEGORI DAN STATUS
# =========================================================

KATEGORI_CATATAN = [
    'Akademik',
    'Kedisiplinan',
    'Perilaku',
    'Sosial',
    'Tanggung Jawab',
    'Prestasi',
    'Kemandirian',
    'Lainnya'
]

STATUS_TINDAK_LANJUT = [
    'belum_ditindaklanjuti',
    'sedang_ditindaklanjuti',
    'selesai'
]


# =========================================================
# HELPER
# =========================================================

def get_base_tahun(kode_tp):
    if not kode_tp:
        return None

    return kode_tp.split('-')[0].strip()


def get_wali_context():
    """
    Memastikan pengguna login dan mengambil:
    user, guru, tahun pelajaran aktif, serta kelas yang diampu.
    """

    if (
        not session.get('logged_in')
        or session.get('sistem_mode') != 'sekolah'
        or not session.get('user_id')
    ):
        return None

    user = db.session.get(User, session.get('user_id'))

    if not user or not user.guru_id:
        return None

    guru = db.session.get(Guru, user.guru_id)

    if not guru:
        return None

    tahun_pelajaran = (
        TahunPelajaran.query
        .filter_by(aktif=True)
        .order_by(TahunPelajaran.id.desc())
        .first()
    )

    if not tahun_pelajaran:
        return {
            'user': user,
            'guru': guru,
            'tahun_pelajaran': None,
            'daftar_kelas': []
        }

    tahun_dasar = get_base_tahun(tahun_pelajaran.kode)

    daftar_kelas = (
        Kelas.query
        .filter(
            Kelas.wali_kelas_id == guru.id,
            Kelas.tahun_pelajaran == tahun_dasar
        )
        .order_by(Kelas.jenjang, Kelas.nama_kelas)
        .all()
    )

    return {
        'user': user,
        'guru': guru,
        'tahun_pelajaran': tahun_pelajaran,
        'daftar_kelas': daftar_kelas
    }


def siswa_terdaftar_di_kelas(siswa_id, kelas_id, kode_tp):
    """
    Validasi siswa berdasarkan riwayat kelas
    pada tahun pelajaran aktif.
    """

    return RiwayatKelas.query.filter_by(
        siswa_id=siswa_id,
        kelas_id=kelas_id,
        tahun_pelajaran=kode_tp
    ).first() is not None


def ambil_catatan_milik_guru(catatan_id, guru_id, kode_tp, kelas_ids):
    """
    Mengambil catatan yang dibuat guru sendiri,
    pada tahun pelajaran aktif, dan kelas yang diampu.
    """

    if not kelas_ids:
        return None

    return CatatanPerkembanganSiswa.query.filter(
        CatatanPerkembanganSiswa.id == catatan_id,
        CatatanPerkembanganSiswa.guru_id == guru_id,
        CatatanPerkembanganSiswa.tahun_pelajaran == kode_tp,
        CatatanPerkembanganSiswa.kelas_id.in_(kelas_ids)
    ).first()


def redirect_ke_catatan(kelas_id=None):
    if kelas_id:
        return redirect(
            url_for(
                'catatan_perkembangan.index',
                kelas_id=kelas_id
            )
        )

    return redirect(url_for('catatan_perkembangan.index'))


# =========================================================
# HALAMAN UTAMA CATATAN PERKEMBANGAN
# =========================================================

@catatan_perkembangan_bp.route('/catatan-perkembangan')
def index():

    context = get_wali_context()

    if not context:
        return redirect(url_for('login.halaman_login'))

    user = context['user']
    guru = context['guru']
    tahun_pelajaran = context['tahun_pelajaran']
    daftar_kelas = context['daftar_kelas']

    if not tahun_pelajaran:
        return render_template(
            'sections/wali_kelas/catatan_perkembangan.html',
            active_page='catatan_perkembangan',
            halaman_aktif='wali_kelas',
            user=user,
            guru=guru,
            tahun_pelajaran=None,
            daftar_kelas=[],
            daftar_siswa=[],
            daftar_catatan=[],
            kelas_terpilih=None,
            kategori_catatan=KATEGORI_CATATAN,
            status_tindak_lanjut=STATUS_TINDAK_LANJUT,
            pesan="Belum ada tahun pelajaran aktif."
        )

    kode_tp = tahun_pelajaran.kode
    kelas_ids = [kelas.id for kelas in daftar_kelas]

    if not daftar_kelas:
        return render_template(
            'sections/wali_kelas/catatan_perkembangan.html',
            active_page='catatan_perkembangan',
            halaman_aktif='wali_kelas',
            user=user,
            guru=guru,
            tahun_pelajaran=tahun_pelajaran,
            daftar_kelas=[],
            daftar_siswa=[],
            daftar_catatan=[],
            kelas_terpilih=None,
            kategori_catatan=KATEGORI_CATATAN,
            status_tindak_lanjut=STATUS_TINDAK_LANJUT,
            pesan="Anda belum ditugaskan sebagai Wali Kelas."
        )

    # -----------------------------------------------------
    # VALIDASI FILTER KELAS
    # -----------------------------------------------------

    kelas_id = request.args.get('kelas_id', type=int)

    if kelas_id and kelas_id not in kelas_ids:
        return "Anda tidak memiliki akses ke kelas tersebut.", 403

    kelas_filter = [kelas_id] if kelas_id else kelas_ids

    kelas_terpilih = next(
        (k for k in daftar_kelas if k.id == kelas_id),
        None
    )

    # -----------------------------------------------------
    # FILTER PENCARIAN DAN KATEGORI
    # -----------------------------------------------------

    pencarian = request.args.get('q', '').strip()
    kategori = request.args.get('kategori', '').strip()
    status = request.args.get('status', '').strip()

    # -----------------------------------------------------
    # AMBIL SISWA BERDASARKAN RIWAYAT KELAS
    # -----------------------------------------------------

    daftar_siswa = (
        db.session.query(Siswa)
        .join(
            RiwayatKelas,
            RiwayatKelas.siswa_id == Siswa.id
        )
        .filter(
            RiwayatKelas.tahun_pelajaran == kode_tp,
            RiwayatKelas.kelas_id.in_(kelas_ids)
        )
        .order_by(Siswa.nama.asc())
        .all()
    )

    # -----------------------------------------------------
    # AMBIL CATATAN PERKEMBANGAN
    # -----------------------------------------------------

    query_catatan = (
        CatatanPerkembanganSiswa.query
        .filter(
            CatatanPerkembanganSiswa.tahun_pelajaran == kode_tp,
            CatatanPerkembanganSiswa.kelas_id.in_(kelas_filter)
        )
    )

    if kategori in KATEGORI_CATATAN:
        query_catatan = query_catatan.filter(
            CatatanPerkembanganSiswa.kategori == kategori
        )

    if status in STATUS_TINDAK_LANJUT:
        query_catatan = query_catatan.filter(
            CatatanPerkembanganSiswa.status_tindak_lanjut == status
        )

    if pencarian:
        query_catatan = (
            query_catatan
            .join(
                Siswa,
                CatatanPerkembanganSiswa.siswa_id == Siswa.id
            )
            .filter(
                or_(
                    Siswa.nama.ilike(f'%{pencarian}%'),
                    CatatanPerkembanganSiswa.judul.ilike(
                        f'%{pencarian}%'
                    ),
                    CatatanPerkembanganSiswa.deskripsi.ilike(
                        f'%{pencarian}%'
                    )
                )
            )
        )

    daftar_catatan = (
        query_catatan
        .order_by(
            CatatanPerkembanganSiswa.tanggal.desc(),
            CatatanPerkembanganSiswa.id.desc()
        )
        .all()
    )

    return render_template(
        'sections/wali_kelas/catatan_perkembangan.html',
        active_page='catatan_perkembangan_wali',
        halaman_aktif='wali_kelas',
        user=user,
        guru=guru,
        tahun_pelajaran=tahun_pelajaran,
        daftar_kelas=daftar_kelas,
        daftar_siswa=daftar_siswa,
        daftar_catatan=daftar_catatan,
        kelas_terpilih=kelas_terpilih,
        kategori_catatan=KATEGORI_CATATAN,
        status_tindak_lanjut=STATUS_TINDAK_LANJUT,
        pencarian=pencarian,
        kategori_terpilih=kategori,
        status_terpilih=status,
        pesan=None
    )


# =========================================================
# TAMBAH CATATAN
# =========================================================

@catatan_perkembangan_bp.route(
    '/catatan-perkembangan/tambah',
    methods=['POST']
)
def tambah():

    context = get_wali_context()

    if not context:
        return redirect(url_for('login.halaman_login'))

    guru = context['guru']
    tahun_pelajaran = context['tahun_pelajaran']
    daftar_kelas = context['daftar_kelas']

    if not tahun_pelajaran:
        flash('Tahun pelajaran aktif belum tersedia.', 'warning')
        return redirect_ke_catatan()

    kelas_ids = [kelas.id for kelas in daftar_kelas]

    if not kelas_ids:
        flash('Anda belum memiliki kelas yang diampu.', 'warning')
        return redirect_ke_catatan()

    try:
        siswa_id = request.form.get('siswa_id', type=int)
        kelas_id = request.form.get('kelas_id', type=int)

        tanggal_input = request.form.get('tanggal', '').strip()
        kategori = request.form.get('kategori', '').strip()
        judul = request.form.get('judul', '').strip()
        deskripsi = request.form.get('deskripsi', '').strip()
        tindak_lanjut = request.form.get('tindak_lanjut', '').strip()

        # Validasi kelas
        if kelas_id not in kelas_ids:
            flash('Kelas tidak valid atau bukan kelas yang Anda ampu.', 'danger')
            return redirect_ke_catatan()

        # Validasi kategori
        if kategori not in KATEGORI_CATATAN:
            flash('Kategori catatan tidak valid.', 'warning')
            return redirect_ke_catatan(kelas_id)

        # Validasi data wajib
        if not siswa_id or not judul or not deskripsi or not tanggal_input:
            flash('Lengkapi seluruh data wajib.', 'warning')
            return redirect_ke_catatan(kelas_id)

        tanggal_catatan = date.fromisoformat(tanggal_input)

        # Validasi siswa berdasarkan riwayat kelas
        if not siswa_terdaftar_di_kelas(
            siswa_id,
            kelas_id,
            tahun_pelajaran.kode
        ):
            flash('Siswa tidak terdaftar di kelas tersebut.', 'danger')
            return redirect_ke_catatan(kelas_id)

        catatan = CatatanPerkembanganSiswa(
            siswa_id=siswa_id,
            kelas_id=kelas_id,
            guru_id=guru.id,
            tahun_pelajaran=tahun_pelajaran.kode,
            tanggal=tanggal_catatan,
            kategori=kategori,
            judul=judul,
            deskripsi=deskripsi,
            tindak_lanjut=tindak_lanjut or None,
            status_tindak_lanjut='belum_ditindaklanjuti'
        )

        db.session.add(catatan)
        db.session.commit()

        flash('Catatan perkembangan siswa berhasil disimpan.', 'success')

    except ValueError:
        db.session.rollback()
        flash('Format tanggal tidak valid.', 'warning')

    except Exception:
        db.session.rollback()
        flash('Terjadi kesalahan saat menyimpan catatan.', 'danger')

    return redirect_ke_catatan(
        request.form.get('kelas_id', type=int)
    )


# =========================================================
# EDIT CATATAN
# =========================================================

@catatan_perkembangan_bp.route(
    '/catatan-perkembangan/<int:catatan_id>/edit',
    methods=['POST']
)
def edit(catatan_id):

    context = get_wali_context()

    if not context:
        return redirect(url_for('login.halaman_login'))

    guru = context['guru']
    tahun_pelajaran = context['tahun_pelajaran']
    daftar_kelas = context['daftar_kelas']

    if not tahun_pelajaran:
        return redirect_ke_catatan()

    kelas_ids = [kelas.id for kelas in daftar_kelas]

    catatan = ambil_catatan_milik_guru(
        catatan_id,
        guru.id,
        tahun_pelajaran.kode,
        kelas_ids
    )

    if not catatan:
        return "Catatan tidak ditemukan atau Anda tidak memiliki akses.", 403

    try:
        siswa_id = request.form.get('siswa_id', type=int)
        kelas_id = request.form.get('kelas_id', type=int)

        tanggal_input = request.form.get('tanggal', '').strip()
        kategori = request.form.get('kategori', '').strip()
        judul = request.form.get('judul', '').strip()
        deskripsi = request.form.get('deskripsi', '').strip()
        tindak_lanjut = request.form.get('tindak_lanjut', '').strip()
        status = request.form.get('status_tindak_lanjut', '').strip()

        if kelas_id not in kelas_ids:
            flash('Kelas tidak valid.', 'danger')
            return redirect_ke_catatan(catatan.kelas_id)

        if kategori not in KATEGORI_CATATAN:
            flash('Kategori tidak valid.', 'warning')
            return redirect_ke_catatan(catatan.kelas_id)

        if status not in STATUS_TINDAK_LANJUT:
            flash('Status tindak lanjut tidak valid.', 'warning')
            return redirect_ke_catatan(catatan.kelas_id)

        if not siswa_id or not judul or not deskripsi or not tanggal_input:
            flash('Lengkapi seluruh data wajib.', 'warning')
            return redirect_ke_catatan(catatan.kelas_id)

        tanggal_catatan = date.fromisoformat(tanggal_input)

        if not siswa_terdaftar_di_kelas(
            siswa_id,
            kelas_id,
            tahun_pelajaran.kode
        ):
            flash('Siswa tidak terdaftar di kelas tersebut.', 'danger')
            return redirect_ke_catatan(catatan.kelas_id)

        catatan.siswa_id = siswa_id
        catatan.kelas_id = kelas_id
        catatan.tanggal = tanggal_catatan
        catatan.kategori = kategori
        catatan.judul = judul
        catatan.deskripsi = deskripsi
        catatan.tindak_lanjut = tindak_lanjut or None
        catatan.status_tindak_lanjut = status

        db.session.commit()

        flash('Catatan perkembangan berhasil diperbarui.', 'success')

    except ValueError:
        db.session.rollback()
        flash('Format tanggal tidak valid.', 'warning')

    except Exception:
        db.session.rollback()
        flash('Terjadi kesalahan saat memperbarui catatan.', 'danger')

    return redirect_ke_catatan(catatan.kelas_id)


# =========================================================
# HAPUS CATATAN
# =========================================================

@catatan_perkembangan_bp.route(
    '/catatan-perkembangan/<int:catatan_id>/hapus',
    methods=['POST']
)
def hapus(catatan_id):

    context = get_wali_context()

    if not context:
        return redirect(url_for('login.halaman_login'))

    guru = context['guru']
    tahun_pelajaran = context['tahun_pelajaran']
    daftar_kelas = context['daftar_kelas']

    if not tahun_pelajaran:
        return redirect_ke_catatan()

    kelas_ids = [kelas.id for kelas in daftar_kelas]

    catatan = ambil_catatan_milik_guru(
        catatan_id,
        guru.id,
        tahun_pelajaran.kode,
        kelas_ids
    )

    if not catatan:
        return "Catatan tidak ditemukan atau Anda tidak memiliki akses.", 403

    kelas_id = catatan.kelas_id

    try:
        db.session.delete(catatan)
        db.session.commit()

        flash('Catatan perkembangan berhasil dihapus.', 'success')

    except Exception:
        db.session.rollback()
        flash('Terjadi kesalahan saat menghapus catatan.', 'danger')

    return redirect_ke_catatan(kelas_id)
