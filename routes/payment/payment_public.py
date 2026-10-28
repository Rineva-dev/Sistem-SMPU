from flask import Blueprint, render_template, request, jsonify, abort, redirect, url_for, flash
from models import (
    Siswa,
    TagihanSiswa,
    JenisPembayaran,
    RiwayatPembayaran
)
from datetime import date
from models import db
import re

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

    kelas = (
        siswa.kelas_sekarang.nama_kelas
        if getattr(siswa, "kelas_sekarang", None)
        else (siswa.tingkat or "Belum ditentukan")
    )

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
    methods=["GET"],
    endpoint="proses_pembayaran"
)
def proses_pembayaran(nisn):
    # Validasi NISN
    if not nisn.isdigit() or len(nisn) != 10:
        flash("NISN tidak valid.", "error")
        return redirect(url_for("payment_public.index"))

    # Cari siswa
    siswa = Siswa.query.filter_by(
        nisn=nisn,
        status="aktif"
    ).first()

    if not siswa:
        flash("Data siswa tidak ditemukan atau tidak aktif.", "error")
        return redirect(url_for("payment_public.index"))

    # Sementara tampilkan halaman informasi proses pembayaran.
    # Form pemilihan tagihan akan dibuat pada tahap berikutnya.
    return render_template(
        "payment/proses.html",
        siswa=siswa
    )