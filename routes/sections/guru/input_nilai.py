
from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    flash,
    request
)

from datetime import date
from decimal import Decimal, InvalidOperation

from models import (
    db,
    User,
    Guru,
    TahunPelajaran,
    PengaturanMapelKelas,
    MataPelajaran,
    RiwayatKelas,
    Siswa,
    Penilaian,
    NilaiSiswa,
    JurnalMengajar
)

from sqlalchemy.orm import joinedload


input_nilai_guru_bp = Blueprint(
    'input_nilai_guru',
    __name__,
    url_prefix='/nilai'
)


def get_guru_penilaian_context():
    """
    Mengambil akun guru yang sedang login dan tahun pelajaran aktif.
    Penugasan mapel dibatasi berdasarkan guru_id dan tahun pelajaran.
    """

    if not session.get('logged_in'):
        return None, None, None, redirect(url_for('login.halaman_login'))

    if session.get('sistem_mode') != 'sekolah':
        flash('Akses hanya tersedia pada sistem sekolah.', 'warning')
        return None, None, None, redirect(url_for('login.halaman_login'))

    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None

    if not user:
        session.clear()
        flash('Sesi pengguna tidak ditemukan. Silakan login kembali.', 'warning')
        return None, None, None, redirect(url_for('login.halaman_login'))

    if not user.guru_id:
        flash('Akun ini belum terhubung dengan data Guru.', 'warning')
        return user, None, None, redirect(url_for('dashboard.index'))

    guru = Guru.query.get(user.guru_id)

    if not guru:
        flash('Data guru tidak ditemukan.', 'warning')
        return user, None, None, redirect(url_for('dashboard.index'))

    tahun_aktif = TahunPelajaran.query.filter_by(
        aktif=True
    ).first()

    if not tahun_aktif:
        flash('Belum ada tahun pelajaran yang diaktifkan.', 'warning')
        return user, guru, None, None

    return user, guru, tahun_aktif, None


@input_nilai_guru_bp.route('/guru', methods=['GET'])
def index():

    user, guru, tahun_aktif, response = get_guru_penilaian_context()

    if response:
        return response

    if not tahun_aktif:
        return render_template(
            'sections/guru/input_nilai.html',
            user=user,
            guru=guru,
            tahun_aktif=None,
            daftar_penugasan=[],
            total_kelas=0,
            total_mapel=0,
            active_page='nilai_guru',
            halaman_aktif='guru'
        )

    daftar_penugasan = (
        PengaturanMapelKelas.query
        .join(
            MataPelajaran,
            PengaturanMapelKelas.mata_pelajaran_id == MataPelajaran.id
        )
        .options(
            joinedload(PengaturanMapelKelas.kelas),
            joinedload(PengaturanMapelKelas.mata_pelajaran)
        )
        .filter(
            PengaturanMapelKelas.guru_id == guru.id,
            PengaturanMapelKelas.tahun_pelajaran == tahun_aktif.kode
        )
        .order_by(
            PengaturanMapelKelas.kelas_id,
            MataPelajaran.nama_pelajaran
        )
        .all()
    )

    total_kelas = len({
        item.kelas_id for item in daftar_penugasan
    })

    total_mapel = len({
        item.mata_pelajaran_id for item in daftar_penugasan
    })

    return render_template(
        'sections/guru/input_nilai.html',
        user=user,
        guru=guru,
        tahun_aktif=tahun_aktif,
        daftar_penugasan=daftar_penugasan,
        total_kelas=total_kelas,
        total_mapel=total_mapel,
        active_page='nilai_guru',
        halaman_aktif='guru'
    )

