
/* =========================================================
   SMPU - STUDENT IMPORT JAVASCRIPT
   SPA SAFE INITIALIZATION
========================================================= */

(function () {

    function initStudentImport() {

        const uploadPage = document.getElementById("siswaImportPage");

        if (uploadPage && !uploadPage.dataset.initialized) {

            uploadPage.dataset.initialized = "true";

            initUploadPage(uploadPage);

        }


        const previewPage = document.getElementById("siPreviewPage");

        if (previewPage && !previewPage.dataset.initialized) {

            previewPage.dataset.initialized = "true";

            initPreviewPage(previewPage);

        }

    }


    /* =====================================================
       UPLOAD PAGE
    ===================================================== */

    function initUploadPage(root) {

        const form = root.querySelector("#siUploadForm");
        const input = root.querySelector("#siExcelFile");
        const dropzone = root.querySelector("#siDropzone");
        const browseButton = root.querySelector("#siBrowseButton");

        const emptyState = root.querySelector("#siDropzoneEmpty");
        const selectedFile = root.querySelector("#siSelectedFile");

        const fileName = root.querySelector("#siFileName");
        const fileSize = root.querySelector("#siFileSize");

        const removeButton = root.querySelector("#siRemoveFile");
        const previewButton = root.querySelector("#siPreviewButton");

        if (!form || !input || !dropzone) return;

        const MAX_SIZE = 10 * 1024 * 1024;


        function formatSize(bytes) {

            if (bytes < 1024) {
                return bytes + " B";
            }

            if (bytes < 1024 * 1024) {
                return (bytes / 1024).toFixed(1) + " KB";
            }

            return (bytes / (1024 * 1024)).toFixed(2) + " MB";

        }


        function resetFile() {

            input.value = "";

            emptyState.hidden = false;
            selectedFile.hidden = true;

            previewButton.disabled = true;

            dropzone.classList.remove("si-has-file");

        }


        function setFile(file) {

            if (!file) {
                resetFile();
                return;
            }

            const extension = file.name
                .split(".")
                .pop()
                .toLowerCase();

            if (extension !== "xlsx") {

                alert("File harus menggunakan format .xlsx.");

                resetFile();

                return;

            }


            if (file.size > MAX_SIZE) {

                alert("Ukuran file maksimal 10 MB.");

                resetFile();

                return;

            }


            if (file.size === 0) {

                alert("File Excel kosong atau tidak dapat dibaca.");

                resetFile();

                return;

            }


            try {

                const transfer = new DataTransfer();

                transfer.items.add(file);

                input.files = transfer.files;

            } catch (error) {

                alert(
                    "File tidak dapat dipilih. Silakan gunakan tombol pilih file."
                );

                resetFile();

                return;

            }


            fileName.textContent = file.name;
            fileSize.textContent = formatSize(file.size);

            emptyState.hidden = true;
            selectedFile.hidden = false;

            previewButton.disabled = false;

            dropzone.classList.add("si-has-file");

        }


        /* Browse */

        browseButton.addEventListener("click", function (event) {

            event.stopPropagation();

            input.click();

        });


        dropzone.addEventListener("click", function (event) {

            if (
                event.target.closest("#siBrowseButton") ||
                event.target.closest("#siRemoveFile")
            ) {
                return;
            }

            input.click();

        });


        dropzone.addEventListener("keydown", function (event) {

            if (
                event.key === "Enter" ||
                event.key === " "
            ) {

                event.preventDefault();

                input.click();

            }

        });


        input.addEventListener("change", function () {

            const file = input.files[0];

            setFile(file);

        });


        /* Remove file */

        removeButton.addEventListener("click", function (event) {

            event.stopPropagation();

            resetFile();

        });


        /* Drag and Drop */

        ["dragenter", "dragover"].forEach(function (eventName) {

            dropzone.addEventListener(eventName, function (event) {

                event.preventDefault();
                event.stopPropagation();

                dropzone.classList.add("si-dragover");

            });

        });


        ["dragleave", "dragend", "drop"].forEach(function (eventName) {

            dropzone.addEventListener(eventName, function (event) {

                event.preventDefault();
                event.stopPropagation();

                dropzone.classList.remove("si-dragover");

            });

        });


        dropzone.addEventListener("drop", function (event) {

            const files = event.dataTransfer.files;

            if (!files || !files.length) return;

            setFile(files[0]);

        });


        /* Submit */

        form.addEventListener("submit", function (event) {

            if (!input.files || !input.files.length) {

                event.preventDefault();

                alert("Silakan pilih file Excel terlebih dahulu.");

                return;

            }


            const file = input.files[0];

            if (
                !file.name.toLowerCase().endsWith(".xlsx") ||
                file.size > MAX_SIZE
            ) {

                event.preventDefault();

                alert("File tidak memenuhi ketentuan upload.");

                return;

            }


            previewButton.disabled = true;

            previewButton.innerHTML = `
                <i class="fa-solid fa-spinner fa-spin"></i>
                <span>Memeriksa Data Excel...</span>
            `;

        });

    }


    /* =====================================================
       PREVIEW PAGE
    ===================================================== */

    function initPreviewPage(root) {

        const searchInput = root.querySelector("#siValidSearch");
        const table = root.querySelector("#siValidTable");
        const countText = root.querySelector("#siValidCount");

        if (searchInput && table) {

            const rows = Array.from(
                table.querySelectorAll("tbody tr")
            );


            searchInput.addEventListener("input", function () {

                const keyword = this.value
                    .trim()
                    .toLowerCase();

                let visible = 0;

                rows.forEach(function (row) {

                    const content = (
                        row.dataset.search || row.textContent
                    ).toLowerCase();

                    const match = content.includes(keyword);

                    row.style.display = match ? "" : "none";

                    if (match) visible++;

                });


                if (countText) {

                    countText.textContent =
                        "Menampilkan " + visible + " dari " + rows.length + " data";

                }

            });

        }


        /* Confirm import */

        const confirmForm = root.querySelector("#siConfirmForm");

        if (confirmForm) {

            confirmForm.addEventListener("submit", function (event) {

                const confirmed = window.confirm(
                    "Apakah kamu yakin ingin menyimpan data siswa yang valid ke database?"
                );

                if (!confirmed) {

                    event.preventDefault();

                    return;

                }


                const button = confirmForm.querySelector(
                    'button[type="submit"]'
                );

                if (button) {

                    button.disabled = true;

                    button.innerHTML = `
                        <i class="fa-solid fa-spinner fa-spin"></i>
                        <span>Menyimpan Data Siswa...</span>
                    `;

                }

            });

        }

    }


    /* =====================================================
       INITIALIZE
    ===================================================== */

    if (document.readyState === "loading") {

        document.addEventListener(
            "DOMContentLoaded",
            initStudentImport
        );

    } else {

        initStudentImport();

    }


    /*
       Fungsi ini juga dapat dipanggil oleh SPA manager
       setelah konten halaman diganti.
    */

    window.initStudentImport = initStudentImport;

})();
