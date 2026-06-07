# CHANGELOG - Dashboard Nilai & Absensi

## [v3.0.0] - 2025-01-XX

### ✨ Fitur Baru: Kelola Nilai Dinamis

**Tab "Kelola Nilai" (Khusus Guru):**
- ✅ Input nilai baru dengan jenis yang fleksibel (PTS, Latihan Harian, UTS, UAS, Tugas, Praktik)
- ✅ Tambah jenis nilai custom dengan pilih "+ Jenis Baru..." lalu ketik nama sendiri
- ✅ Form input: Pilih kelas → tanggal → jenis nilai → muat daftar siswa → isi nilai 0-100 per siswa → simpan
- ✅ Tabel data nilai tersimpan dengan filter real-time (kelas, jenis, nama siswa)
- ✅ Tombol hapus per baris untuk koreksi data
- ✅ Export semua nilai (PTS dari xlsx + semua jenis dari DB) ke satu file Excel dengan sheet terpisah

**Halaman Siswa:**
- ✅ Tab "PTS" — nilai dari file xlsx seperti sebelumnya
- ✅ Tab "Nilai Lainnya" — nilai latihan, tugas, dll yang diinput guru dengan badge jumlah data
- ✅ Tabel detail per tanggal dengan progress bar dan grade warna

**Database:**
- ✅ Tabel `nilai` baru dengan kolom: id, nama, kelas, jenis, nilai, tanggal, keterangan
- ✅ Constraint UNIQUE(nama, kelas, jenis, tanggal) untuk mencegah duplikasi

---

## [v2.0.0] - 2025-01-XX

### 🔐 Sistem Login & Role Management

**Autentikasi:**
- ✅ Login dengan username & password
- ✅ Role: Guru (akses penuh) dan Siswa (view only)
- ✅ Session management dengan Flask session
- ✅ Akun default guru: `guru` / `guru123`

**Akun Siswa Otomatis:**
- ✅ Generate otomatis dari file xlsx saat startup
- ✅ Username = nama depan (lowercase), password = `siswa123`
- ✅ Handle duplikat nama dengan suffix kelas (contoh: `ridhox`, `ridhoxi`)
- ✅ Total 30 akun siswa dibuat otomatis

**Halaman Siswa:**
- ✅ Dashboard khusus siswa dengan nilai PTS dan absensi diri sendiri
- ✅ Statistik: Nilai, Grade, Peringkat, % Kehadiran
- ✅ Alert otomatis jika kehadiran < 80%
- ✅ Tabel detail absensi per tanggal

**Tab Admin (Khusus Guru):**
- ✅ Manajemen akun: Tambah, hapus, reset password
- ✅ Query database langsung dengan SQL editor
- ✅ Contoh query siap pakai (SELECT, DELETE, dll)
- ✅ Tabel hasil query dengan scroll

**Export Data:**
- ✅ Export nilai PTS ke Excel (semua kelas, sheet terpisah)
- ✅ Export absensi ke Excel dengan pilihan per kelas atau semua
- ✅ Sheet rekap (total Hadir/Sakit/Izin/Alpha + % kehadiran)
- ✅ Sheet detail per tanggal
- ✅ Auto-width kolom untuk readability

---

## [v1.0.0] - 2025-01-XX

### 🎓 Fitur Awal

**Dashboard Nilai PTS:**
- ✅ Load data dari file xlsx (Kelas X, XI, XII)
- ✅ Statistik gabungan: Total siswa, rata-rata gabungan, kelas terbaik
- ✅ Chart perbandingan rata-rata kelas (bar chart)
- ✅ Chart distribusi grade per kelas (doughnut chart)
- ✅ Tabel ranking siswa dengan progress bar nilai
- ✅ Badge grade dengan warna (A=biru, B=hijau, C=kuning, D=merah, E=abu)
- ✅ Icon trophy untuk rank 1-3

**Absensi Siswa:**
- ✅ Input absensi per kelas dengan status: Hadir, Sakit, Izin, Alpha
- ✅ Tombol "Semua Hadir" / "Semua Alpha" untuk isi cepat
- ✅ Rekap hari ini (counter per status)
- ✅ Tabel rekap per siswa (total Hadir/Sakit/Izin/Alpha + % kehadiran)
- ✅ Sub-tab "Detail per Tanggal" dengan tombol edit & hapus
- ✅ Modal edit absensi untuk koreksi data
- ✅ Database SQLite dengan constraint UNIQUE(nama, kelas, tanggal)

**UI/UX:**
- ✅ Design modern dengan gradient navbar
- ✅ Card dengan shadow dan border-radius
- ✅ Responsive layout (mobile-friendly)
- ✅ Bootstrap 5 + Bootstrap Icons
- ✅ Chart.js untuk visualisasi data
- ✅ Flash messages untuk feedback user

---

## 📋 Roadmap

### Planned Features
- [ ] Import nilai dari Excel (bulk upload)
- [ ] Grafik perkembangan nilai per siswa (line chart)
- [ ] Notifikasi email untuk siswa dengan kehadiran rendah
- [ ] Cetak rapor per siswa (PDF)
- [ ] Backup & restore database
- [ ] Dark mode toggle
- [ ] Multi-semester support

---

## 🛠️ Tech Stack

- **Backend:** Flask (Python)
- **Database:** SQLite
- **Frontend:** Bootstrap 5, Chart.js, Bootstrap Icons
- **Data Processing:** Pandas, openpyxl
- **Authentication:** Flask Session

---

## 📝 Notes

- File xlsx nilai PTS harus ada di path yang sudah dikonfigurasi
- Database `absensi.db` dibuat otomatis saat pertama kali run
- Akun siswa di-generate ulang setiap startup (skip jika sudah ada)
- Semua password default bisa direset oleh guru di tab Admin
