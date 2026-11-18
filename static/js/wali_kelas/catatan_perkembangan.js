
/* =========================================================
   CATATAN PERKEMBANGAN SISWA
   Disesuaikan dengan template HTML SMPU
   ========================================================= */

(() => {
    "use strict";

    const $ = (selector, parent = document) =>
        parent.querySelector(selector);

    const modalForm = () => $("#cpModalForm");
    const modalDetail = () => $("#cpModalDetail");
    const formCatatan = () => $("#cpForm");

    function bukaModal(modal) {
        if (!modal) return;

        modal.classList.add("show");
        modal.style.display = "flex";
        document.body.style.overflow = "hidden";
    }

    function tutupModal(modal) {
        if (!modal) return;

        modal.classList.remove("show");
        modal.style.display = "none";

        if (!document.querySelector(".cp-modal.show")) {
            document.body.style.overflow = "";
        }
    }

    function setField(id, value) {
        const el = document.getElementById(id);
        if (el) el.value = value ?? "";
    }

    function setText(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value || "-";
    }

    function formatTanggal(value) {
        if (!value) return "-";

        const parts = String(value).split("-");
        if (parts.length !== 3) return value;

        return `${parts[2]}/${parts[1]}/${parts[0]}`;
    }

    function formatStatus(value) {
        const status = {
            belum_ditindaklanjuti: "Belum Ditindaklanjuti",
            sedang_ditindaklanjuti: "Sedang Ditindaklanjuti",
            selesai: "Selesai"
        };

        return status[value] || value || "-";
    }

    function filterSiswa() {
        const kelas = $("#cpKelas");
        const siswa = $("#cpSiswa");

        if (!kelas || !siswa) return;

        const kelasId = kelas.value;

        Array.from(siswa.options).forEach(option => {
            if (!option.value) {
                option.hidden = false;
                option.disabled = false;
                return;
            }

            const kelasSiswa = option.dataset.kelas || "";
            const cocok = !kelasId || kelasSiswa === kelasId;

            option.hidden = !cocok;
            option.disabled = !cocok;
        });

        const selected = siswa.selectedOptions[0];

        if (selected && selected.disabled) {
            siswa.value = "";
        }
    }

    function setFormAction(mode, id = null) {
        const form = formCatatan();
        if (!form) return;

        const basePath = window.location.pathname.replace(/\/$/, "");

        if (mode === "edit" && id) {
            form.action = `${basePath}/${encodeURIComponent(id)}/edit`;
        } else {
            form.action = `${basePath}/tambah`;
        }
    }

    function tampilkanStatusEdit(aktif) {
        const group = $("#cpStatusGroup");
        if (group) group.hidden = !aktif;
    }

    // -----------------------------------------------------
    // TAMBAH
    // -----------------------------------------------------

    window.cpBukaTambah = function () {
        const form = formCatatan();
        if (!form) return;

        form.reset();

        setFormAction("tambah");
        tampilkanStatusEdit(false);

        const title = $("#cpFormTitle");
        if (title) title.textContent = "Tambah Catatan";

        const tanggal = $("#cpTanggal");

        if (tanggal && !tanggal.value) {
            const now = new Date();
            const offset = now.getTimezoneOffset() * 60000;

            tanggal.value = new Date(now.getTime() - offset)
                .toISOString()
                .slice(0, 10);
        }

        filterSiswa();
        bukaModal(modalForm());
    };

    window.cpTutupForm = function () {
        tutupModal(modalForm());
    };

    // -----------------------------------------------------
    // EDIT
    // -----------------------------------------------------

    window.cpBukaEdit = function (button) {
        if (!button) return;

        const data = button.dataset;
        const form = formCatatan();

        if (!form) return;

        form.reset();

        setFormAction("edit", data.id);

        setField("cpKelas", data.kelas);
        filterSiswa();

        setField("cpSiswa", data.siswa);
        setField("cpTanggal", data.tanggal);
        setField("cpKategori", data.kategori);
        setField("cpJudul", data.judul);
        setField("cpDeskripsi", data.deskripsi);
        setField("cpTindakLanjut", data.tindakLanjut);
        setField(
            "cpStatus",
            data.status || "belum_ditindaklanjuti"
        );

        tampilkanStatusEdit(true);

        const title = $("#cpFormTitle");
        if (title) title.textContent = "Edit Catatan";

        bukaModal(modalForm());
    };

    // -----------------------------------------------------
    // DETAIL
    // -----------------------------------------------------

    window.cpLihatDetail = function (button) {
        if (!button) return;

        const data = button.dataset;

        setText("cpDetailNama", data.nama);
        setText("cpDetailKelas", data.kelas);
        setText("cpDetailTanggal", formatTanggal(data.tanggal));
        setText("cpDetailKategori", data.kategori);
        setText("cpDetailJudul", data.judul);
        setText("cpDetailDeskripsi", data.deskripsi);
        setText(
            "cpDetailTindakLanjut",
            data.tindakLanjut || "Belum ada tindak lanjut."
        );
        setText("cpDetailStatus", formatStatus(data.status));

        bukaModal(modalDetail());
    };

    window.cpTutupDetail = function () {
        tutupModal(modalDetail());
    };

    // -----------------------------------------------------
    // HAPUS
    // -----------------------------------------------------

    window.cpKonfirmasiHapus = function (id) {
        if (!id) return;

        const yakin = window.confirm(
            "Hapus catatan perkembangan ini?\n\n" +
            "Data yang sudah dihapus tidak dapat dikembalikan."
        );

        if (!yakin) return;

        const form = $("#cpFormHapus");
        if (!form) return;

        const basePath = window.location.pathname.replace(/\/$/, "");

        form.action = `${basePath}/${encodeURIComponent(id)}/hapus`;
        form.submit();
    };

    // -----------------------------------------------------
    // EVENT
    // -----------------------------------------------------

    document.addEventListener("DOMContentLoaded", () => {
        const kelas = $("#cpKelas");

        if (kelas) {
            kelas.addEventListener("change", filterSiswa);
        }

        document.querySelectorAll(".cp-modal").forEach(modal => {
            modal.addEventListener("click", event => {
                if (event.target === modal) {
                    tutupModal(modal);
                }
            });
        });

        document.addEventListener("keydown", event => {
            if (event.key === "Escape") {
                tutupModal(modalForm());
                tutupModal(modalDetail());
            }
        });

        filterSiswa();
    });

})();