@input_nilai_guru_bp.route(
    '/guru/penugasan/<int:penugasan_id>',
    methods=['GET']
)
def detail_penugasan(penugasan_id):
    user, guru, tahun_aktif, response = get_guru_penilaian_context()

    if response:
        return response

    if not tahun_aktif:
        flash('Tahun pelajaran belum aktif.', 'warning')
        return redirect(url_for('input_nilai_guru.index'))

    # Pastikan penugasan benar-benar milik guru yang login
    penugasan = (
        PengaturanMapelKelas.query
        .options(
            joinedload(PengaturanMapelKelas.kelas),
            joinedload(PengaturanMapelKelas.mata_pelajaran)
        )
        .filter(
            PengaturanMapelKelas.id == penugasan_id,
            PengaturanMapelKelas.guru_id == guru.id,
            PengaturanMapelKelas.tahun_pelajaran == tahun_aktif.kode
        )
        .first()
    )

    if not penugasan:
        flash(
            'Penugasan tidak ditemukan atau bukan hak akses Anda.',
            'danger'
        )
        return redirect(url_for('input_nilai_guru.index'))

    # Ambil jumlah siswa yang terdaftar pada kelas dan semester ini
    total_siswa = (
        db.session.query(RiwayatKelas.siswa_id)
        .join(
            Siswa,
            Siswa.id == RiwayatKelas.siswa_id
        )
        .filter(
            RiwayatKelas.kelas_id == penugasan.kelas_id,
            RiwayatKelas.tahun_pelajaran == tahun_aktif.kode
        )
        .distinct()
        .count()
    )

    # Ambil komponen penilaian yang sudah dibuat untuk penugasan ini
    daftar_penilaian = (
        Penilaian.query
        .filter(
            Penilaian.pengaturan_mapel_kelas_id == penugasan.id,
            Penilaian.guru_id == guru.id,
            Penilaian.tahun_pelajaran == tahun_aktif.kode
        )
        .order_by(
            Penilaian.tanggal.desc(),
            Penilaian.id.desc()
        )
        .all()
    )

    # Ambil seluruh jurnal untuk penugasan ini berdasarkan urutan tanggal
    daftar_jurnal = (
        JurnalMengajar.query
        .filter(
            JurnalMengajar.guru_id == guru.id,
            JurnalMengajar.mata_pelajaran_id == penugasan.mata_pelajaran_id,
            JurnalMengajar.kelas_id == penugasan.kelas_id,
            JurnalMengajar.tahun_pelajaran == tahun_aktif.kode
        )
        .order_by(
            JurnalMengajar.tanggal.asc(),
            JurnalMengajar.jam_mulai.asc(),
            JurnalMengajar.id.asc()
        )
        .all()
    )

    # Pemetaan nomor pertemuan berdasarkan urutan jurnal
    nomor_pertemuan_map = {
        jurnal.id: nomor
        for nomor, jurnal in enumerate(daftar_jurnal, start=1)
    }

    return render_template(
        'sections/guru/detail_penugasan_nilai.html',

        # Data pengguna dan guru
        user=user,
        guru=guru,

        # Data akademik
        tahun_aktif=tahun_aktif,
        penugasan=penugasan,
        total_siswa=total_siswa,
        daftar_penilaian=daftar_penilaian,
        nomor_pertemuan_map=nomor_pertemuan_map,

        # Navigasi
        active_page='nilai_guru',
        halaman_aktif='guru'
    )


