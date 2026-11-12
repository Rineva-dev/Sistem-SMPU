
/* =========================================================
   SMPU — BIODATA PREMIUM
   COMPLETE EDIT BIODATA • PHOTO STUDIO • SPA SAFE
========================================================= */

(() => {
    "use strict";

    /*
     * Mencegah script terdaftar berulang kali saat SPA
     * melakukan navigasi antarhalaman.
     */
    if (window.__smpuBiodataSPARegistered) return;
    window.__smpuBiodataSPARegistered = true;

    let cropper = null;
    let activePage = null;
    let previousBodyOverflow = "";
    let cropperInitializing = false;
    let fileReader = null;

    const $ = (selector, root = document) =>
        root.querySelector(selector);

    const $$ = (selector, root = document) =>
        [...root.querySelectorAll(selector)];

    /* =====================================================
       ICONS
    ===================================================== */

    function refreshIcons() {
        if (window.lucide?.createIcons) {
            window.lucide.createIcons({
                attrs: {
                    "stroke-width": 1.8
                }
            });
        }
    }

    /* =====================================================
       MODAL MANAGEMENT
    ===================================================== */

    function getActiveModals() {
        return $$(".bp-overlay.active, .bp-view-modal.active");
    }

    function bukaModal(modal) {
        if (!modal) {
            console.error("[Biodata] Modal tidak ditemukan.");
            return;
        }

        if (!modal.classList.contains("active")) {
            if (getActiveModals().length === 0) {
                previousBodyOverflow = document.body.style.overflow;
            }

            modal.classList.add("active");
        }

        document.body.style.overflow = "hidden";

        refreshIcons();
    }

    function tutupModal(modal) {
        if (!modal || !modal.classList.contains("active")) return;

        modal.classList.remove("active");

        if (getActiveModals().length === 0) {
            document.body.style.overflow = previousBodyOverflow;
        }
    }

    function tutupSemuaModal() {
        getActiveModals().forEach(modal => {
            modal.classList.remove("active");
        });

        document.body.style.overflow = previousBodyOverflow;
    }

    /* =====================================================
       CROPPER MANAGEMENT
    ===================================================== */

    function destroyCropper() {
        if (cropper) {
            try {
                cropper.destroy();
            } catch (error) {
                console.warn("[Biodata] Cropper cleanup:", error);
            }
        }

        cropper = null;
        cropperInitializing = false;
    }

    function resetCropImage() {
        const image = $("#cropImage");

        if (!image) return;

        image.onload = null;
        image.onerror = null;
        image.removeAttribute("src");
    }

    /* =====================================================
       CLEANUP
    ===================================================== */

    function cleanupBiodata() {
        destroyCropper();

        if (fileReader) {
            try {
                fileReader.abort();
            } catch (_) {
                // Tidak perlu tindakan tambahan.
            }

            fileReader = null;
        }

        tutupSemuaModal();

        const fileInput = $("#fileInput");
        const fotoData = $("#fotoData");

        if (fileInput) fileInput.value = "";
        if (fotoData) fotoData.value = "";

        resetCropImage();

        activePage = null;
    }

    /* =====================================================
       INITIALIZE BIODATA
    ===================================================== */

    function initBiodata() {
        const page = $("#biodataPage");

        if (!page) return;

        if (activePage === page) return;

        if (activePage) {
            cleanupBiodata();
        }

        activePage = page;

        refreshIcons();

        /* =================================================
           ELEMENTS
        ================================================= */

        const avatarWrapper = $("#avatarWrapper", page);
        const btnGantiFoto = $("#btnGantiFoto", page);

        const fileInput = $("#fileInput");

        const viewModal = $("#viewModal");
        const viewFoto = $("#viewFoto");

        const cropModal = $("#cropModal");
        const cropImage = $("#cropImage");

        const btnSimpanFoto = $("#btnSimpanFoto");
        const fotoData = $("#fotoData");
        const formUploadFoto = $("#formUploadFoto");

        const editModal = $("#editModal");
        const btnEdit = $("#btnEdit", page);
        const formEdit = $("#formEditBiodata");
        const btnSimpanBiodata = $("#btnSimpanBiodata");

        /* =================================================
           VALIDATE REQUIRED ELEMENTS
        ================================================= */

        if (!btnEdit) {
            console.error("[Biodata] Tombol #btnEdit tidak ditemukan.");
        }

        if (!editModal) {
            console.error("[Biodata] Modal #editModal tidak ditemukan.");
        }

        /* =================================================
           PHOTO PREVIEW
        ================================================= */

        function tampilkanFotoBesar() {
            if (!avatarWrapper || !viewModal || !viewFoto) return;

            const foto = $("img", avatarWrapper);

            if (!foto || !foto.src) return;

            viewFoto.src = foto.src;

            bukaModal(viewModal);
        }

        avatarWrapper?.addEventListener(
            "click",
            tampilkanFotoBesar
        );

        $("#btnTutupFoto")?.addEventListener("click", () => {
            tutupModal(viewModal);
        });

        $("#btnTutupFotoFooter")?.addEventListener("click", () => {
            tutupModal(viewModal);
        });

        viewModal?.addEventListener("click", event => {
            if (event.target === viewModal) {
                tutupModal(viewModal);
            }
        });

        /* =================================================
           SELECT PHOTO
        ================================================= */

        btnGantiFoto?.addEventListener("click", event => {
            event.preventDefault();
            event.stopPropagation();

            fileInput?.click();
        });

        /* =================================================
           CANCEL CROP
        ================================================= */

        function batalkanCrop() {
            destroyCropper();

            tutupModal(cropModal);

            if (fileInput) {
                fileInput.value = "";
            }

            resetCropImage();
        }

        $("#btnBatalFoto")?.addEventListener(
            "click",
            batalkanCrop
        );

        $("#btnBatalFotoFooter")?.addEventListener(
            "click",
            batalkanCrop
        );

        cropModal?.addEventListener("click", event => {
            if (event.target === cropModal) {
                batalkanCrop();
            }
        });

        /* =================================================
           INITIALIZE CROPPER
        ================================================= */

        function initializeCropper() {
            if (!cropImage || !cropImage.complete) return;
            if (cropperInitializing) return;

            if (!cropImage.naturalWidth) {
                alert("Foto tidak dapat dibaca. Silakan pilih foto lain.");
                batalkanCrop();
                return;
            }

            if (typeof Cropper === "undefined") {
                alert("Komponen Cropper belum tersedia.");
                batalkanCrop();
                return;
            }

            destroyCropper();

            cropperInitializing = true;

            requestAnimationFrame(() => {
                try {
                    if (!activePage || !cropImage.isConnected) {
                        cropperInitializing = false;
                        return;
                    }

                    cropper = new Cropper(cropImage, {
                        aspectRatio: 1,
                        viewMode: 1,
                        dragMode: "move",

                        autoCropArea: 0.9,

                        responsive: true,
                        restore: false,

                        guides: true,
                        center: true,
                        highlight: false,
                        background: false,

                        movable: true,
                        zoomable: true,
                        zoomOnWheel: true,

                        cropBoxMovable: true,
                        cropBoxResizable: true,

                        toggleDragModeOnDblclick: false,

                        minCropBoxWidth: 100,
                        minCropBoxHeight: 100,

                        ready() {
                            cropperInitializing = false;
                            refreshIcons();
                        }
                    });

                } catch (error) {
                    console.error("[Biodata] Cropper error:", error);

                    cropperInitializing = false;

                    alert("Gagal membuka editor foto.");

                    batalkanCrop();
                }
            });
        }

        /* =================================================
           FILE VALIDATION & READER
        ================================================= */

        fileInput?.addEventListener("change", event => {
            const file = event.target.files?.[0];

            if (!file) return;

            const allowedTypes = [
                "image/jpeg",
                "image/png",
                "image/webp"
            ];

            if (!allowedTypes.includes(file.type)) {
                alert("Gunakan foto berformat JPG, PNG, atau WEBP.");
                fileInput.value = "";
                return;
            }

            if (file.size > 5 * 1024 * 1024) {
                alert("Ukuran foto maksimal 5 MB.");
                fileInput.value = "";
                return;
            }

            if (typeof Cropper === "undefined") {
                alert("Komponen Cropper belum tersedia. Muat ulang halaman.");
                fileInput.value = "";
                return;
            }

            destroyCropper();

            if (fileReader) {
                try {
                    fileReader.abort();
                } catch (_) {}
            }

            fileReader = new FileReader();

            fileReader.onload = () => {
                if (!activePage || !cropImage) return;

                bukaModal(cropModal);

                cropImage.onload = () => {
                    initializeCropper();
                };

                cropImage.onerror = () => {
                    alert("Gagal membaca gambar. Silakan pilih foto lain.");
                    batalkanCrop();
                };

                cropImage.src = fileReader.result;
            };

            fileReader.onerror = () => {
                alert("Foto gagal dibaca. Silakan pilih foto lain.");

                if (fileInput) {
                    fileInput.value = "";
                }
            };

            fileReader.readAsDataURL(file);
        });

        /* =================================================
           SAVE CROPPED PHOTO
        ================================================= */

        btnSimpanFoto?.addEventListener("click", () => {
            if (!cropper || !fotoData || !formUploadFoto) {
                alert("Editor foto belum siap.");
                return;
            }

            try {
                const canvas = cropper.getCroppedCanvas({
                    width: 400,
                    height: 400,
                    minWidth: 400,
                    minHeight: 400,
                    maxWidth: 800,
                    maxHeight: 800,
                    imageSmoothingEnabled: true,
                    imageSmoothingQuality: "high"
                });

                if (!canvas) {
                    throw new Error("Canvas tidak tersedia.");
                }

                fotoData.value = canvas.toDataURL(
                    "image/jpeg",
                    0.9
                );

                btnSimpanFoto.disabled = true;

                btnSimpanFoto.innerHTML = `
                    <i data-lucide="loader-circle"></i>
                    Menyimpan...
                `;

                refreshIcons();

                formUploadFoto.submit();

            } catch (error) {
                console.error("[Biodata] Photo processing:", error);

                alert("Foto gagal diproses. Silakan coba kembali.");

                btnSimpanFoto.disabled = false;

                btnSimpanFoto.innerHTML = `
                    <i data-lucide="check-circle-2"></i>
                    Simpan Foto
                `;

                refreshIcons();
            }
        });

        /* =================================================
           EDIT BIODATA MODAL
        ================================================= */

        function bukaEditBiodata(event) {
            event?.preventDefault();

            if (!editModal) {
                console.error(
                    "[Biodata] #editModal tidak ditemukan. Periksa HTML."
                );

                return;
            }

            bukaModal(editModal);

            // Fokus ke input nama setelah modal dibuka.
            requestAnimationFrame(() => {
                const inputNama = $("#edit_nama", editModal);

                inputNama?.focus({
                    preventScroll: true
                });
            });
        }

        function tutupEditBiodata() {
            tutupModal(editModal);
        }

        btnEdit?.addEventListener(
            "click",
            bukaEditBiodata
        );

        $("#btnBatalEdit")?.addEventListener(
            "click",
            tutupEditBiodata
        );

        $("#btnBatalEditFooter")?.addEventListener(
            "click",
            tutupEditBiodata
        );

        editModal?.addEventListener("click", event => {
            if (event.target === editModal) {
                tutupEditBiodata();
            }
        });

        /* =================================================
           VALIDATION NIK
        ================================================= */

        const inputNIK = $("#edit_nik", editModal || document);

        inputNIK?.addEventListener("input", () => {
            inputNIK.value = inputNIK.value
                .replace(/\D/g, "")
                .slice(0, 16);
        });

        /* =================================================
           VALIDATION EMAIL
        ================================================= */

        const inputEmail = $("#email", editModal || document);

        inputEmail?.addEventListener("blur", () => {
            inputEmail.value = inputEmail.value.trim();
        });

        /* =================================================
        SUBMIT EDIT BIODATA
        ================================================= */

        formEdit?.addEventListener("submit", event => {
            if (!formEdit.checkValidity()) {
                event.preventDefault();
                formEdit.reportValidity();
                return;
            }

            const nama = $("#edit_nama", formEdit)?.value.trim();
            const jenisKelamin = $("#edit_jenis_kelamin", formEdit)?.value;

            if (!nama) {
                event.preventDefault();
                alert("Nama lengkap wajib diisi.");
                $("#edit_nama", formEdit)?.focus();
                return;
            }

            if (!jenisKelamin) {
                event.preventDefault();
                alert("Silakan pilih jenis kelamin.");
                $("#edit_jenis_kelamin", formEdit)?.focus();
                return;
            }

            // Data kepegawaian tidak divalidasi atau diubah oleh guru.
            // Jabatan, status, tugas tambahan, dan sertifikasi
            // sepenuhnya dikelola Admin Utama.

            if (btnSimpanBiodata) {
                btnSimpanBiodata.disabled = true;

                btnSimpanBiodata.innerHTML = `
                    <i data-lucide="loader-circle"></i>
                    Menyimpan...
                `;

                refreshIcons();
            }
        });

        console.log("[SMPU] Biodata berhasil diinisialisasi.");
    }

    /* =====================================================
       GLOBAL KEYBOARD
    ===================================================== */

    document.addEventListener("keydown", event => {
        if (event.key !== "Escape") return;

        const activeModals = getActiveModals();

        if (!activeModals.length) return;

        const topModal = activeModals[activeModals.length - 1];

        if (topModal.id === "cropModal") {
            destroyCropper();

            tutupModal(topModal);

            const fileInput = $("#fileInput");

            if (fileInput) {
                fileInput.value = "";
            }

            resetCropImage();

            return;
        }

        tutupModal(topModal);
    });

    /* =====================================================
       SPA LIFECYCLE
    ===================================================== */

    document.addEventListener(
        "spa:before-page-unload",
        cleanupBiodata
    );

    document.addEventListener(
        "spa:page-loaded",
        initBiodata
    );

    /* =====================================================
       FIRST LOAD
    ===================================================== */

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initBiodata,
            { once: true }
        );
    } else {
        initBiodata();
    }

})();
