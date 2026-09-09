from flask import Blueprint, current_app, request, jsonify, session
from sqlalchemy import select
from models import db, SuratKeluar, PenandatanganSurat, User, Guru
from datetime import datetime
import os, base64
from werkzeug.utils import secure_filename
import qrcode
import qrcode.image.svg as svg
from lxml import etree

surat_bp = Blueprint('surat_global', __name__, url_prefix='/surat-global')

UPLOAD_FOLDER_KELUAR = 'static/uploads/surat_keluar'
QR_FOLDER = 'static/assets/qr_surat'
os.makedirs(QR_FOLDER, exist_ok=True)

# ✅ FUNGSI BUAT QR KHUSUS PER PENANDATANGAN
def buat_qr_per_ttd(surat, ttd):
    """Buat QR unik untuk setiap penandatangan"""
    data_qr = f"""
Surat Nomor: {surat.nomor_surat}
Tanggal Surat: {surat.tanggal_surat.strftime('%d %B %Y')}
Perihal: {surat.perihal}
Sekolah: SMP Unggulan Hamzanwadi
Ditandatangani Oleh: {ttd.nama}
Jabatan: {ttd.jabatan}
Tanggal Tanda Tangan: {datetime.now().strftime('%d %B %Y %H:%M')}
Status: Sah & Terverifikasi
""".strip()

    # Buat QR format SVG
    factory = svg.SvgPathImage
    img = qrcode.make(
        data_qr,
        image_factory=factory,
        box_size=10,
        border=2,
        error_correction=qrcode.constants.ERROR_CORRECT_H
    )

    nama_file = secure_filename(
        f"surat_{surat.id}_ttd_{ttd.id}_{surat.nomor_surat.replace('/', '-')}.svg"
    )
    path_svg = os.path.join(QR_FOLDER, nama_file)
    img.save(path_svg)

    # Sisipkan logo sekolah di tengah QR
    tree = etree.parse(path_svg)
    root = tree.getroot()
    SVG_NS = "http://www.w3.org/2000/svg"

    if "viewBox" not in root.attrib:
        w = float(root.attrib.get("width", "200").replace("mm", ""))
        h = float(root.attrib.get("height", "200").replace("mm", ""))
        root.attrib["viewBox"] = f"0 0 {w} {h}"

    vb = list(map(float, root.attrib["viewBox"].split()))
    cx, cy = vb[2]/2, vb[3]/2

    radius_outer = vb[2] * 0.16
    radius_gap1 = radius_outer * 0.88
    radius_inner = radius_outer * 0.78
    radius_gap2 = radius_outer * 0.68
    logo_size = radius_gap2 * 1.2

    logo_path = os.path.join("static", "img", "logo1.svg")
    with open(logo_path, "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode("utf-8")
    logo_href = f"data:image/svg+xml;base64,{logo_base64}"

    root.append(etree.Element(f"{{{SVG_NS}}}circle", {"cx":str(cx), "cy":str(cy), "r":str(radius_outer), "fill":"#FFFFFF"}))
    root.append(etree.Element(f"{{{SVG_NS}}}circle", {"cx":str(cx), "cy":str(cy), "r":str(radius_gap1), "fill":"#00221A"}))
    root.append(etree.Element(f"{{{SVG_NS}}}circle", {"cx":str(cx), "cy":str(cy), "r":str(radius_inner), "fill":"#FFFFFF"}))
    root.append(etree.Element(f"{{{SVG_NS}}}circle", {"cx":str(cx), "cy":str(cy), "r":str(radius_gap2), "fill":"#00221A"}))
    root.append(etree.Element(f"{{{SVG_NS}}}image", {
        "href": logo_href, "x":str(cx-logo_size/2), "y":str(cy-logo_size/2),
        "width":str(logo_size), "height":str(logo_size), "preserveAspectRatio":"xMidYMid meet"
    }))

    tree.write(path_svg, encoding="UTF-8", xml_declaration=True, pretty_print=True)
    return f"assets/qr_surat/{nama_file}"

# --- RUTE DAFTAR SURAT ---
@surat_bp.route('/daftar-surat')
def daftar_surat():
    if not session.get('logged_in'):
        return jsonify({"error": "Belum login", "surat": [], "jumlah": 0}), 200

    user_id = session.get('user_id')
    peran = session.get('peran', '')

    pengguna = db.session.execute(select(User).filter_by(id=user_id)).scalar_one_or_none()
    guru_id_saya = pengguna.guru_id if pengguna else None

    jenis = request.args.get('jenis', 'perlu')

    if jenis == 'perlu':
        if peran in ['tu', 'admin']:
            surat = SuratKeluar.query.filter_by(status='Diajukan').order_by(SuratKeluar.tanggal_surat.desc()).all()
        else:
            if not guru_id_saya:
                surat = []
            else:
                surat = SuratKeluar.query.join(PenandatanganSurat).filter(
                    SuratKeluar.status == 'Diajukan',
                    PenandatanganSurat.id_guru == guru_id_saya,
                    PenandatanganSurat.ttd_selesai == False
                ).order_by(SuratKeluar.tanggal_surat.desc()).all()

    elif jenis == 'disetujui':
        if peran in ['tu', 'admin']:
            surat = SuratKeluar.query.filter_by(status='Disetujui').order_by(SuratKeluar.tanggal_surat.desc()).all()
        else:
            if not guru_id_saya:
                surat = []
            else:
                surat = SuratKeluar.query.join(PenandatanganSurat).filter(
                    SuratKeluar.status.in_(['Diajukan', 'Disetujui']),
                    PenandatanganSurat.id_guru == guru_id_saya,
                    PenandatanganSurat.ttd_selesai == True
                ).order_by(SuratKeluar.tanggal_surat.desc()).all()

    else:
        if peran in ['tu', 'admin']:
            surat = SuratKeluar.query.filter(SuratKeluar.status.in_(['Tersimpan', 'Perlu Perbaikan', 'Ditolak'])).order_by(SuratKeluar.tanggal_surat.desc()).all()
        else:
            if not guru_id_saya:
                surat = []
            else:
                surat = SuratKeluar.query.join(PenandatanganSurat).filter(
                    SuratKeluar.status.in_(['Tersimpan', 'Perlu Perbaikan', 'Ditolak']),
                    PenandatanganSurat.id_guru == guru_id_saya
                ).order_by(SuratKeluar.tanggal_surat.desc()).all()

    jumlah = SuratKeluar.query.join(PenandatanganSurat).filter(
        SuratKeluar.status == 'Diajukan',
        PenandatanganSurat.id_guru == guru_id_saya,
        PenandatanganSurat.ttd_selesai == False
    ).count() if guru_id_saya else 0

    hasil = []
    for s in surat:
        hasil.append({
            "id": s.id,
            "nomor_surat": s.nomor_surat,
            "tanggal_surat": s.tanggal_surat.strftime('%d %b %Y'),
            "perihal": s.perihal,
            "status": s.status
        })

    return jsonify({"surat": hasil, "jumlah": jumlah})

# --- RUTE AMBIL DETAIL SURAT ---
@surat_bp.route('/ambil-detail/<int:id>')
def ambil_detail(id):
    if not session.get('logged_in'):
        return jsonify({"error": "Belum login"}), 401

    surat = SuratKeluar.query.get_or_404(id)

    return jsonify({
        "id": surat.id,
        "nomor_surat": surat.nomor_surat,
        "tanggal_surat": surat.tanggal_surat.strftime('%d %B %Y'),
        "lampiran": surat.lampiran,
        "perihal": surat.perihal,
        "tujuan": surat.tujuan,
        "isi_surat": surat.isi_surat,
        "status": surat.status,
        "penandatangan": [
            {
                "id": t.id,
                "nama": t.nama,
                "jabatan": t.jabatan,
                "id_guru": t.id_guru,  # ✅ TAMBAHKAN BARIS INI
                "nip": t.guru.nip if (t.guru and t.guru.nip) else "-",
                "ttd_selesai": t.ttd_selesai,
                "qr_code": t.qr_code,
                "tanggal_ttd": t.tanggal_ttd.strftime('%d %b %Y %H:%M') if t.tanggal_ttd else None
            } 
            for t in surat.daftar_penandatangan
        ]
    })

# --- ✅ RUTE PROSES PERSETUJUAN PER ORANG ---
@surat_bp.route('/proses-persetujuan/<int:id>', methods=['POST'])
def proses_persetujuan(id):
    if not session.get('logged_in'):
        return jsonify({"status": "error", "pesan": "Belum login"}), 401

    # ✅ Ambil guru_id dari sesi dengan pengecekan
    guru_id_saya = session.get('guru_id')
    if not guru_id_saya:
        return jsonify({"status": "error", "pesan": "Data akun tidak lengkap, silakan login ulang"}), 403

    surat = SuratKeluar.query.get_or_404(id)
    tindakan = request.form.get('tindakan', '').strip().lower()
    id_ttd = request.form.get('id_ttd', type=int)
    catatan = request.form.get('catatan', '').strip()

    try:
        if tindakan in ('setuju', 'setujui'):
            if not id_ttd:
                return jsonify({"status": "error", "pesan": "ID penandatangan tidak ditemukan. Gunakan tombol di bawah nama Anda."}), 400

            # ✅ Pastikan penandatangan ini memang milik surat ini
            ttd = PenandatanganSurat.query.filter_by(id=id_ttd, surat_id=surat.id).first_or_404()

            # ✅ Bandingkan dengan ID guru yang login
            if ttd.id_guru != guru_id_saya:
                return jsonify({"status": "error", "pesan": "Anda bukan penandatangan untuk surat ini"}), 403

            # ✅ Cegah tanda tangan ganda
            if ttd.ttd_selesai:
                return jsonify({"status": "info", "pesan": "Anda sudah menandatangani surat ini sebelumnya"}), 200

            # Tandai selesai & buat QR khusus dia
            ttd.ttd_selesai = True
            ttd.tanggal_ttd = datetime.now()
            ttd.qr_code = buat_qr_per_ttd(surat, ttd)

            # Cek semua sudah tanda tangan?
            semua_selesai = all(t.ttd_selesai for t in surat.daftar_penandatangan)
            if semua_selesai:
                surat.status = 'Disetujui'
                surat.tanggal_persetujuan = datetime.now()
                surat.catatan_persetujuan = catatan

            db.session.commit()
            return jsonify({"status": "sukses", "pesan": f"Tanda tangan berhasil disimpan untuk {ttd.nama}"})

        elif tindakan == 'perbaiki':
            surat.status = 'Perlu Perbaikan'
            surat.catatan_persetujuan = catatan
            db.session.commit()
            return jsonify({"status": "sukses", "pesan": "Surat dikembalikan untuk diperbaiki"})

        elif tindakan == 'tolak':
            surat.status = 'Ditolak'
            surat.catatan_persetujuan = catatan
            db.session.commit()
            return jsonify({"status": "sukses", "pesan": "Surat ditolak"})

        else:
            return jsonify({"status": "error", "pesan": f"Tindakan tidak valid: '{tindakan}'"}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "pesan": f"Gagal memproses: {str(e)}"}), 500