@input_nilai_guru_bp.route(
    '/guru/penugasan/<int:penugasan_id>/tambah',
    methods=['GET', 'POST']
)
def tambah_penilaian(penugasan_id):

    user, guru, tahun_aktif, response = get_guru_penilaian_context()

    if response:
        return response

    if not tahun_aktif:
        flash('Tahun pelajaran belum aktif.', 'warning')
        return redirect(url_for('input_nilai_guru.index'))

    # Validasi kepemilikan penugasan
    penugasan = (
        PengaturanMapelKelas.query
        .options(
            joinedload(PengaturanMapelKelas.kelas),
            joinedload(PengaturanMapelKelas.mata_pelajaran)
        )
        .filter(
            PengaturanMapelKelas.id == penugasan_id,
            PengaturanMapelKelas.guru_id == guru.id,
            PengaturanMapelKelas.tahun_pelajaran == tahun_aktif.kode
        )
        .first()
    )

    if not penugasan:
        flash('Penugasan tidak ditemukan atau bukan hak akses Anda.', 'danger')
        return redirect(url_for('input_nilai_guru.index'))

    jenis_valid = {
        'formatif': 'Kuis / Ulangan Harian',
        'praktik': 'Praktik',
        'proyek': 'Proyek',
        'pts': 'PTS',
        'pas': 'PAS',
        'sumatif': 'Sumatif'
    }

    if request.method == 'POST':

        jenis = request.form.get('jenis', '').strip()
        judul = request.form.get('judul', '').strip()
        deskripsi = request.form.get('deskripsi', '').strip()
        tanggal_input = request.form.get('tanggal', '').strip()
        nilai_maksimal_input = request.form.get('nilai_maksimal', '').strip()
        bobot_input = request.form.get('bobot', '').strip()

        try:
            if jenis not in jenis_valid:
                raise ValueError('Jenis penilaian tidak valid.')

            if not judul:
                raise ValueError('Judul penilaian wajib diisi.')

            if len(judul) > 150:
                raise ValueError('Judul maksimal 150 karakter.')

            tanggal_penilaian = date.fromisoformat(tanggal_input)

            nilai_maksimal = Decimal(nilai_maksimal_input)
            bobot = Decimal(bobot_input)

            if not nilai_maksimal.is_finite() or nilai_maksimal <= 0:
                raise ValueError('Nilai maksimal harus lebih besar dari 0.')

            if not bobot.is_finite() or bobot < 0 or bobot > 100:
                raise ValueError('Bobot harus berada antara 0 sampai 100.')

            if len(deskripsi) > 10000:
                raise ValueError('Deskripsi terlalu panjang.')

            penilaian = Penilaian(
                pengaturan_mapel_kelas_id=penugasan.id,
                guru_id=guru.id,
                tahun_pelajaran=tahun_aktif.kode,
                jenis=jenis,
                judul=judul,
                deskripsi=deskripsi or None,
                tanggal=tanggal_penilaian,
                nilai_maksimal=nilai_maksimal,
                bobot=bobot,
                status='draft'
            )

            db.session.add(penilaian)
            db.session.commit()

            flash('Komponen penilaian berhasil dibuat.', 'success')

            return redirect(
                url_for(
                    'input_nilai_guru.detail_penugasan',
                    penugasan_id=penugasan.id
                )
            )

        except (ValueError, InvalidOperation):
            db.session.rollback()
            flash(
                'Periksa kembali jenis, tanggal, nilai maksimal, dan bobot penilaian.',
                'danger'
            )

        except Exception:
            db.session.rollback()
            flash('Terjadi kesalahan saat menyimpan penilaian.', 'danger')

    return render_template(
        'sections/guru/tambah_penilaian.html',
        user=user,
        guru=guru,
        tahun_aktif=tahun_aktif,
        penugasan=penugasan,
        jenis_valid=jenis_valid,
        tanggal_default=date.today().isoformat(),
        active_page='nilai_guru',
        halaman_aktif='guru'
    )


