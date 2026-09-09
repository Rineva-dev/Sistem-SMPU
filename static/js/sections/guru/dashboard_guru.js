document.addEventListener('DOMContentLoaded', function() {
    const btnDaftar = document.getElementById('btnTampilanDaftar');
    const btnKalender = document.getElementById('btnTampilanKalender');
    const tampilanDaftar = document.getElementById('tampilanDaftar');
    const tampilanKalender = document.getElementById('tampilanKalender');
    let kalender = null;

    // Fungsi ganti tampilan
    btnDaftar.addEventListener('click', function() {
        btnDaftar.classList.add('active');
        btnKalender.classList.remove('active');
        tampilanDaftar.classList.remove('d-none');
        tampilanDaftar.classList.add('tampilan-aktif');
        tampilanKalender.classList.add('d-none');
        tampilanKalender.classList.remove('tampilan-aktif');
    });

    btnKalender.addEventListener('click', function() {
        btnKalender.classList.add('active');
        btnDaftar.classList.remove('active');
        tampilanKalender.classList.remove('d-none');
        tampilanKalender.classList.add('tampilan-aktif');
        tampilanDaftar.classList.add('d-none');
        tampilanDaftar.classList.remove('tampilan-aktif');

        // Inisialisasi kalender jika belum ada
        if (!kalender) {
            initKalenderDashboard();
        }
    });

    // ✅ Fungsi utama: Buat modal detail agenda
    function bukaModalDetail(agenda) {
        const mulai = new Date(agenda.tanggal_mulai).toLocaleString('id-ID', {
            day: '2-digit', month: 'long', year: 'numeric',
            hour: '2-digit', minute: '2-digit'
        });

        const selesai = agenda.tanggal_selesai 
            ? new Date(agenda.tanggal_selesai).toLocaleString('id-ID', {
                day: '2-digit', month: 'long', year: 'numeric',
                hour: '2-digit', minute: '2-digit'
              }) 
            : '-';

        const statusMap = {
            'terjadwal': { label: 'Terjadwal', warna: 'primary' },
            'berlangsung': { label: 'Berlangsung', warna: 'success' },
            'selesai': { label: 'Selesai', warna: 'secondary' },
            'dibatalkan': { label: 'Dibatalkan', warna: 'danger' }
        };

        const status = statusMap[agenda.status.toLowerCase().replace(' ', '-')] || { label: 'Tidak diketahui', warna: 'dark' };

        const isiModal = `
            <div class="detail-row">
                <div class="detail-label"><i class="fas fa-calendar-alt"></i> Judul</div>
                <div class="detail-separator">:</div>
                <div class="detail-value"><strong>${agenda.judul}</strong></div>
            </div>
            <div class="detail-row">
                <div class="detail-label"><i class="fas fa-clock"></i> Mulai</div>
                <div class="detail-separator">:</div>
                <div class="detail-value">${mulai}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label"><i class="fas fa-clock"></i> Selesai</div>
                <div class="detail-separator">:</div>
                <div class="detail-value">${selesai}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label"><i class="fas fa-map-marker-alt"></i> Lokasi</div>
                <div class="detail-separator">:</div>
                <div class="detail-value">${agenda.lokasi || '-'}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label"><i class="fas fa-user"></i> Penanggung Jawab</div>
                <div class="detail-separator">:</div>
                <div class="detail-value">${agenda.penanggung_jawab || '-'}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label"><i class="fas fa-info-circle"></i> Status</div>
                <div class="detail-separator">:</div>
                <div class="detail-value">
                    <span class="badge bg-${status.warna} w-100 text-center py-1">${status.label}</span>
                </div>
            </div>
            <hr class="my-3">
            <div class="detail-row">
                <div class="detail-label"><i class="fas fa-file-alt"></i> Deskripsi</div>
                <div class="detail-separator">:</div>
                <div class="detail-value">${agenda.deskripsi || 'Tidak ada keterangan tambahan'}</div>
            </div>
        `;

        // Buat elemen modal
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.style.cssText = `
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.55); display: flex; align-items: center; justify-content: center;
            z-index: 9999; padding: 1rem;
        `;

        modal.innerHTML = `
            <div style="background: #ffffff; border-radius: 1rem; box-shadow: 0 10px 30px rgba(0,0,0,0.2); max-width: 580px; width: 100%; max-height: 90vh; overflow-y: auto;">
                <div style="padding: 1rem 1.75rem; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="margin: 0; font-weight: 600; color: #1e293b; font-size: 1.25rem;">Detail Agenda</h4>
                    <button type="button" onclick="this.closest('.modal-overlay').remove()" style="border: none; background: none; font-size: 1.75rem; line-height: 1; color: #94a3b8; cursor: pointer; padding: 0 0.5rem;">&times;</button>
                </div>
                <div style="padding: 1rem 1.75rem;">
                    ${isiModal}
                </div>
            </div>
        `;

        // Tutup modal jika klik di luar kotak
        modal.addEventListener('click', function(e) {
            if (e.target === modal) modal.remove();
        });

        document.body.appendChild(modal);
    }

    // ✅ Jalankan modal saat klik tombol Detail di daftar
    document.querySelectorAll('.agenda-item .btn-light').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const id = this.getAttribute('href').split('/').pop();
            const agenda = window.agendaData.find(a => a.id == id);
            if (agenda) bukaModalDetail(agenda);
        });
    });

    // ✅ Fungsi buat kalender
    function initKalenderDashboard() {
        const kalenderEl = document.getElementById('kalenderDashboard');
        if (!kalenderEl || !window.agendaData) return;

        const events = window.agendaData.map(item => ({
            id: item.id,
            title: item.judul,
            start: item.tanggal_mulai,
            end: item.tanggal_selesai || item.tanggal_mulai,
            className: item.status ? item.status.toLowerCase().replace(' ', '-') : 'terjadwal',
            extendedProps: {
                lokasi: item.lokasi || '-',
                pj: item.penanggung_jawab || '-',
                deskripsi: item.deskripsi || ''
            }
        }));

        kalender = new FullCalendar.Calendar(kalenderEl, {
            initialView: 'dayGridMonth',
            locale: 'id',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek'
            },
            events: events,
            height: 'auto',
            eventContent: function(arg) {
                const waktu = new Date(arg.event.start).toLocaleTimeString('id-ID', {
                    hour: '2-digit', minute: '2-digit', hour12: false
                });
                return {
                    html: `<div class="fc-event-time">${waktu}</div><div class="fc-event-title">${arg.event.title}</div>`
                };
            },
            // ✅ Klik di kalender juga buka modal
            eventClick: function(info) {
                info.jsEvent.preventDefault();
                const id = info.event.id;
                const agenda = window.agendaData.find(a => a.id == id);
                if (agenda) bukaModalDetail(agenda);
            }
        });

        kalender.render();
    }
});