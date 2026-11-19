
(function () {
    function initInputNilaiGuru() {
        const input = document.getElementById('cariPenugasan');
        const container = document.getElementById('daftarPenugasan');
        const hasilKosong = document.getElementById('hasilKosong');

        if (!input || !container || input.dataset.initialized === 'true') {
            return;
        }

        input.dataset.initialized = 'true';

        input.addEventListener('input', function () {
            const keyword = this.value.trim().toLowerCase();
            const cards = container.querySelectorAll('.nilai-assignment-card');

            let jumlahTampil = 0;

            cards.forEach(function (card) {
                const teks = card.dataset.search || '';
                const cocok = teks.includes(keyword);

                card.style.display = cocok ? '' : 'none';

                if (cocok) {
                    jumlahTampil++;
                }
            });

            if (hasilKosong) {
                hasilKosong.hidden = jumlahTampil !== 0;
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initInputNilaiGuru);
    } else {
        initInputNilaiGuru();
    }

    document.addEventListener('spa:page-loaded', initInputNilaiGuru);
})();
