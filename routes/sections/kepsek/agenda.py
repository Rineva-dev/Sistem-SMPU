from flask import Blueprint, render_template, request, redirect, url_for, session, flash, get_flashed_messages, g  # ✅ Tambah g
from datetime import datetime
from models import db, AgendaKegiatan

agenda_bp = Blueprint(
    'agenda',
    __name__,
    template_folder='../../../templates/sections/kepsek',
    url_prefix='/agenda'
)

# HALAMAN UTAMA - SEMUA ORANG BISA LIHAT
@agenda_bp.route('/')
def daftar_agenda():
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    daftar = AgendaKegiatan.query.order_by(AgendaKegiatan.tanggal_mulai.asc()).all()

    sekarang = datetime.now()
    
    events = []
    daftar_dengan_status = []
    if daftar:
        for a in daftar:
            # ✅ Logika Status Otomatis
            if a.status != "Dibatalkan":
                if a.tanggal_mulai > sekarang:
                    status = "Terjadwal"
                elif a.tanggal_selesai and a.tanggal_selesai < sekarang:
                    status = "Selesai"
                else:
                    status = "Berlangsung"
            else:
                status = "Dibatalkan"

            # Data untuk kalender
            events.append({
                'id': a.id,
                'title': a.judul,
                # ✅ Format tetap: YYYY-MM-DDTHH:MM
                'start': a.tanggal_mulai.strftime('%Y-%m-%dT%H:%M'),
                'end': a.tanggal_selesai.strftime('%Y-%m-%dT%H:%M') if a.tanggal_selesai else a.tanggal_mulai.strftime('%Y-%m-%dT%H:%M'),
                'status': status,
                'lokasi': a.lokasi or '',
                'pj': a.penanggung_jawab or ''
            })

            # ✅ Data lengkap untuk tabel
            daftar_dengan_status.append({
                'id': a.id,
                'judul': a.judul,
                'deskripsi': a.deskripsi,
                'tanggal_mulai': a.tanggal_mulai,
                'tanggal_selesai': a.tanggal_selesai,
                'lokasi': a.lokasi,
                'penanggung_jawab': a.penanggung_jawab,
                'status': status
            })

    # Data untuk sidebar
    user_role = session.get('role', '')
    daftar_tugas = session.get('daftar_tugas', [])
    user = {
        'nama': session.get('user_name', 'Pengguna'),
        'jabatan': user_role,
        'tugas_tambahan': ", ".join(daftar_tugas) if isinstance(daftar_tugas, list) else "",
        'inisial': session.get('user_initials', 'U')
    }

    # Bersihkan pesan lama
    get_flashed_messages(with_categories=True)

    context = {
        'active_page': 'agenda',
        'halaman_aktif': 'utama',
        'role': user_role,
        'user': user,
        'user_name': session.get('user_name', ''),
        'daftar_agenda': daftar_dengan_status,
        'events': events,
        'tahun_pelajaran': g.tahun_pelajaran,  # ✅ Ganti jadi dinamis
        'semester': 'Genap'
    }
    return render_template('agenda.html', **context)


