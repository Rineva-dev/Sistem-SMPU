
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

    function angkaDariRupiah(value) {
        return Number(
            String(value).replace(/\D/g, "")
        ) || 0;
    }

    function formatInputRupiah(value) {
        const angka = angkaDariRupiah(value);

        if (angka === 0) return "";

        return "Rp " + angka.toLocaleString("id-ID");
    }

    function getMetode() {
        return methodInputs.find(input => input.checked)?.value || "";
    }

    function updateSummary() {
        const selected = checkboxes.filter(item => item.checked);
        let total = 0;

        // Atur input nominal Pembangunan
        document.querySelectorAll(".nominal-pembangunan").forEach(input => {
            const billItem = input.closest(".bill-item");
            const checkbox = billItem?.querySelector(".bill-checkbox");
            const wrapper = input.closest(".partial-payment-input");

            const isSelected = checkbox?.checked === true;

            // Input hanya aktif jika tagihan dipilih
            input.disabled = !isSelected;

            if (wrapper) {
                wrapper.hidden = !isSelected;
            }

            // Format nominal saat pertama kali ditampilkan
            if (isSelected) {
                const nominal = angkaDariRupiah(input.value);

                input.value = nominal > 0
                    ? nominal.toLocaleString("id-ID")
                    : "";
            }

            // Pastikan nominal tidak melebihi sisa tagihan
            const maksimal = Number(input.dataset.remaining) || 0;
            let nominal = Number(input.value) || 0;

            if (nominal > maksimal) {
                nominal = maksimal;
                input.value = maksimal;
            }
        });

        // Hitung total berdasarkan tagihan yang dipilih
        selected.forEach(item => {
            const sisa = Math.max(
                0,
                Number(item.dataset.remaining) || 0
            );

            const billItem = item.closest(".bill-item");
            const inputNominal = billItem?.querySelector(
                ".nominal-pembangunan"
            );

            if (inputNominal) {
                // Pembangunan menggunakan nominal yang diinput
                let nominal = angkaDariRupiah(inputNominal.value);

                nominal = Math.max(0, Math.min(nominal, sisa));

                total += nominal;
            } else {
                // Tagihan lainnya tetap membayar seluruh sisa tagihan
                total += sisa;
            }
        });

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
            checkoutButton.disabled =
                selected.length === 0 || !metode;
        }

        document.querySelectorAll(".method-card").forEach(card => {
            const radio = card.querySelector('input[name="metode"]');

            card.classList.toggle(
                "selected",
                Boolean(radio?.checked)
            );
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

    document.querySelectorAll(".nominal-pembangunan").forEach(input => {

        // Format nominal ketika pengguna mengetik
        input.addEventListener("input", () => {
            const maksimal = Number(input.dataset.remaining) || 0;

            let nominal = angkaDariRupiah(input.value);

            if (nominal > maksimal) {
                nominal = maksimal;
            }

            input.value = nominal > 0
                ? "Rp " + nominal.toLocaleString("id-ID")
                : "";

            updateSummary();
        });

        // Validasi ketika pengguna selesai mengisi
        input.addEventListener("change", () => {
            const maksimal = Number(input.dataset.remaining) || 0;
            let nominal = angkaDariRupiah(input.value);

            if (nominal < 1) {
                nominal = 1;
            }

            if (nominal > maksimal) {
                nominal = maksimal;
            }

            input.value = "Rp " + nominal.toLocaleString("id-ID");

            updateSummary();
        });
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
