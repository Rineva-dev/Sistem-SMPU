from flask import (
    Blueprint, render_template, request, jsonify,
    abort, redirect, url_for, flash, current_app
)

from models import (
    db,
    Siswa,
    TagihanSiswa,
    JenisPembayaran,
    RiwayatPembayaran,
    PengajuanPembayaran,
    DetailPengajuanPembayaran,
)

from datetime import date, datetime
import re
import secrets
import os
from werkzeug.utils import secure_filename

payment_public_bp = Blueprint(
    "payment_public",
    __name__,
    url_prefix="/payment-public"
)


# Urutan bulan kalender
URUTAN_BULAN = {
    "januari": 1,
    "februari": 2,
    "maret": 3,
    "april": 4,
    "mei": 5,
    "juni": 6,
    "juli": 7,
    "agustus": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "desember": 12,
}


def informasi_periode(bulan, tahun_pelajaran):
    teks_bulan = str(bulan or "").strip()
    teks_tp = str(tahun_pelajaran or "").strip()

    nama_bulan = teks_bulan.lower()
    tahun_dari_bulan = None

    # Jika periode sudah mengandung tahun, misalnya "Januari 2025"
    for nama in URUTAN_BULAN:
        if nama in nama_bulan:
            nama_bulan = nama
            angka_bulan = URUTAN_BULAN[nama]

            angka_tahun = re.search(
                r"\b(20\d{2})\b",
                teks_bulan
            )

            if angka_tahun:
                tahun_dari_bulan = int(angka_tahun.group(1))

            break
    else:
        angka_bulan = None

    # Ambil tahun dari tahun pelajaran, misalnya 2025/2026
    daftar_tahun = re.findall(r"\b(20\d{2})\b", teks_tp)

    if tahun_dari_bulan:
        tahun_kalender = tahun_dari_bulan

    elif angka_bulan and len(daftar_tahun) >= 2:
        tahun_awal = int(daftar_tahun[0])
        tahun_akhir = int(daftar_tahun[1])

        # Asumsi tahun pelajaran dimulai pada Juli:
        # Januari-Juni masuk tahun kedua.
        # Juli-Desember masuk tahun pertama.
        tahun_kalender = (
            tahun_akhir if angka_bulan <= 6 else tahun_awal
        )

    elif angka_bulan and daftar_tahun:
        tahun_kalender = int(daftar_tahun[0])

    else:
        tahun_kalender = None

    if angka_bulan and tahun_kalender:
        kunci = f"{tahun_kalender:04d}-{angka_bulan:02d}"
        label = f"{nama_bulan.capitalize()} {tahun_kalender}"
        urutan = (tahun_kalender, angka_bulan)

    else:
        # Untuk periode non-bulanan seperti Semester 1
        kunci = f"9999-{teks_tp}-{teks_bulan}"
        label = teks_bulan or "-"
        urutan = (9999, 99)

    return {
        "bulan_urut": angka_bulan or 99,
        "tahun_kalender": tahun_kalender or 9999,
        "kelompok_bulan": kunci,
        "label_periode": label,
        "urutan_periode": urutan,
    }

# Status ini masih mengunci tagihan agar tidak diajukan dua kali.
STATUS_TRANSAKSI_AKTIF = {
    "menunggu_pembayaran",
    "menunggu_verifikasi",
    "diproses",
}


def ambil_transaksi_aktif_tagihan(daftar_tagihan_ids):
    """
    Mengambil transaksi aktif untuk daftar ID tagihan.
    Hasil berbentuk dictionary: {tagihan_id: transaksi}
    """
    if not daftar_tagihan_ids:
        return {}

    hasil = (
        db.session.query(
            DetailPengajuanPembayaran.tagihan_id,
            PengajuanPembayaran,
        )
        .join(
            PengajuanPembayaran,
            DetailPengajuanPembayaran.pengajuan_id
            == PengajuanPembayaran.id,
        )
        .filter(
            DetailPengajuanPembayaran.tagihan_id.in_(
                daftar_tagihan_ids
            ),
            PengajuanPembayaran.status.in_(
                STATUS_TRANSAKSI_AKTIF
            ),
        )
        .order_by(PengajuanPembayaran.diajukan_pada.desc())
        .all()
    )

    transaksi_per_tagihan = {}

    for tagihan_id, transaksi in hasil:
        # Jika ada lebih dari satu transaksi aktif lama,
        # tampilkan transaksi terbaru. Data lama tetap perlu diaudit.
        transaksi_per_tagihan.setdefault(
            tagihan_id,
            transaksi,
        )

    return transaksi_per_tagihan

