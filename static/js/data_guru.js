document.addEventListener('DOMContentLoaded', function() {
    const inputCari = document.getElementById('cariGuru');
    const tabel = document.querySelector('table tbody');

    if (inputCari && tabel) {
        inputCari.addEventListener('input', function() {
            const kataKunci = this.value.toLowerCase();
            const baris = tabel.querySelectorAll('tr');

            baris.forEach(baris => {
                const teks = baris.textContent.toLowerCase();
                baris.style.display = teks.includes(kataKunci) ? '' : 'none';
            });
        });
    }
});