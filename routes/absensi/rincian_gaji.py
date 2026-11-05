from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal

from models import Guru, GajiGuru, DetailGajiGuru
import secrets
import string


rincian_gaji_bp = Blueprint(
    'rincian_gaji',
    __name__
)


BULAN_LIST = [
    '', 'Januari', 'Februari', 'Maret', 'April',
    'Mei', 'Juni', 'Juli', 'Agustus',
    'September', 'Oktober', 'November', 'Desember'
]

def buat_kode_verifikasi(bulan, tahun):
    karakter = string.ascii_uppercase + string.digits
    kode_unik = ''.join(
        secrets.choice(karakter) for _ in range(6)
    )

    return f"SLP-{tahun}{bulan:02d}-{kode_unik}"

@rincian_gaji_bp.route('/rincian-gaji')
def halaman_rincian_gaji():

    # Validasi login guru
    if not (
        session.get('absensi_logged_in') is True
        and session.get('absensi_sistem_mode') == 'absensi'
        and session.get('absensi_user_id')
    ):
        flash('Silakan login terlebih dahulu.', 'absensi_warning')
        return redirect(url_for('absensi.login_absensi'))

    guru = Guru.query.filter_by(
        id=session.get('absensi_guru_id')
    ).first()

    if not guru:
        flash('Akun ini tidak memiliki akses.', 'absensi_danger')
        return redirect(url_for('absensi.login_absensi'))

    hari_ini = datetime.now(
        ZoneInfo('Asia/Makassar')
    ).date()

    # Ambil hanya slip yang sudah diterbitkan untuk guru login
    daftar_gaji_db = GajiGuru.query.filter_by(
        guru_id=guru.id,
        status_penerbitan='terbit'
    ).order_by(
        GajiGuru.tahun.desc(),
        GajiGuru.bulan.desc()
    ).all()

    # Daftar periode yang benar-benar sudah diterbitkan
    periode_tersedia = [
        {
            'bulan': item.bulan,
            'tahun': item.tahun,
            'nama_bulan': BULAN_LIST[item.bulan]
        }
        for item in daftar_gaji_db
        if 1 <= item.bulan <= 12
    ]

    rincian = None
    filter_bulan = None
    filter_tahun = None
    nama_bulan = None

    if periode_tersedia:

        # Default ke periode terbit terbaru
        periode_terbaru = periode_tersedia[0]

        filter_tahun = request.args.get(
            'tahun', type=int
        ) or periode_terbaru['tahun']

        # Pilihan bulan hanya dari periode terbit pada tahun terpilih
        bulan_tersedia = [
            item['bulan']
            for item in periode_tersedia
            if item['tahun'] == filter_tahun
        ]

        # Jika tahun tidak memiliki slip, kembali ke tahun terbaru
        if not bulan_tersedia:
            filter_tahun = periode_terbaru['tahun']
            bulan_tersedia = [
                item['bulan']
                for item in periode_tersedia
                if item['tahun'] == filter_tahun
            ]

        filter_bulan = request.args.get(
            'bulan', type=int
        )

        if filter_bulan not in bulan_tersedia:
            filter_bulan = bulan_tersedia[0]

        nama_bulan = BULAN_LIST[filter_bulan]

        # Ambil slip sesuai guru, bulan, tahun, dan status terbit
        gaji_data = GajiGuru.query.filter_by(
            guru_id=guru.id,
            bulan=filter_bulan,
            tahun=filter_tahun,
            status_penerbitan='terbit'
        ).first()

        if gaji_data:

            # Ambil komponen dinamis dari DetailGajiGuru
            detail_db = DetailGajiGuru.query.filter_by(
                gaji_id=gaji_data.id
            ).order_by(
                DetailGajiGuru.urutan.asc(),
                DetailGajiGuru.id.asc()
            ).all()

            penerimaan = []
            potongan = []

            for detail in detail_db:
                komponen = {
                    'nama': detail.nama_item,
                    'nominal': Decimal(str(detail.nominal or 0))
                }

                if detail.jenis == 'penerimaan':
                    penerimaan.append(komponen)

                elif detail.jenis == 'potongan':
                    potongan.append(komponen)

            total_penerimaan = sum(
                (item['nominal'] for item in penerimaan),
                Decimal('0')
            )

            total_potongan = sum(
                (item['nominal'] for item in potongan),
                Decimal('0')
            )

            gaji_bersih = total_penerimaan - total_potongan

            rincian = {
                'nama': guru.nama,
                'nip': guru.nip,
                'jabatan': guru.jabatan,
                'penerimaan': penerimaan,
                'potongan': potongan,
                'total_penerimaan': float(total_penerimaan),
                'total_potongan': float(total_potongan),
                'gaji_bersih': float(gaji_bersih),
                'kode_verifikasi': gaji_data.kode_verifikasi or '-'
            }

    # Daftar tahun yang benar-benar memiliki slip terbit
    tahun_tersedia = sorted(
        {item['tahun'] for item in periode_tersedia},
        reverse=True
    )

    # Daftar bulan untuk tahun yang sedang dipilih
    bulan_tersedia = [
        item for item in periode_tersedia
        if item['tahun'] == filter_tahun
    ]

    return render_template(
        'sections/absensi/rincian_gaji.html',
        user=guru,
        guru=guru,
        rincian=rincian,
        nama_bulan=nama_bulan,
        tahun=filter_tahun,
        filter_bulan=filter_bulan,
        filter_tahun=filter_tahun,
        tahun_tersedia=tahun_tersedia,
        bulan_tersedia=bulan_tersedia,
        hari_ini=hari_ini.strftime('%d-%m-%Y'),
        tanggal_cetak=hari_ini.strftime('%d-%m-%Y'),
        halaman_aktif='absensi',
        active_page='rincian_gaji'
    )