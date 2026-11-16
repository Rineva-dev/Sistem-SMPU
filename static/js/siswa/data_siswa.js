
/* ==========================================================
   SMPU STUDENT HUB — SPA READY INTERACTION ENGINE
   Compatible with SMPU SPA Navigation
   ========================================================== */

(() => {
    "use strict";

    const INIT_ATTR = "shInitialized";
    const LISTENER_ATTR = "shSpaListener";
    const MODAL_LISTENER_ATTR = "shModalListener";

    /* ======================================================
       INITIALIZE STUDENT HUB
    ====================================================== */

    function initStudentHub() {

        const root = document.querySelector(".student-hub");

        if (!root) {
            console.log("[STUDENT HUB] Root tidak ditemukan.");
            return;
        }

        // Hindari inisialisasi dua kali pada elemen yang sama.
        if (root.dataset[INIT_ATTR] === "true") return;

        root.dataset[INIT_ATTR] = "true";

        console.log("[STUDENT HUB] Berhasil diinisialisasi.");

        const search = root.querySelector("#cariSiswa");
        const statusSelect = root.querySelector("#filterStatusSiswa");

        const rows = Array.from(
            root.querySelectorAll(".sh-student-row")
        );

        const tabs = root.querySelectorAll(".sh-tab");

        const visibleCount = root.querySelector("#shVisibleCount");
        const totalCount = root.querySelector("#shTotalCount");
        const noResult = root.querySelector("#shNoResult");
        const resetButton = root.querySelector("#shResetFilter");

        let activeTab = "all";

        /* =====================================
           STATUS NORMALIZATION
        ===================================== */

        function cocokStatus(status, filter) {

            if (!filter || filter === "all") return true;

            if (filter === "nonaktif") {
                return status !== "aktif" && status !== "lulus";
            }

            return status === filter;
        }

        /* =====================================
           FILTER ENGINE
        ===================================== */

        function filterSiswa() {

            const keyword = (search?.value || "")
                .toLowerCase()
                .trim();

            const dropdownFilter = statusSelect?.value || "";

            let jumlah = 0;

            rows.forEach(row => {

                const teks = row.textContent
                    .toLowerCase()
                    .replace(/\s+/g, " ");

                const status = row.dataset.status || "";

                const cocokKeyword = teks.includes(keyword);
                const cocokTab = cocokStatus(status, activeTab);
                const cocokDropdown = cocokStatus(
                    status,
                    dropdownFilter
                );

                const tampil =
                    cocokKeyword &&
                    cocokTab &&
                    cocokDropdown;

                row.hidden = !tampil;

                if (tampil) jumlah++;

            });

            if (visibleCount) {
                visibleCount.textContent = jumlah;
            }

            if (totalCount) {
                totalCount.textContent = rows.length;
            }

            if (noResult) {
                noResult.hidden = jumlah !== 0;
            }
        }

        /* =====================================
           SEARCH
        ===================================== */

        search?.addEventListener("input", filterSiswa);

        /* =====================================
           DROPDOWN STATUS
        ===================================== */

        statusSelect?.addEventListener("change", function () {

            activeTab = "all";

            tabs.forEach(tab => {
                tab.classList.toggle(
                    "active",
                    tab.dataset.filter === "all"
                );
            });

            filterSiswa();
        });

        /* =====================================
           QUICK FILTER TABS
        ===================================== */

        tabs.forEach(tab => {

            tab.addEventListener("click", function () {

                activeTab = this.dataset.filter || "all";

                tabs.forEach(item => {
                    item.classList.remove("active");
                });

                this.classList.add("active");

                if (statusSelect) {
                    statusSelect.value = "";
                }

                filterSiswa();
            });

        });

        /* =====================================
           RESET FILTER
        ===================================== */

        resetButton?.addEventListener("click", function () {

            if (search) search.value = "";

            if (statusSelect) {
                statusSelect.value = "";
            }

            activeTab = "all";

            tabs.forEach(tab => {
                tab.classList.toggle(
                    "active",
                    tab.dataset.filter === "all"
                );
            });

            filterSiswa();
        });

        /* =====================================
           INITIAL STATE
        ===================================== */

        filterSiswa();

        /* =====================================
           TAHUN PENDAFTARAN
        ===================================== */

        const tanggalDiterima =
            root.querySelector("#tanggalDiterima");

        const tahunDiterima =
            root.querySelector("#tahunDiterima");

        function ambilTahunDariTanggal() {

            if (!tanggalDiterima || !tahunDiterima) return;

            tahunDiterima.value = tanggalDiterima.value
                ? tanggalDiterima.value.split("-")[0]
                : "";
        }

        tanggalDiterima?.addEventListener(
            "change",
            ambilTahunDariTanggal
        );

        ambilTahunDariTanggal();

    }

    /* ======================================================
       GLOBAL MODAL FUNCTIONS
    ====================================================== */

    window.tampilkanFormNonAktif = function (id) {

        const status = document.getElementById(
            `status${id}`
        )?.value;

        const form = document.getElementById(
            `formNonAktif${id}`
        );

        if (form) {
            form.classList.toggle(
                "d-none",
                status !== "Non Aktif"
            );
        }

    };

    window.tampilkanSekolahTujuan = function (id) {

        const jenis = document.getElementById(
            `jenis${id}`
        )?.value;

        const kolom = document.getElementById(
            `kolomSekolah${id}`
        );

        if (kolom) {
            kolom.classList.toggle(
                "d-none",
                jenis !== "Pindah"
            );
        }

    };

    /* ======================================================
       BOOTSTRAP MODAL EVENT — REGISTER ONCE
    ====================================================== */

    if (
        document.documentElement.dataset[MODAL_LISTENER_ATTR] !== "true"
    ) {

        document.documentElement.dataset[MODAL_LISTENER_ATTR] = "true";

        document.addEventListener(
            "shown.bs.modal",
            function (event) {

                const modal = event.target;

                if (
                    !modal.id ||
                    !modal.id.startsWith("modalStatus")
                ) {
                    return;
                }

                const id = modal.id.replace(
                    "modalStatus",
                    ""
                );

                window.tampilkanFormNonAktif(id);
                window.tampilkanSekolahTujuan(id);

            }
        );

    }

    /* ======================================================
       SPA PAGE LOADED LISTENER — REGISTER ONCE
    ====================================================== */

    if (
        document.documentElement.dataset[LISTENER_ATTR] !== "true"
    ) {

        document.documentElement.dataset[LISTENER_ATTR] = "true";

        document.addEventListener(
            "spa:page-loaded",
            function () {

                // Tunggu sampai konten SPA selesai dimasukkan.
                requestAnimationFrame(() => {
                    initStudentHub();
                });

            }
        );

    }

    /* ======================================================
       INITIAL PAGE LOAD
    ====================================================== */

    if (document.readyState === "loading") {

        document.addEventListener(
            "DOMContentLoaded",
            initStudentHub,
            { once: true }
        );

    } else {

        initStudentHub();

    }

})();