@surat_bp.route('/perbarui-semua-qr', methods=['GET'])
def perbarui_semua_qr():
    if not session.get('logged_in'):
        return jsonify({"status": "error", "pesan": "Belum login"}), 401

    surat_disetujui = SuratKeluar.query.filter_by(status='Disetujui').all()
    jumlah = 0
    gagal = 0

    for surat in surat_disetujui:
        for ttd in surat.daftar_penandatangan:  # ✅ Nama baru
            if ttd.ttd_selesai:
                try:
                    ttd.qr_code = buat_qr_per_ttd(surat, ttd)
                    jumlah += 1
                except Exception as e:
                    gagal += 1
                    print(f"⚠️ Surat {surat.id} TTD {ttd.id} gagal: {e}")
    db.session.commit()
    return jsonify({"status": "sukses", "pesan": f"QR diperbarui: {jumlah}, gagal: {gagal}"})

@surat_bp.route('/perbaiki-data-penandatangan', methods=['GET'])
def perbaiki_data_penandatangan():
    if not session.get('logged_in'):
        return jsonify({"status": "error", "pesan": "Harap login terlebih dahulu"}), 401

    try:
        # ✅ Cari yang id_guru KOSONG / NULL saja
        daftar_ttd = PenandatanganSurat.query.filter(
            PenandatanganSurat.id_guru.is_(None)
        ).all()

        diperbarui = 0
        tidak_ditemukan = 0

        for ttd in daftar_ttd:
            # ✅ Cocokkan berdasarkan NAMA dan JABATAN
            guru_cocok = Guru.query.filter(
                (Guru.nama == ttd.nama) & 
                (Guru.jabatan == ttd.jabatan)
            ).first()

            if guru_cocok:
                ttd.id_guru = guru_cocok.id
                diperbarui += 1
            else:
                tidak_ditemukan += 1

        db.session.commit()
        return jsonify({
            "status": "sukses",
            "pesan": f"Selesai! Diperbarui: {diperbarui}, Tidak ditemukan: {tidak_ditemukan}"
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "pesan": f"Gagal: {str(e)}"}), 500