
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("paymentForm");
    if (!form) return;

    const checkboxes = [...document.querySelectorAll(".bill-checkbox")];
    const selectAll = document.getElementById("selectAll");
    const methodInputs = [...document.querySelectorAll('input[name="metode"]')];

    const selectedCount = document.getElementById("selectedCount");
    const selectedMethod = document.getElementById("selectedMethod");
    const totalAmount = document.getElementById("totalAmount");
    const checkoutButton = document.getElementById("checkoutButton");

    const methodInstructions = document.getElementById("methodInstructions");
    const instructionTitle = document.getElementById("instructionTitle");
    const instructionText = document.getElementById("instructionText");
    const instructionNoticeText = document.getElementById("instructionNoticeText");

    const cancelButton = document.getElementById("cancelPaymentButton");

    const detailUrl = document.querySelector(".back-link")?.href;

    const rupiah = (nominal) =>
        new Intl.NumberFormat("id-ID", {
            style: "currency",
            currency: "IDR",
            maximumFractionDigits: 0
        }).format(nominal);

    const metodeInfo = {
        "Transfer Bank": {
            title: "Transfer Bank",
            description:
                "Rekening sementara: 123456789. Pastikan nama bank dan pemilik rekening telah dikonfirmasi sekolah sebelum transfer.",
            notice:
                "Pengajuan akan menunggu verifikasi petugas. Status tidak otomatis menjadi lunas setelah formulir dikirim."
        },
        "VA": {
            title: "Virtual Account",
            description:
                "Nomor Virtual Account akan diberikan setelah integrasi penyedia pembayaran tersedia.",
            notice:
                "Status akan Menunggu Pembayaran sampai penyedia pembayaran mengonfirmasi transaksi. Jika batas waktu berakhir, buat transaksi VA baru."
        },
        "QRIS": {
            title: "QRIS",
            description:
                "Kode QR pembayaran resmi akan ditampilkan setelah integrasi penyedia pembayaran tersedia.",
            notice:
                "Status akan Menunggu Pembayaran sampai penyedia pembayaran mengonfirmasi transaksi. Jika batas waktu berakhir, buat transaksi QRIS baru."
        }
    };

    function getMetode() {
        return methodInputs.find(input => input.checked)?.value || "";
    }

    function updateSummary() {
        const selected = checkboxes.filter(item => item.checked);

        const total = selected.reduce((sum, item) => {
            return sum + Math.max(0, Number(item.dataset.remaining) || 0);
        }, 0);

        selectedCount.textContent = `${selected.length} tagihan`;
        totalAmount.textContent = rupiah(total);

        const metode = getMetode();
        selectedMethod.textContent = metode || "Belum dipilih";

        if (selectAll) {
            selectAll.checked =
                checkboxes.length > 0 &&
                checkboxes.every(item => item.checked);

            selectAll.indeterminate =
                selected.length > 0 &&
                selected.length < checkboxes.length;
        }

        if (checkoutButton) {
            checkoutButton.disabled = selected.length === 0 || !metode;
        }

        document.querySelectorAll(".method-card").forEach(card => {
            const radio = card.querySelector('input[name="metode"]');
            card.classList.toggle("selected", Boolean(radio?.checked));
        });
    }

    function updateMethodInstructions() {
        const metode = getMetode();
        const info = metodeInfo[metode];

        if (!methodInstructions) return;

        methodInstructions.hidden = !info;

        if (!info) return;

        instructionTitle.textContent = info.title;
        instructionText.textContent = info.description;
        instructionNoticeText.textContent = info.notice;

        updateSummary();
    }

    checkboxes.forEach(checkbox => {
        checkbox.addEventListener("change", updateSummary);
    });

    selectAll?.addEventListener("change", () => {
        checkboxes.forEach(checkbox => {
            checkbox.checked = selectAll.checked;
        });

        updateSummary();
    });

    methodInputs.forEach(input => {
        input.addEventListener("change", updateMethodInstructions);
    });

    cancelButton?.addEventListener("click", () => {
        if (detailUrl) {
            window.location.href = detailUrl;
        }
    });

    
    form.addEventListener("submit", event => {
        const selected = checkboxes.filter(item => item.checked);
        const metode = getMetode();

        if (selected.length === 0) {
            event.preventDefault();
            alert("Pilih minimal satu tagihan terlebih dahulu.");
            return;
        }

        if (!metode) {
            event.preventDefault();
            alert("Pilih metode pembayaran terlebih dahulu.");
            return;
        }

        if (metode === "VA" || metode === "QRIS") {
            const namaMetode = metode === "VA"
                ? "Virtual Account"
                : "QRIS";

            const lanjut = confirm(
                namaMetode + " masih dalam mode simulasi dan belum bisa " +
                "digunakan untuk membayar secara nyata. Buat transaksi simulasi?"
            );

            if (!lanjut) {
                event.preventDefault();
                return;
            }
        }

        if (checkoutButton) {
            checkoutButton.disabled = true;
            checkoutButton.querySelector("span").textContent =
                "Memproses transaksi...";
        }

        // Jangan panggil preventDefault di sini.
        // Form akan dikirim ke server untuk divalidasi kembali.
    });


    updateMethodInstructions();
    updateSummary();
});
