document.addEventListener('DOMContentLoaded', function() {
    // Ambil semua elemen
    const btnDaftar = document.getElementById('btnTampilanDaftar');
    const btnKalender = document.getElementById('btnTampilanKalender');
    const tampilanDaftar = document.getElementById('tampilanDaftar');
    const tampilanKalender = document.getElementById('tampilanKalender');
    let kalender = null;

    // Fungsi ganti tampilan DAFTAR
    btnDaftar.addEventListener('click', function() {
        btnDaftar.classList.add('active');
        btnKalender.classList.remove('active');
        tampilanDaftar.classList.remove('d-none');
        tampilanKalender.classList.add('d-none');
    });

    // Fungsi ganti tampilan KALENDER
    btnKalender.addEventListener('click', function() {
        btnKalender.classList.add('active');
        btnDaftar.classList.remove('active');
        tampilanKalender.classList.remove('d-none');
        tampilanDaftar.classList.add('d-none');

        // Inisialisasi kalender jika belum ada
        if (!kalender) {
            initKalender();
        } else {
            kalender.updateSize();
        }
    });

    // Fungsi buat kalender
    function initKalender() {
        const kalenderEl = document.getElementById('kalenderKegiatan');
        if (!kalenderEl) return;

        // Pastikan data aman dan terdefinisi
        const data = Array.isArray(window.agendaData) ? window.agendaData : [];

        // Proses data dengan validasi format tanggal
        const events = data.map(item => {
            // Cek apakah tanggal mulai valid
            const waktuMulai = new Date(item.start);
            if (isNaN(waktuMulai.getTime())) {
                console.warn('Tanggal mulai tidak valid, dilewati:', item);
                return null;
            }

            // Cek juga tanggal selesai jika ada
            let waktuSelesai = null;
            if (item.end) {
                waktuSelesai = new Date(item.end);
                if (isNaN(waktuSelesai.getTime())) {
                    console.warn('Tanggal selesai tidak valid, gunakan tanggal mulai:', item);
                    item.end = item.start;
                }
            }

            // Format jam menjadi HH.MM
            const jam = waktuMulai.toLocaleTimeString('id-ID', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            }).replace(':', '.');

            return {
                id: item.id,
                title: item.title,
                start: item.start,
                end: item.end || item.start,
                className: item.status ? item.status.toLowerCase() : 'terjadwal',
                extendedProps: {
                    waktu: jam,
                    lokasi: item.lokasi || '-',
                    pj: item.pj || '-'
                }
            };
        }).filter(Boolean); // Hapus data yang tidak valid

        kalender = new FullCalendar.Calendar(kalenderEl, {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            locale: 'id',
            events: events,
            height: 'auto',
            // Tampilkan jam dan judul kegiatan
            eventContent: function(arg) {
                const waktu = arg.event.extendedProps.waktu || '';
                const judul = arg.event.title;
                return {
                    html: `<div class="fc-event-time">${waktu}</div>
                           <div class="fc-event-title">${judul}</div>`
                };
            },
            // Tampilkan detail saat diklik
            eventClick: function(info) {
                const kegiatan = info.event;
                const mulai = new Date(kegiatan.start).toLocaleString('id-ID', {
                    day: '2-digit', month: 'long', year: 'numeric',
                    hour: '2-digit', minute: '2-digit'
                });
                const selesai = kegiatan.end ? new Date(kegiatan.end).toLocaleString('id-ID', {
                    day: '2-digit', month: 'long', year: 'numeric',
                    hour: '2-digit', minute: '2-digit'
                }) : '-';

                const statusMap = {
                    terjadwal: 'Terjadwal',
                    berlangsung: 'Berlangsung',
                    selesai: 'Selesai',
                    dibatalkan: 'Dibatalkan'
                };
                const status = statusMap[kegiatan.classNames[0]] || 'Tidak diketahui';

                let detail = `
                    <hr class="my-3">
                    <div class="detail-row">
                        <div class="detail-label"><i class="fa fa-calendar"></i> Agenda</div>
                        <div class="detail-separator">:</div>
                        <div class="detail-value"><strong>${kegiatan.title}</strong></div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label"><i class="fa fa-clock"></i> Mulai</div>
                        <div class="detail-separator">:</div>
                        <div class="detail-value">${mulai}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label"><i class="fa fa-clock"></i> Selesai</div>
                        <div class="detail-separator">:</div>
                        <div class="detail-value">${selesai}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label"><i class="fa fa-map-marker"></i> Lokasi</div>
                        <div class="detail-separator">:</div>
                        <div class="detail-value">${kegiatan.extendedProps.lokasi}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label"><i class="fa fa-user"></i> Penanggung Jawab</div>
                        <div class="detail-separator">:</div>
                        <div class="detail-value">${kegiatan.extendedProps.pj}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label"><i class="fa fa-info-circle"></i> Status</div>
                        <div class="detail-separator">:</div>
                        <div class="detail-value">
                            <span class="badge bg-${
                                kegiatan.classNames[0] === 'terjadwal' ? 'primary' :
                                kegiatan.classNames[0] === 'berlangsung' ? 'success' :
                                kegiatan.classNames[0] === 'selesai' ? 'secondary' : 'danger'
                            } w-100 text-center py-1">${status}</span>
                        </div>
                    </div>
                `;

                if (window.userRole === 'Kepala Sekolah') {
                    detail += `
                        <hr class="my-4">
                        <a href="/agenda/edit/${kegiatan.id}" class="btn btn-primary w-100 py-2">
                            <i class="fa fa-pencil"></i> Edit Agenda
                        </a>
                    `;
                }

                const modal = document.createElement('div');
                modal.style.cssText = `
                    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                    background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center;
                    z-index: 9999; padding: 1rem;
                `;
                modal.innerHTML = `
                    <div style="background: white; padding: 1.5rem; border-radius: 8px; max-width: 550px; width: 100%;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                            <h4 style="margin:0; font-weight:700; color:#1e293b;">Detail Kegiatan</h4>
                            <button onclick="this.closest('.modal-overlay').remove()" style="border:none; background:none; font-size:1.5rem; cursor:pointer; color:#64748b; line-height:1;">&times;</button>
                        </div>
                        <div class="modal-body-custom">${detail}</div>
                    </div>
                `;
                modal.classList.add('modal-overlay');
                modal.addEventListener('click', e => { if (e.target === modal) modal.remove(); });
                document.body.appendChild(modal);
            }
        });

        kalender.render();
    }
});