@payment_public_bp.route("/", methods=["GET", "POST"])
def index():
    # Halaman utama — tidak perlu perubahan besar
    return render_template("payment/index.html")

@payment_public_bp.route("/cari_siswa", methods=["POST"])
def cari_siswa():
    nisn = request.form.get("nisn", "").strip()
    
    if not nisn:
        return jsonify({
            "status": "error",
            "pesan": "Silakan masukkan NISN siswa."
        })
    
    if not nisn.isdigit() or len(nisn) != 10:
        return jsonify({
            "status": "error",
            "pesan": "NISN harus terdiri dari 10 digit angka."
        })
    
    siswa = Siswa.query.filter_by(nisn=nisn).first()
    
    if not siswa:
        return jsonify({
            "status": "not_found",
            "pesan": "NISN tidak terdaftar."
        })
    
    if (siswa.status or "").strip().lower() != "aktif":
        return jsonify({
            "status": "inactive",
            "pesan": "Data siswa ditemukan, tetapi status siswa perlu dikonfirmasi ke pihak sekolah."
        })
    
    nama_kelas = (
        siswa.kelas_sekarang.nama_kelas
        if hasattr(siswa, 'kelas_sekarang') and siswa.kelas_sekarang
        else (siswa.tingkat or "Belum ditentukan")
    )
    
    return jsonify({
        "status": "found",
        "pesan": "Data siswa berhasil ditemukan.",
        "siswa": {
            "nama": siswa.nama or "Nama tidak tersedia",
            "nisn": siswa.nisn,
            "kelas": nama_kelas,
            "tahun_masuk": siswa.tahun_masuk or "-"
        }
    })

@payment_public_bp.route("/detail/<string:nisn>")
def detail_pembayaran(nisn):
    # 1. Validasi NISN dan status siswa
    if not nisn.isdigit() or len(nisn) != 10:
        abort(404)

    siswa = Siswa.query.filter_by(nisn=nisn).first()

    if not siswa or (siswa.status or "").strip().lower() != "aktif":
        abort(404)

    # 2. Ambil tagihan siswa yang sudah tercatat di database
    semua_tagihan = TagihanSiswa.query.filter_by(
        siswa_id=siswa.id
    ).all()

    # Ambil transaksi aktif yang masih mengikat tagihan siswa.
    transaksi_aktif = ambil_transaksi_aktif_tagihan(
        [tagihan.id for tagihan in semua_tagihan]
    )

    daftar_tagihan = []
    daftar_riwayat = []


    for tagihan in semua_tagihan:
        jenis = None

        if tagihan.jenis_pembayaran_id:
            jenis = db.session.get(
                JenisPembayaran,
                tagihan.jenis_pembayaran_id
            )

        nominal = max(0, int(tagihan.nominal_tagihan or 0))
        sudah_dibayar = max(0, int(tagihan.sudah_dibayar or 0))

        # Cegah sisa tagihan bernilai negatif
        sisa = max(0, nominal - sudah_dibayar)

        # Tentukan status berdasarkan nominal dan pembayaran aktual
        if nominal > 0 and sisa == 0:
            status_tampilan = "Lunas"
        elif sudah_dibayar > 0:
            status_tampilan = "Sebagian"
        else:
            status_tampilan = "Belum Dibayar"

        periode = (
            tagihan.bulan
            or (
                f"Semester {tagihan.semester}"
                if tagihan.semester
                else "-"
            )
        )
        
        info_periode = informasi_periode(
            periode,
            tagihan.tahun_pelajaran
        )

        item = {
            "id": tagihan.id,
            "nama": jenis.nama if jenis else "Tagihan Sekolah",
            "periode": periode,
            "tahun_pelajaran": tagihan.tahun_pelajaran or "-",
            "nominal": nominal,
            "sudah_dibayar": min(sudah_dibayar, nominal),
            "sisa": sisa,
            "status": status_tampilan,
            "transaksi_aktif": transaksi_aktif.get(tagihan.id),

            # Data untuk pengurutan dan pengelompokan card
            **info_periode,
        }

        if (
            jenis
            and (jenis.nama or "").strip().lower() == "pembangunan"
        ):
            item["kelompok_bulan"] = "pembangunan"
            item["label_periode"] = "Pembangunan"

        daftar_tagihan.append(item)

        # 3. Ambil riwayat pembayaran untuk setiap tagihan
        riwayat = RiwayatPembayaran.query.filter_by(
            tagihan_id=tagihan.id
        ).all()

        for bayar in riwayat:
            daftar_riwayat.append({
                "nama": item["nama"],
                "periode": periode,
                "jumlah": int(bayar.jumlah_bayar or 0),
                "tanggal": bayar.tanggal_bayar,
                "metode": bayar.metode or "-",
                "keterangan": bayar.keterangan or "",
            })

    # 4. Urutkan tagihan dan riwayat
    daftar_tagihan.sort(
        key=lambda x: (
            0 if x["kelompok_bulan"] == "pembangunan" else 1,
            x["tahun_kalender"],
            x["bulan_urut"],
            x["id"]
        )
    )


    daftar_riwayat.sort(
        key=lambda x: x["tanggal"] or date.min,
        reverse=True
    )

    # 5. Hitung ringkasan keuangan
    total_tagihan = sum(x["nominal"] for x in daftar_tagihan)
    total_dibayar = sum(x["sudah_dibayar"] for x in daftar_tagihan)
    total_sisa = sum(x["sisa"] for x in daftar_tagihan)

    progres = (
        round(total_dibayar / total_tagihan * 100)
        if total_tagihan > 0
        else 0
    )

    # Informasi tingkat dan rombel siswa
    rombel = (
        (siswa.kelas_sekarang.nama_kelas or "").strip()
        if siswa.kelas_sekarang
        else ""
    )

    tingkat = str(siswa.tingkat or "").strip()

    if tingkat and rombel:
        kelas = f"Kelas {tingkat} · {rombel}"
    elif rombel:
        kelas = rombel
    elif tingkat:
        kelas = f"Kelas {tingkat}"
    else:
        kelas = "Belum ditentukan"

    return render_template(
        "payment/detail.html",
        siswa=siswa,
        kelas=kelas,
        daftar_tagihan=daftar_tagihan,
        daftar_riwayat=daftar_riwayat,
        tagihan_belum_lunas=[
            x for x in daftar_tagihan if x["sisa"] > 0
        ],
        total_tagihan=total_tagihan,
        total_dibayar=total_dibayar,
        total_sisa=total_sisa,
        progres=progres,
        tahun_sekarang=date.today().year,
    )