# TAMBAH AGENDA - HANYA UNTUK KEPALA SEKOLAH
@agenda_bp.route('/tambah', methods=['GET', 'POST'])
def tambah_agenda():
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    if session.get('role') != 'Kepala Sekolah':
        flash('Anda tidak memiliki hak akses untuk menambah agenda', 'warning')
        return redirect(url_for('agenda.daftar_agenda'))

    if request.method == 'POST':
        tgl_mulai = datetime.strptime(request.form['tanggal_mulai'], '%Y-%m-%dT%H:%M')
        tgl_selesai_str = request.form.get('tanggal_selesai')
        tgl_selesai = datetime.strptime(tgl_selesai_str, '%Y-%m-%dT%H:%M') if tgl_selesai_str else None

        # Tentukan status otomatis saat disimpan
        sekarang = datetime.now()
        if tgl_mulai > sekarang:
            status = "Terjadwal"
        elif tgl_selesai and tgl_selesai < sekarang:
            status = "Selesai"
        else:
            status = "Berlangsung"

        baru = AgendaKegiatan(
            judul = request.form['judul'].strip(),
            deskripsi = request.form['deskripsi'].strip(),
            tanggal_mulai = tgl_mulai,
            tanggal_selesai = tgl_selesai,
            lokasi = request.form['lokasi'].strip(),
            penanggung_jawab = request.form['penanggung_jawab'].strip(),
            status = status,
            dibuat_oleh = session.get('user_name'),
            tahun_pelajaran = g.tahun_pelajaran  # ✅ Simpan tahun pelajaran otomatis
        )
        db.session.add(baru)
        db.session.commit()
        flash('Agenda berhasil ditambahkan', 'success')
        return redirect(url_for('agenda.daftar_agenda'))

    context = {
        'active_page': 'agenda',
        'halaman_aktif': 'utama',
        'role': session.get('role'),
        'user': {
            'nama': session.get('user_name'),
            'jabatan': session.get('role'),
            'inisial': session.get('user_initials', 'KS')
        },
        'tahun_pelajaran': g.tahun_pelajaran
    }
    return render_template('agenda_tambah.html', **context)


# EDIT AGENDA - HANYA UNTUK KEPALA SEKOLAH
@agenda_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_agenda(id):
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    if session.get('role') != 'Kepala Sekolah':
        flash('Anda tidak memiliki hak akses untuk mengedit agenda', 'warning')
        return redirect(url_for('agenda.daftar_agenda'))

    kegiatan = AgendaKegiatan.query.get_or_404(id)

    if request.method == 'POST':
        tgl_mulai = datetime.strptime(request.form['tanggal_mulai'], '%Y-%m-%dT%H:%M')
        tgl_selesai_str = request.form.get('tanggal_selesai')
        tgl_selesai = datetime.strptime(tgl_selesai_str, '%Y-%m-%dT%H:%M') if tgl_selesai_str else None

        # Status otomatis kecuali jika dibatalkan
        if request.form.get('status') == "Dibatalkan":
            status = "Dibatalkan"
        else:
            sekarang = datetime.now()
            if tgl_mulai > sekarang:
                status = "Terjadwal"
            elif tgl_selesai and tgl_selesai < sekarang:
                status = "Selesai"
            else:
                status = "Berlangsung"

        kegiatan.judul = request.form['judul'].strip()
        kegiatan.deskripsi = request.form['deskripsi'].strip()
        kegiatan.tanggal_mulai = tgl_mulai
        kegiatan.tanggal_selesai = tgl_selesai
        kegiatan.lokasi = request.form['lokasi'].strip()
        kegiatan.penanggung_jawab = request.form['penanggung_jawab'].strip()
        kegiatan.status = status
        kegiatan.tahun_pelajaran = g.tahun_pelajaran  # ✅ Update tahun jika perlu

        db.session.commit()
        flash('Agenda berhasil diperbarui', 'success')
        return redirect(url_for('agenda.daftar_agenda'))

    context = {
        'kegiatan': kegiatan,
        'active_page': 'agenda',
        'halaman_aktif': 'utama',
        'role': session.get('role'),
        'user': {
            'nama': session.get('user_name'),
            'jabatan': session.get('role'),
            'inisial': session.get('user_initials', 'KS')
        },
        'tahun_pelajaran': g.tahun_pelajaran
    }
    return render_template('agenda_edit.html', **context)


# HAPUS AGENDA - HANYA UNTUK KEPALA SEKOLAH
@agenda_bp.route('/hapus/<int:id>')
def hapus_agenda(id):
    if not session.get('logged_in'):
        return redirect(url_for('login.halaman_login'))

    if session.get('role') != 'Kepala Sekolah':
        flash('Anda tidak memiliki hak akses untuk menghapus agenda', 'warning')
        return redirect(url_for('agenda.daftar_agenda'))

    kegiatan = AgendaKegiatan.query.get_or_404(id)
    db.session.delete(kegiatan)
    db.session.commit()
    flash('Agenda berhasil dihapus', 'info')
    return redirect(url_for('agenda.daftar_agenda'))