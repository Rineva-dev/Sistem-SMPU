
/* =========================================================
   SMPU BIODATA
   PREMIUM PROFILE + SPA COMPATIBLE
========================================================= */

(() => {
    "use strict";

    // Hindari pemasangan event global berulang.
    if (window.__smpuBiodataSPARegistered) return;

    window.__smpuBiodataSPARegistered = true;

    let cropper = null;
    let activePage = null;
    let previousBodyOverflow = "";

    // =====================================================
    // HELPER
    // =====================================================

    const $ = (selector, root = document) =>
        root.querySelector(selector);

    function refreshIcons(root = document) {
        if (window.lucide?.createIcons) {
            window.lucide.createIcons({
                attrs: {
                    "stroke-width": 1.8
                }
            });
        }
    }

    function getActiveModal() {
        return document.querySelector(
            ".modal-overlay.active, .view-modal.active"
        );
    }

    function bukaModal(modal) {
        if (!modal) return;

        if (!getActiveModal()) {
            previousBodyOverflow = document.body.style.overflow;
        }

        modal.classList.add("active");
        document.body.style.overflow = "hidden";

        refreshIcons(modal);
    }

    function tutupModal(modal) {
        if (!modal) return;

        modal.classList.remove("active");

        if (!getActiveModal()) {
            document.body.style.overflow = previousBodyOverflow;
        }
    }

    function tutupSemuaModal() {
        document.querySelectorAll(
            ".modal-overlay.active, .view-modal.active"
        ).forEach(modal => {
            modal.classList.remove("active");
        });

        document.body.style.overflow = previousBodyOverflow;
    }

    // =====================================================
    // DESTROY CROPper
    // =====================================================

    function destroyCropper() {
        if (cropper) {
            cropper.destroy();
            cropper = null;
        }
    }

    // =====================================================
    // CLEANUP SEBELUM HALAMAN SPA DIGANTI
    // =====================================================

    function cleanupBiodata() {
        destroyCropper();
        tutupSemuaModal();

        if (activePage) {
            activePage = null;
        }

        const fileInput = $("#fileInput");

        if (fileInput) {
            fileInput.value = "";
        }
    }

    // =====================================================
    // INITIALIZE BIODATA
    // =====================================================

    function initBiodata() {
        const page = $(".biodata-page");

        // Bukan halaman biodata.
        if (!page) return;

        // Hindari inisialisasi dua kali pada halaman yang sama.
        if (activePage === page) return;

        cleanupBiodata();

        activePage = page;

        refreshIcons(page);

        // =================================================
        // ELEMENTS
        // =================================================

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

        // =================================================
        // VIEW PHOTO
        // =================================================

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

        // =================================================
        // UPLOAD PHOTO
        // =================================================

        btnGantiFoto?.addEventListener("click", event => {
            event.preventDefault();
            event.stopPropagation();

            fileInput?.click();
        });

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
                alert("Komponen pemotong foto belum siap. Silakan muat ulang halaman.");
                fileInput.value = "";
                return;
            }

            const reader = new FileReader();

            reader.onload = () => {
                destroyCropper();

                cropImage.src = reader.result;

                bukaModal(cropModal);

                cropImage.onload = () => {
                    destroyCropper();

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
                        toggleDragModeOnDblclick: false
                    });
                };
            };

            reader.onerror = () => {
                alert("Foto gagal dibaca. Silakan pilih foto lain.");
                fileInput.value = "";
            };

            reader.readAsDataURL(file);
        });

        // =================================================
        // CANCEL CROP
        // =================================================

        function batalkanCrop() {
            destroyCropper();

            tutupModal(cropModal);

            if (fileInput) {
                fileInput.value = "";
            }

            if (cropImage) {
                cropImage.onload = null;
                cropImage.removeAttribute("src");
            }
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

        // =================================================
        // SAVE CROPPED PHOTO
        // =================================================

        btnSimpanFoto?.addEventListener("click", () => {
            if (!cropper || !fotoData || !formUploadFoto) return;

            const canvas = cropper.getCroppedCanvas({
                width: 400,
                height: 400,
                imageSmoothingEnabled: true,
                imageSmoothingQuality: "high"
            });

            if (!canvas) {
                alert("Foto tidak dapat diproses. Silakan coba kembali.");
                return;
            }

            try {
                fotoData.value = canvas.toDataURL(
                    "image/jpeg",
                    0.9
                );
            } catch (error) {
                console.error("Gagal memproses foto:", error);
                alert("Foto gagal diproses. Silakan gunakan foto lain.");
                return;
            }

            btnSimpanFoto.disabled = true;

            btnSimpanFoto.innerHTML =
                '<i data-lucide="loader-circle"></i>' +
                '<span>Menyimpan...</span>';

            refreshIcons(btnSimpanFoto);

            formUploadFoto.submit();
        });

        // =================================================
        // EDIT BIODATA
        // =================================================

        btnEdit?.addEventListener("click", () => {
            bukaModal(editModal);
        });

        function tutupEdit() {
            tutupModal(editModal);
        }

        $("#btnBatalEdit")?.addEventListener(
            "click",
            tutupEdit
        );

        $("#btnBatalEditFooter")?.addEventListener(
            "click",
            tutupEdit
        );

        editModal?.addEventListener("click", event => {
            if (event.target === editModal) {
                tutupEdit();
            }
        });

        console.log("[SMPU SPA] Biodata berhasil diinisialisasi.");
    }

    // =====================================================
    // SPA EVENTS
    // =====================================================

    document.addEventListener(
        "spa:before-page-unload",
        cleanupBiodata
    );

    document.addEventListener(
        "spa:page-loaded",
        initBiodata
    );

    // =====================================================
    // ESCAPE KEY
    // =====================================================

    document.addEventListener("keydown", event => {
        if (event.key !== "Escape") return;

        const cropModal = $("#cropModal");

        if (cropModal?.classList.contains("active")) {
            destroyCropper();
            tutupModal(cropModal);

            const fileInput = $("#fileInput");

            if (fileInput) {
                fileInput.value = "";
            }

            const cropImage = $("#cropImage");

            if (cropImage) {
                cropImage.onload = null;
                cropImage.removeAttribute("src");
            }

            return;
        }

        const activeModal = getActiveModal();

        if (activeModal) {
            tutupModal(activeModal);
        }
    });

    // =====================================================
    // INITIAL PAGE LOAD
    // =====================================================

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