@payment_public_bp.route(
    "/proses-pembayaran/<string:nisn>",
    methods=["GET", "POST"],
    endpoint="proses_pembayaran",
)
def proses_pembayaran(nisn):
    # 1. Validasi NISN
    if not nisn.isdigit() or len(nisn) != 10:
        flash("NISN tidak valid.", "error")
        return redirect(url_for("payment_public.index"))

    siswa = Siswa.query.filter_by(nisn=nisn).first()

    if not siswa or (siswa.status or "").strip().lower() != "aktif":
        flash("Data siswa tidak ditemukan atau tidak aktif.", "error")
        return redirect(url_for("payment_public.index"))

    # =====================================================
    # POST: SIMPAN PENGAJUAN PEMBAYARAN
    # =====================================================
    if request.method == "POST":
        metode = request.form.get("metode", "").strip()
        tagihan_ids_raw = request.form.getlist("tagihan_ids")

        metode_diizinkan = {
            "VA",
            "QRIS",
            "Transfer Bank",
        }

        if metode not in metode_diizinkan:
            flash("Silakan pilih metode pembayaran yang tersedia.", "error")
            return redirect(
                url_for(
                    "payment_public.proses_pembayaran",
                    nisn=nisn,
                )
            )

        try:
            tagihan_ids = list({
                int(item)
                for item in tagihan_ids_raw
                if item.isdigit()
            })
        except (TypeError, ValueError):
            tagihan_ids = []

        if not tagihan_ids:
            flash("Pilih setidaknya satu tagihan.", "error")
            return redirect(
                url_for(
                    "payment_public.proses_pembayaran",
                    nisn=nisn,
                )
            )

        try:
            # Mengunci baris tagihan saat transaksi diproses.
            # Mendukung PostgreSQL dan tidak menggunakan SQL khusus SQLite.
            tagihan_dipilih = (
                TagihanSiswa.query
                .filter(
                    TagihanSiswa.siswa_id == siswa.id,
                    TagihanSiswa.id.in_(tagihan_ids),
                )
                .with_for_update()
                .all()
            )

            if len(tagihan_dipilih) != len(tagihan_ids):
                db.session.rollback()
                flash(
                    "Sebagian tagihan tidak ditemukan atau bukan milik siswa ini.",
                    "error",
                )
                return redirect(
                    url_for(
                        "payment_public.proses_pembayaran",
                        nisn=nisn,
                    )
                )

            # Periksa ulang di server. Jangan hanya mengandalkan
            # checkbox yang disembunyikan di browser.
            transaksi_aktif = ambil_transaksi_aktif_tagihan(
                tagihan_ids
            )

            if transaksi_aktif:
                db.session.rollback()
                flash(
                    "Ada tagihan yang masih terikat transaksi aktif. "
                    "Periksa riwayat transaksi sebelum mencoba lagi.",
                    "warning",
                )
                return redirect(
                    url_for(
                        "payment_public.riwayat_transaksi",
                        nisn=nisn,
                    )
                )

            rincian = []
            total = 0

            for tagihan in tagihan_dipilih:
                nominal = max(
                    0,
                    int(tagihan.nominal_tagihan or 0),
                )
                sudah_dibayar = max(
                    0,
                    int(tagihan.sudah_dibayar or 0),
                )
                sisa = max(0, nominal - sudah_dibayar)

                if sisa <= 0:
                    continue

                rincian.append((tagihan, sisa))
                total += sisa

            if not rincian or total <= 0:
                db.session.rollback()
                flash("Tidak ada sisa tagihan yang dapat diajukan.", "warning")
                return redirect(
                    url_for(
                        "payment_public.detail_pembayaran",
                        nisn=nisn,
                    )
                )

            kode_transaksi = (
                "SMPU-"
                + datetime.now().strftime("%Y%m%d%H%M%S")
                + "-"
                + secrets.token_hex(3).upper()
            )

            pengajuan = PengajuanPembayaran(
                kode_transaksi=kode_transaksi,
                siswa_id=siswa.id,
                metode=metode,
                total_diajukan=total,
                status="menunggu_verifikasi",
                catatan_orangtua=(
                    "SIMULASI: metode VA/QRIS belum terhubung "
                    "ke payment gateway."
                    if metode in {"VA", "QRIS"}
                    else None
                ),
            )

            db.session.add(pengajuan)
            db.session.flush()

            for tagihan, nominal_dibayar in rincian:
                db.session.add(
                    DetailPengajuanPembayaran(
                        pengajuan_id=pengajuan.id,
                        tagihan_id=tagihan.id,
                        nominal_dibayar=nominal_dibayar,
                    )
                )

            db.session.commit()

            flash(
                f"Pengajuan {kode_transaksi} berhasil disimpan. "
                "Status: Menunggu Verifikasi.",
                "success",
            )

            return redirect(
                url_for(
                    "payment_public.detail_transaksi",
                    nisn=nisn,
                    kode_transaksi=kode_transaksi,
                )
            )

        except Exception:
            db.session.rollback()
            # Detail error dicatat di log server, bukan ditampilkan
            # kepada orang tua.
            import logging
            logging.exception("Gagal menyimpan pengajuan pembayaran")

            flash(
                "Pengajuan belum berhasil disimpan. Silakan coba kembali.",
                "error",
            )
            return redirect(
                url_for(
                    "payment_public.proses_pembayaran",
                    nisn=nisn,
                )
            )

    # =====================================================
    # GET: TAMPILKAN TAGIHAN YANG BELUM TERIKAT TRANSAKSI
    # =====================================================
    semua_tagihan = TagihanSiswa.query.filter_by(
        siswa_id=siswa.id
    ).all()

    transaksi_aktif = ambil_transaksi_aktif_tagihan(
        [t.id for t in semua_tagihan]
    )

    daftar_tagihan = []
    grup_dict = {}

    for tagihan in semua_tagihan:
        jenis = (
            db.session.get(
                JenisPembayaran,
                tagihan.jenis_pembayaran_id,
            )
            if tagihan.jenis_pembayaran_id
            else None
        )

        nominal = max(0, int(tagihan.nominal_tagihan or 0))
        sudah_dibayar = max(0, int(tagihan.sudah_dibayar or 0))
        sisa = max(0, nominal - sudah_dibayar)

        if sisa <= 0:
            continue

        periode = (
            tagihan.bulan
            or (
                f"Semester {tagihan.semester}"
                if tagihan.semester
                else "Tagihan Sekolah"
            )
        )

        info = informasi_periode(
            periode,
            tagihan.tahun_pelajaran,
        )

        transaksi = transaksi_aktif.get(tagihan.id)

        item = {
            "id": tagihan.id,
            "nama": jenis.nama if jenis else "Tagihan Sekolah",
            "bulan": periode,
            "tahun_pelajaran": tagihan.tahun_pelajaran or "-",
            "nominal_tagihan": nominal,
            "sudah_dibayar": min(sudah_dibayar, nominal),
            "sisa_tagihan": sisa,
            "label_kelompok": info["label_periode"],
            "tahun_kalender": info["tahun_kalender"],
            "bulan_urut": info["bulan_urut"],
            "transaksi_aktif": transaksi,
            "terkunci_transaksi": transaksi is not None
        }

        daftar_tagihan.append(item)

        kunci = (
            item["label_kelompok"],
            item["tahun_pelajaran"],
        )

        if kunci not in grup_dict:
            grup_dict[kunci] = {
                "label": item["label_kelompok"],
                "tahun_pelajaran": item["tahun_pelajaran"],
                "tahun_kalender": item["tahun_kalender"],
                "bulan_urut": item["bulan_urut"],
                "daftar": [],
            }

        grup_dict[kunci]["daftar"].append(item)

    grup_tagihan = sorted(
        grup_dict.values(),
        key=lambda grup: (
            grup["tahun_kalender"],
            grup["bulan_urut"],
            grup["tahun_pelajaran"],
            grup["label"],
        ),
    )

    for grup in grup_tagihan:
        grup["daftar"].sort(
            key=lambda item: item["nama"].lower()
        )

    rombel = (
        (siswa.kelas_sekarang.nama_kelas or "").strip()
        if siswa.kelas_sekarang
        else ""
    )
    tingkat = str(siswa.tingkat or "").strip()

    if tingkat and rombel:
        kelas = f"Kelas {tingkat} · {rombel}"
    elif rombel:
        kelas = rombel
    elif tingkat:
        kelas = f"Kelas {tingkat}"
    else:
        kelas = "Belum ditentukan"

    return render_template(
        "payment/proses.html",
        siswa=siswa,
        kelas=kelas,
        daftar_tagihan=daftar_tagihan,
        grup_tagihan=grup_tagihan,
    )

