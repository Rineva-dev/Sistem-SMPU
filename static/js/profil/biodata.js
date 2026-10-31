
document.addEventListener("DOMContentLoaded", () => {
    if (window.lucide) {
        lucide.createIcons();
    }
    
    const $ = (selector) => document.querySelector(selector);

    // =====================================================
    // ELEMENTS
    // =====================================================

    const avatarWrapper = $("#avatarWrapper");
    const btnGantiFoto = $("#btnGantiFoto");
    const fileInput = $("#fileInput");

    const viewModal = $("#viewModal");
    const viewFoto = $("#viewFoto");
    const btnTutupFoto = $("#btnTutupFoto");

    const cropModal = $("#cropModal");
    const cropImage = $("#cropImage");
    const btnBatalFoto = $("#btnBatalFoto");
    const btnBatalFotoFooter = $("#btnBatalFotoFooter");
    const btnSimpanFoto = $("#btnSimpanFoto");

    const fotoData = $("#fotoData");
    const formUploadFoto = $("#formUploadFoto");

    const editModal = $("#editModal");
    const btnEdit = $("#btnEdit");
    const btnBatalEdit = $("#btnBatalEdit");
    const btnBatalEditFooter = $("#btnBatalEditFooter");

    let cropper = null;

    // =====================================================
    // HELPER MODAL
    // =====================================================

    function bukaModal(modal) {
        if (!modal) return;

        modal.classList.add("active");
        document.body.style.overflow = "hidden";
    }

    function tutupModal(modal) {
        if (!modal) return;

        modal.classList.remove("active");

        const modalMasihTerbuka = document.querySelector(
            ".modal-overlay.active, .view-modal.active"
        );

        if (!modalMasihTerbuka) {
            document.body.style.overflow = "";
        }
    }

    // =====================================================
    // VIEW PHOTO
    // =====================================================

    function tampilkanFotoBesar() {
        if (!avatarWrapper || !viewModal || !viewFoto) return;

        const foto = avatarWrapper.querySelector("img");

        if (!foto || !foto.src) return;

        viewFoto.src = foto.src;
        bukaModal(viewModal);
    }

    avatarWrapper?.addEventListener("click", tampilkanFotoBesar);

    btnTutupFoto?.addEventListener("click", () => {
        tutupModal(viewModal);
    });

    viewModal?.addEventListener("click", (event) => {
        if (event.target === viewModal) {
            tutupModal(viewModal);
        }
    });

    // =====================================================
    // UPLOAD & CROP PHOTO
    // =====================================================

    btnGantiFoto?.addEventListener("click", (event) => {
        event.stopPropagation();
        fileInput?.click();
    });

    fileInput?.addEventListener("change", (event) => {
        const file = event.target.files?.[0];

        if (!file) return;

        if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
            alert("Gunakan foto berformat JPG, PNG, atau WEBP.");
            fileInput.value = "";
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            alert("Ukuran foto maksimal 5 MB.");
            fileInput.value = "";
            return;
        }

        const reader = new FileReader();

        reader.onload = () => {
            cropImage.src = reader.result;

            bukaModal(cropModal);

            cropImage.onload = () => {
                if (cropper) {
                    cropper.destroy();
                    cropper = null;
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
                    toggleDragModeOnDblclick: false
                });
            };
        };

        reader.readAsDataURL(file);
    });

    function batalkanCrop() {
        if (cropper) {
            cropper.destroy();
            cropper = null;
        }

        tutupModal(cropModal);

        if (fileInput) {
            fileInput.value = "";
        }
    }

    btnBatalFoto?.addEventListener("click", batalkanCrop);
    btnBatalFotoFooter?.addEventListener("click", batalkanCrop);

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

        fotoData.value = canvas.toDataURL("image/jpeg", 0.9);

        btnSimpanFoto.disabled = true;
        btnSimpanFoto.innerHTML = '<i data-lucide="loader-circle"></i> Menyimpan...';

        formUploadFoto.submit();
    });

    // =====================================================
    // EDIT BIODATA
    // =====================================================

    btnEdit?.addEventListener("click", () => {
        bukaModal(editModal);
    });

    function tutupEdit() {
        tutupModal(editModal);
    }

    btnBatalEdit?.addEventListener("click", tutupEdit);
    btnBatalEditFooter?.addEventListener("click", tutupEdit);

    editModal?.addEventListener("click", (event) => {
        if (event.target === editModal) {
            tutupEdit();
        }
    });

    // =====================================================
    // ESCAPE KEY
    // =====================================================

    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") return;

        if (cropModal?.classList.contains("active")) {
            batalkanCrop();
        } else if (editModal?.classList.contains("active")) {
            tutupEdit();
        } else if (viewModal?.classList.contains("active")) {
            tutupModal(viewModal);
        }
    });

    
    /* =========================================================
    MODAL PREMIUM — FOOTER PHOTO BUTTON
    ========================================================= */

    // Tombol Tutup pada footer pratinjau foto
    document.getElementById('btnTutupFotoFooter')?.addEventListener('click', function () {
        document.getElementById('btnTutupFoto')?.click();
    });

    // Refresh Lucide untuk ikon pada modal yang baru dibuka
    function refreshBiodataModalIcons() {
        if (window.lucide?.createIcons) {
            window.lucide.createIcons();
        }
    }


});