@input_nilai_guru_bp.route(
    '/guru/penilaian/<int:penilaian_id>',
    methods=['GET', 'POST']
)
def input_nilai_siswa(penilaian_id):

    user, guru, tahun_aktif, response = get_guru_penilaian_context()

    if response:
        return response

    if not tahun_aktif:
        flash('Tahun pelajaran belum aktif.', 'warning')
        return redirect(url_for('input_nilai_guru.index'))

    # Ambil penilaian sekaligus periksa kepemilikan guru
    penilaian = (
        Penilaian.query
        .options(
            joinedload(Penilaian.pengaturan_mapel_kelas)
            .joinedload(PengaturanMapelKelas.kelas),

            joinedload(Penilaian.pengaturan_mapel_kelas)
            .joinedload(PengaturanMapelKelas.mata_pelajaran)
        )
        .filter(
            Penilaian.id == penilaian_id,
            Penilaian.guru_id == guru.id,
            Penilaian.tahun_pelajaran == tahun_aktif.kode
        )
        .first()
    )

    if not penilaian:
        flash(
            'Penilaian tidak ditemukan atau bukan hak akses Anda.',
            'danger'
        )
        return redirect(url_for('input_nilai_guru.index'))

    penugasan = penilaian.pengaturan_mapel_kelas

    if not penugasan or str(penugasan.guru_id) != str(guru.id):
        flash('Penugasan penilaian tidak valid.', 'danger')
        return redirect(url_for('input_nilai_guru.index'))

    # Ambil siswa berdasarkan riwayat kelas semester aktif
    daftar_siswa = (
        db.session.query(Siswa)
        .join(
            RiwayatKelas,
            RiwayatKelas.siswa_id == Siswa.id
        )
        .filter(
            RiwayatKelas.kelas_id == penugasan.kelas_id,
            RiwayatKelas.tahun_pelajaran == tahun_aktif.kode
        )
        .order_by(Siswa.nama.asc())
        .all()
    )

    daftar_nilai = (
        NilaiSiswa.query
        .filter_by(penilaian_id=penilaian.id)
        .all()
    )

    nilai_map = {
        item.siswa_id: item
        for item in daftar_nilai
    }

    # Simpan nilai
    if request.method == 'POST':

        if penilaian.status == 'ditutup':
            flash('Penilaian ini sudah ditutup dan tidak dapat diubah.', 'warning')
            return redirect(
                url_for(
                    'input_nilai_guru.input_nilai_siswa',
                    penilaian_id=penilaian.id
                )
            )

        try:
            data_nilai = []

            for siswa in daftar_siswa:

                nilai_input = request.form.get(
                    f'nilai_{siswa.id}', ''
                ).strip()

                if nilai_input == '':
                    data_nilai.append((siswa.id, None))
                    continue

                nilai = Decimal(nilai_input)

                if not nilai.is_finite():
                    raise ValueError('Nilai harus berupa angka yang valid.')

                if nilai < 0:
                    raise ValueError('Nilai tidak boleh kurang dari 0.')

                if nilai > Decimal(str(penilaian.nilai_maksimal)):
                    raise ValueError(
                        f'Nilai siswa tidak boleh melebihi '
                        f'{penilaian.nilai_maksimal}.'
                    )

                data_nilai.append((siswa.id, nilai))

            # Semua nilai sudah tervalidasi, baru lakukan penyimpanan
            for siswa_id, nilai in data_nilai:

                record = nilai_map.get(siswa_id)

                if record:
                    record.nilai = nilai
                else:
                    record = NilaiSiswa(
                        penilaian_id=penilaian.id,
                        siswa_id=siswa_id,
                        nilai=nilai
                    )
                    db.session.add(record)

            db.session.commit()

            flash('Nilai siswa berhasil disimpan.', 'success')

            return redirect(
                url_for(
                    'input_nilai_guru.input_nilai_siswa',
                    penilaian_id=penilaian.id
                )
            )

        except (ValueError, InvalidOperation) as e:
            db.session.rollback()
            flash(str(e), 'danger')

        except Exception:
            db.session.rollback()
            flash('Terjadi kesalahan saat menyimpan nilai siswa.', 'danger')

        # Ambil ulang nilai setelah rollback
        daftar_nilai = (
            NilaiSiswa.query
            .filter_by(penilaian_id=penilaian.id)
            .all()
        )

        nilai_map = {
            item.siswa_id: item
            for item in daftar_nilai
        }

    return render_template(
        'sections/guru/input_nilai_siswa.html',
        user=user,
        guru=guru,
        tahun_aktif=tahun_aktif,
        penugasan=penugasan,
        penilaian=penilaian,
        daftar_siswa=daftar_siswa,
        nilai_map=nilai_map,
        active_page='nilai_guru',
        halaman_aktif='guru'
    )