@payment_public_bp.route(
    "/status-transaksi/<string:kode_transaksi>",
    methods=["GET"],
    endpoint="status_transaksi"
)
def status_transaksi(kode_transaksi):
    pengajuan = PengajuanPembayaran.query.filter_by(
        kode_transaksi=kode_transaksi
    ).first_or_404()

    status_labels = {
        "menunggu_verifikasi": "Menunggu Verifikasi",
        "menunggu_pembayaran": "Menunggu Pembayaran — Simulasi",
        "disetujui": "Pembayaran Disetujui",
        "ditolak": "Pengajuan Ditolak",
        "dibatalkan": "Transaksi Dibatalkan",
    }

    return render_template(
        "payment/status_transaksi.html",
        pengajuan=pengajuan,
        status_label=status_labels.get(
            pengajuan.status,
            pengajuan.status.replace("_", " ").title()
        )
    )


@payment_public_bp.route(
    "/riwayat/<string:nisn>",
    methods=["GET"],
    endpoint="riwayat_transaksi",
)
def riwayat_transaksi(nisn):
    if not nisn.isdigit() or len(nisn) != 10:
        abort(404)

    siswa = Siswa.query.filter_by(nisn=nisn).first_or_404()

    pengajuan_list = (
        PengajuanPembayaran.query
        .filter_by(siswa_id=siswa.id)
        .order_by(PengajuanPembayaran.diajukan_pada.desc())
        .all()
    )

    status_labels = {
        "menunggu_verifikasi": "Menunggu Verifikasi",
        "menunggu_pembayaran": "Menunggu Pembayaran",
        "diproses": "Sedang Diproses",
        "disetujui": "Disetujui",
        "ditolak": "Ditolak",
        "dibatalkan": "Dibatalkan",
    }

    return render_template(
        "payment/riwayat_transaksi.html",
        siswa=siswa,
        pengajuan_list=pengajuan_list,
        status_labels=status_labels,
    )


