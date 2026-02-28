# 📡 Sistem Monitoring Spektrum Frekuensi Radio

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-Web%20App-lightgrey?logo=flask)
![GnuRadio](https://img.shields.io/badge/GnuRadio-SDR-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

Aplikasi web berbasis **Flask** untuk monitoring spektrum frekuensi radio secara real-time menggunakan perangkat **Software Defined Radio (SDR)**. Sistem ini dikembangkan sebagai proyek akhir oleh **Kelompok 3 - TEB 2023**, Politeknik Negeri Sriwijaya (Polsri), dalam kerja sama dengan **Balai Monitor Spektrum Frekuensi Radio Kelas I Palembang**.

---

## 🧠 Tentang Proyek Ini

Sistem ini memungkinkan pemantauan spektrum frekuensi radio secara digital menggunakan perangkat RTL-SDR atau HackRF. Data yang ditangkap diolah secara real-time dan ditampilkan melalui antarmuka web yang informatif, dilengkapi dengan peta lokasi GPS.

Tujuan utama sistem ini adalah membantu petugas monitoring frekuensi radio untuk:
- Mendeteksi sinyal radio aktif di berbagai pita frekuensi
- Memantau komunikasi airband (Pilot & ATC) di rentang 118–137 MHz
- Melacak posisi perangkat monitoring secara real-time menggunakan GPS

---

## ✨ Fitur Utama

| Fitur | Keterangan |
|-------|-----------|
| 📻 Monitoring GNU Radio | Scanning pita frekuensi lebar menggunakan RTL-SDR/HackRF |
| 🛩️ Monitoring Airband | Monitoring komunikasi Pilot & ATC (118–137 MHz, AM) |
| 🗺️ Peta GPS Real-time | Tampilan lokasi monitoring menggunakan Folium (OpenStreetMap) |
| 📊 Grafik Occupancy & PSD | Visualisasi tingkat kepadatan dan power spectral density |
| 🔄 Live Data | Update data otomatis tanpa refresh halaman |
| 🖥️ Dashboard Terintegrasi | Satu antarmuka untuk semua fitur monitoring |

---

## 🗂️ Struktur Folder

```
Program_Web/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── templates/              # HTML templates utama
│   ├── index.html          # Halaman utama / menu
│   ├── sdr.html            # Dashboard GNU Radio + Peta
│   ├── airband.html        # Halaman Monitoring Airband
│   ├── peta.html           # Peta GPS fullscreen
│   └── occupancy.html      # Grafik Occupancy & PSD
├── static/                 # Asset statis (CSS, gambar)
│   ├── css/style.css
│   └── img/
├── gps_flask/
│   └── baca_gps.py         # Script pembaca GPS (serial/simulasi)
└── monitorgnu/
    ├── gnu_multi.py        # Script scanning multi-frekuensi
    ├── RTL_SDR_rcv.py      # Script single frekuensi (FM)
    ├── default.py          # Script airband AM
    └── *.grc               # GnuRadio flowgraph files
```

---

## ⚙️ Persyaratan Sistem

### Hardware
- Perangkat SDR: **RTL-SDR** atau **HackRF One**
- (Opsional) Modul **GPS USB** untuk tracking lokasi real

### Software
- Python 3.10+
- GnuRadio 3.10+
- Driver RTL-SDR atau HackRF

---

## 🚀 Cara Menjalankan

### 1. Clone Repository

```bash
git clone https://github.com/AlifFauzan21/radio-spectrum-monitor.git
cd radio-spectrum-monitor
```

### 2. Install Dependencies Python

```bash
pip install flask folium
```

> **Catatan:** Jika menggunakan sistem berbasis Debian/Ubuntu yang memblokir pip global, gunakan:
> ```bash
> pip install flask folium --break-system-packages
> ```
> Atau install via package manager:
> ```bash
> sudo apt install python3-flask python3-folium
> ```

### 3. Install GnuRadio (jika belum)

```bash
sudo apt update
sudo apt install gnuradio
```

Untuk RTL-SDR:
```bash
sudo apt install gr-osmosdr rtl-sdr
```

### 4. Jalankan Aplikasi Web

```bash
python3 app.py
```

Aplikasi akan berjalan di: **http://127.0.0.1:5000**

---

## 🖥️ Panduan Penggunaan

### Halaman Utama
Terdapat 3 menu utama:
- **Monitoring GNU Radio** → Dashboard SDR + peta GPS
- **Monitoring Airband** → Monitoring komunikasi pesawat
- **GPS** → Peta lokasi fullscreen

### Monitoring GNU Radio (`/run-gnuradio`)
1. Klik **Monitoring GNU Radio** dari menu utama
2. Dashboard akan menampilkan peta lokasi GPS saat ini
3. Pilih mode monitoring:
   - **Scanning Pita Frekuensi** → Jalankan `gnu_multi.py` (scan multi-band)
   - **Monitoring Single Frekuensi (FM)** → Jalankan `RTL_SDR_rcv.py`
   - **Monitoring Airband** → Arahkan ke halaman airband
   - **Grafik Occupancy & PSD** → Tampilkan grafik analisis

### Monitoring Airband (`/airband`)
1. Klik **Mulai Monitoring** untuk memulai penerimaan sinyal AM 118–137 MHz
2. Status akan berubah menjadi **RUNNING**
3. Klik **Stop** untuk menghentikan

### GPS (`/gps`)
- Menampilkan peta fullscreen dengan posisi perangkat
- **Marker Biru** = Data GPS Hardware Asli
- **Marker Merah** = Mode Simulasi
- Koordinat, kecepatan, dan status ditampilkan di pojok kiri atas

---

## 🔌 Konfigurasi Path (app.py)

Jika path folder berbeda di sistem kamu, sesuaikan di bagian ini dalam `app.py`:

```python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SDR_FOLDER  = os.path.join(BASE_DIR, 'monitorgnu')
GPS_FOLDER  = os.path.join(BASE_DIR, 'gps_flask')
```

---

## 📡 Frekuensi yang Didukung

| Band | Rentang | Mode |
|------|---------|------|
| FM Broadcast | 88 – 108 MHz | FM |
| Airband (Pilot & ATC) | 118 – 137 MHz | AM |
| VHF High | 174 – 230 MHz | FM |
| UHF | 300 – 960 MHz | FM |
| L-Band | Hingga 2400 MHz | FM |

---

## 👥 Tim Pengembang

**Kelompok 3 - TEB 2023**  
Program Studi Teknik Elektronika  
**Politeknik Negeri Sriwijaya (Polsri)**  

Proyek ini dikembangkan dalam rangka kerja sama dengan:  
**Balai Monitor Spektrum Frekuensi Radio Kelas I Palembang**

---

## 📄 Lisensi

Proyek ini dibuat untuk keperluan akademis dan pendidikan.  
© TEB2023 Kelas 5 TEB - Polsri. All rights reserved.
