
/* =========================================================
   PREMIUM PAYMENT CONFIGURATION
   SPA compatible
========================================================= */

(() => {
    "use strict";

    function initPengaturanPembayaran() {
        const halaman = document.querySelector(".pengaturan-pembayaran-page");
        if (!halaman || halaman.dataset.initialized === "true") return;

        halaman.dataset.initialized = "true";

        const pilihAngkatan = halaman.querySelector("#pilihAngkatan");
        const modalElement = halaman.querySelector("#modalTambah");

        // ==========================================
        // MODAL PORTAL — PINDAHKAN LANGSUNG KE BODY
        // Agar tidak terpotong overflow / SPA container
        // ==========================================
        if (modalElement) {
            const portal = document.createElement("div");
            portal.className = "pengaturan-pembayaran-page pp-modal-portal";

            document.body.appendChild(portal);
            portal.appendChild(modalElement);
        }

        // Elemen-elemen modal tetap bisa diakses
        const formTarif = modalElement?.querySelector("#formTarif");
        const pilihJenis = modalElement?.querySelector("#pilihJenisUtama");
        const bagianKelompok = modalElement?.querySelector("#bagianKelompok");
        const pilihKelompok = modalElement?.querySelector("#pilihKelompok");
        const inputEditId = modalElement?.querySelector("#editTarifId");
        const inputKode = modalElement?.querySelector("#kodeTarif");
        const inputPola = modalElement?.querySelector("#polaWaktu");
        const inputNominal = modalElement?.querySelector("#nominalInput");
        const inputNominalAsli = modalElement?.querySelector("#nominalAsli");
        const inputKeterangan = modalElement?.querySelector("#keteranganTarif");
        const tombolSimpan = modalElement?.querySelector("#btnSimpanTarif");;


        // =====================================================
        // DATA BACKEND
        // =====================================================

        function bacaJSON(id, fallback) {
            const element = halaman.querySelector("#" + id);

            if (!element) return fallback;

            try {
                return JSON.parse(element.textContent.trim());
            } catch (error) {
                console.error("Gagal membaca data:", id, error);
                return fallback;
            }
        }

        const semuaEkskul = bacaJSON("ppDataEkskul", []);
        const semuaEkskulTahun = bacaJSON("ppDataEkskulTahun", []);

        const semuaPeminatan = bacaJSON("ppDataPeminatan", []);
        const semuaPeminatanTahun = bacaJSON("ppDataPeminatanTahun", []);

        const tahunDipilih = bacaJSON("ppTahunDipilih", "");

        // =====================================================
        // FORMAT RUPIAH
        // =====================================================

        function hanyaAngka(value) {
            return String(value || "").replace(/\D/g, "");
        }

        function formatRupiah(value) {
            const angka = hanyaAngka(value);

            if (!angka) return "";

            return angka.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
        }

        function sinkronkanNominal() {
            if (!inputNominal || !inputNominalAsli) return;

            const angka = hanyaAngka(inputNominal.value);

            inputNominal.value = formatRupiah(angka);
            inputNominalAsli.value = angka;
        }

        if (inputNominal) {
            inputNominal.addEventListener("input", sinkronkanNominal);

            inputNominal.addEventListener("blur", sinkronkanNominal);
        }

        // =====================================================
        // PILIH TAHUN PELAJARAN
        // =====================================================

        if (pilihAngkatan) {
            pilihAngkatan.addEventListener("change", function () {
                const tahun = this.value;

                if (!tahun) {
                    window.location.href = "/bendahara/pengaturan-pembayaran";
                    return;
                }

                window.location.href =
                    "/bendahara/pengaturan-pembayaran?angkatan=" +
                    encodeURIComponent(tahun);
            });
        }

        // =====================================================
        // PILIH KELOMPOK EKSKUL / PEMINATAN
        // =====================================================

        function tampilkanKelompok(jenis, namaTerpilih = "") {
            if (!bagianKelompok || !pilihKelompok) return;

            pilihKelompok.innerHTML =
                '<option value="">Pilih kelompok</option>';

            if (!tahunDipilih) {
                bagianKelompok.hidden = true;
                pilihKelompok.required = false;
                return;
            }

            let namaList = [];
            let tahunList = [];

            if (jenis === "Ekstrakurikuler") {
                namaList = semuaEkskul;
                tahunList = semuaEkskulTahun;
            } else if (jenis === "Kelas Peminatan") {
                namaList = semuaPeminatan;
                tahunList = semuaPeminatanTahun;
            } else {
                bagianKelompok.hidden = true;
                pilihKelompok.required = false;
                return;
            }

            const tersedia = namaList
                .map((nama, index) => ({
                    nama: nama,
                    tahun: String(tahunList[index] || "").split("-")[0].trim()
                }))
                .filter(item => item.tahun === String(tahunDipilih))
                .filter((item, index, array) =>
                    array.findIndex(x => x.nama === item.nama) === index
                );

            tersedia.forEach(item => {
                const option = document.createElement("option");

                option.value = item.nama;
                option.textContent = item.nama;

                if (item.nama === namaTerpilih) {
                    option.selected = true;
                }

                pilihKelompok.appendChild(option);
            });

            bagianKelompok.hidden = false;
            pilihKelompok.required = true;

            if (tersedia.length === 0) {
                const option = document.createElement("option");
                option.value = "";
                option.textContent = "Belum ada kelompok untuk tahun ini";
                option.disabled = true;
                pilihKelompok.appendChild(option);
            }
        }

        if (pilihJenis) {
            pilihJenis.addEventListener("change", function () {
                tampilkanKelompok(this.value);
            });
        }

        // =====================================================
        // RESET FORM
        // =====================================================

        function resetForm() {
            if (!formTarif) return;

            formTarif.reset();

            if (inputEditId) inputEditId.value = "";

            if (bagianKelompok) bagianKelompok.hidden = true;

            if (pilihKelompok) {
                pilihKelompok.innerHTML =
                    '<option value="">Pilih kelompok</option>';
                pilihKelompok.required = false;
            }

            if (inputNominal) inputNominal.value = "";
            if (inputNominalAsli) inputNominalAsli.value = "";

            if (tombolSimpan) {
                tombolSimpan.disabled = false;
                tombolSimpan.innerHTML =
                    '<i class="fas fa-check"></i><span>Simpan Tarif</span>';
            }

            const judul = modalElement.querySelector("#modalTambahLabel");

            if (judul) judul.textContent = "Tambah Tarif Baru";
        }

        // =====================================================
        // MODAL TAMBAH
        // =====================================================

        if (modalElement) {
            modalElement.addEventListener("show.bs.modal", function (event) {
                const pemicu = event.relatedTarget;

                if (pemicu && !pemicu.classList.contains("btnUbah")) {
                    resetForm();
                }
            });

            modalElement.addEventListener("hidden.bs.modal", resetForm);
        }

        // =====================================================
        // MODAL EDIT
        // =====================================================

        halaman.querySelectorAll(".btnUbah").forEach(button => {
            button.addEventListener("click", function () {
                const row = this.closest("tr");

                if (!row || !modalElement || !formTarif) return;

                resetForm();

                const id = row.dataset.id || "";
                const kode = row.dataset.kode || "";
                const pola = row.dataset.pola || "";
                const nama = row.dataset.nama || "";
                const nominal = row.dataset.nominal || "";
                const keterangan = row.dataset.keterangan || "";

                if (inputEditId) inputEditId.value = id;
                if (inputKode) inputKode.value = kode;
                if (inputPola) inputPola.value = pola;
                if (inputKeterangan) inputKeterangan.value = keterangan;

                // Tentukan kategori berdasarkan nama tarif.
                let kategori = nama;
                let namaKelompok = "";

                const kategoriList = [
                    "Ekstrakurikuler",
                    "Kelas Peminatan",
                    "Pembangunan",
                    "Seragam",
                    "SPP",
                    "Buku"
                ];

                const kategoriCocok = kategoriList.find(item =>
                    nama === item || nama.startsWith(item + " - ")
                );

                if (kategoriCocok) {
                    kategori = kategoriCocok;

                    if (
                        kategoriCocok === "Ekstrakurikuler" ||
                        kategoriCocok === "Kelas Peminatan"
                    ) {
                        namaKelompok = nama.substring(
                            kategoriCocok.length
                        ).replace(/^\s*-\s*/, "");
                    }
                }

                if (pilihJenis) {
                    pilihJenis.value = kategori;

                    if (
                        kategori === "Ekstrakurikuler" ||
                        kategori === "Kelas Peminatan"
                    ) {
                        tampilkanKelompok(kategori, namaKelompok);
                    } else if (bagianKelompok) {
                        bagianKelompok.hidden = true;
                    }
                }

                if (inputNominal) {
                    inputNominal.value = formatRupiah(nominal);
                }

                if (inputNominalAsli) {
                    inputNominalAsli.value = hanyaAngka(nominal);
                }

                const judul = modalElement.querySelector("#modalTambahLabel");

                if (judul) judul.textContent = "Ubah Tarif Pembayaran";

                if (tombolSimpan) {
                    tombolSimpan.innerHTML =
                        '<i class="fas fa-save"></i><span>Simpan Perubahan</span>';
                }

                if (window.bootstrap && window.bootstrap.Modal) {
                    window.bootstrap.Modal
                        .getOrCreateInstance(modalElement)
                        .show();
                }
            });
        });

        // =====================================================
        // VALIDASI NOMINAL SEBELUM SUBMIT
        // =====================================================

        if (formTarif) {
            formTarif.addEventListener("submit", function (event) {
                sinkronkanNominal();

                const nominal = inputNominalAsli
                    ? inputNominalAsli.value
                    : "";

                if (!nominal || Number(nominal) <= 0) {
                    event.preventDefault();

                    if (inputNominal) {
                        inputNominal.focus();
                        inputNominal.classList.add("pp-input-invalid");

                        setTimeout(() => {
                            inputNominal.classList.remove("pp-input-invalid");
                        }, 1800);
                    }

                    alert("Nominal pembayaran harus lebih besar dari nol.");
                    return;
                }

                if (tombolSimpan) {
                    tombolSimpan.disabled = true;
                    tombolSimpan.innerHTML =
                        '<i class="fas fa-spinner fa-spin"></i><span>Menyimpan...</span>';
                }
            });
        }

        // =====================================================
        // AKTIF / NONAKTIFKAN TARIF
        // =====================================================

        halaman.querySelectorAll(".pp-toggle-btn").forEach(link => {
            link.addEventListener("click", async function (event) {
                event.preventDefault();

                const url = this.href;
                const judul = this.getAttribute("title") || "Ubah status";
                const row = this.closest("tr");

                if (!url || this.dataset.processing === "true") return;

                const konfirmasi = window.confirm(
                    "Apakah Anda yakin ingin " +
                    judul.toLowerCase() +
                    " tarif " +
                    (row?.dataset.nama || "ini") +
                    "?"
                );

                if (!konfirmasi) return;

                this.dataset.processing = "true";
                this.style.opacity = ".55";
                this.style.pointerEvents = "none";

                try {
                    const response = await fetch(url, {
                        method: "POST",
                        credentials: "same-origin",
                        headers: {
                            "X-Requested-With": "XMLHttpRequest"
                        }
                    });

                    if (!response.ok) {
                        throw new Error("Server merespons " + response.status);
                    }

                    window.location.reload();

                } catch (error) {
                    console.error("Gagal mengubah status tarif:", error);

                    alert(
                        "Gagal mengubah status tarif. Silakan coba kembali."
                    );

                    this.dataset.processing = "false";
                    this.style.opacity = "";
                    this.style.pointerEvents = "";
                }
            });
        });

        console.log(
            "%c PAYMENT CONFIGURATION READY ",
            "background:#08785a;color:#fff;padding:6px 10px;border-radius:5px;font-weight:bold"
        );
    }

    // Inisialisasi saat script pertama kali dimuat.
    initPengaturanPembayaran();

    // Inisialisasi kembali setelah navigasi SPA.
    document.addEventListener(
        "spa:page-loaded",
        initPengaturanPembayaran
    );

})();