@payment_public_bp.route(
    "/transaksi/<string:nisn>/<string:kode_transaksi>",
    methods=["GET"],
    endpoint="detail_transaksi",
)
def detail_transaksi(nisn, kode_transaksi):
    # Validasi NISN.
    if not nisn.isdigit() or len(nisn) != 10:
        abort(404)

    siswa = Siswa.query.filter_by(nisn=nisn).first_or_404()

    # Pastikan transaksi memang milik siswa tersebut.
    pengajuan = PengajuanPembayaran.query.filter_by(
        kode_transaksi=kode_transaksi,
        siswa_id=siswa.id,
    ).first_or_404()

    status_labels = {
        "menunggu_pembayaran": "Menunggu Pembayaran",
        "menunggu_verifikasi": "Menunggu Verifikasi",
        "diproses": "Sedang Diproses",
        "disetujui": "Disetujui",
        "ditolak": "Ditolak",
        "dibatalkan": "Dibatalkan",
    }

    return render_template(
        "payment/status_transaksi.html",
        siswa=siswa,
        pengajuan=pengajuan,
        status_label=status_labels.get(
            pengajuan.status,
            pengajuan.status.replace("_", " ").title(),
        ),
    )


@payment_public_bp.route(
    "/unggah-bukti/<string:nisn>/<string:kode_transaksi>",
    methods=["POST"],
    endpoint="unggah_bukti",
)
def unggah_bukti(nisn, kode_transaksi):

    if not nisn.isdigit() or len(nisn) != 10:
        abort(404)

    siswa = Siswa.query.filter_by(nisn=nisn).first_or_404()

    pengajuan = (
        PengajuanPembayaran.query
        .filter_by(
            kode_transaksi=kode_transaksi,
            siswa_id=siswa.id,
        )
        .with_for_update()
        .first_or_404()
    )

    tujuan_redirect = url_for(
        "payment_public.detail_transaksi",
        nisn=nisn,
        kode_transaksi=kode_transaksi,
    )

    # Hanya Transfer Bank yang menerima bukti manual.
    if pengajuan.metode != "Transfer Bank":
        flash(
            "Unggah bukti hanya tersedia untuk metode Transfer Bank.",
            "error",
        )
        return redirect(tujuan_redirect)

    # Bukti yang sudah ada tidak boleh diganti orang tua.
    if pengajuan.bukti_pembayaran:
        flash(
            "Bukti pembayaran sudah tercatat dan tidak dapat diganti.",
            "warning",
        )
        return redirect(tujuan_redirect)

    # Hanya transaksi menunggu verifikasi yang dapat menerima bukti.
    if pengajuan.status != "menunggu_verifikasi":
        flash(
            "Transaksi ini tidak dapat menerima unggahan bukti.",
            "error",
        )
        return redirect(tujuan_redirect)

    file = request.files.get("bukti_pembayaran")

    if not file or not file.filename:
        flash("Pilih file bukti pembayaran terlebih dahulu.", "error")
        return redirect(tujuan_redirect)

    nama_asli = secure_filename(file.filename)

    if "." not in nama_asli:
        flash("Format file tidak valid.", "error")
        return redirect(tujuan_redirect)

    ekstensi = nama_asli.rsplit(".", 1)[1].lower()
    ekstensi_diizinkan = {"jpg", "jpeg", "png", "pdf"}

    if ekstensi not in ekstensi_diizinkan:
        flash(
            "Format file harus JPG, JPEG, PNG, atau PDF.",
            "error",
        )
        return redirect(tujuan_redirect)

    isi_file = file.read(3 * 1024 * 1024 + 1)

    if not isi_file:
        flash("File yang dipilih kosong.", "error")
        return redirect(tujuan_redirect)

    if len(isi_file) > 3 * 1024 * 1024:
        flash("Ukuran file maksimal 3 MB.", "error")
        return redirect(tujuan_redirect)

    nama_file = secrets.token_hex(16) + "." + ekstensi

    folder_upload = os.path.join(
        current_app.instance_path,
        "uploads",
        "bukti_pembayaran",
    )

    os.makedirs(folder_upload, exist_ok=True)

    path_file = os.path.join(folder_upload, nama_file)

    try:
        with open(path_file, "wb") as tujuan:
            tujuan.write(isi_file)

        pengajuan.bukti_pembayaran = nama_file
        db.session.commit()

        flash(
            "Bukti pembayaran berhasil diunggah. "
            "Silakan tunggu verifikasi pihak sekolah.",
            "success",
        )

    except Exception:
        db.session.rollback()

        if os.path.exists(path_file):
            os.remove(path_file)

        current_app.logger.exception(
            "Gagal menyimpan bukti pembayaran"
        )

        flash(
            "Bukti pembayaran gagal disimpan. Silakan coba kembali.",
            "error",
        )

    return redirect(tujuan_redirect)
