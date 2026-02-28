import signal
import subprocess
import sys
import time
import os
import glob

from flask import Flask, render_template, redirect, url_for, jsonify
import folium

app = Flask(__name__)

# --- KONFIGURASI PATH (JALUR FOLDER) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Folder Radio (SDR)
SDR_FOLDER = os.path.join(BASE_DIR, 'monitorgnu')
SDR_LOG_FILE = os.path.join(SDR_FOLDER, 'sdr_log.csv')

# 2. Folder GPS
GPS_FOLDER = os.path.join(BASE_DIR, 'gps_flask')
GPS_LOG_REAL = os.path.join(GPS_FOLDER, 'gps_log_REAL.txt')
GPS_LOG_SIM  = os.path.join(GPS_FOLDER, 'gps_log_SIMULASI.txt')

# --- VARIABEL GLOBAL PROSES ---
sdr_process = None  # Proses khusus Radio
gps_process = None  # Proses khusus GPS

# --- FUNGSI MANAJEMEN PROSES ---
def stop_process(proc_obj):
    if proc_obj:
        try:
            if sys.platform == 'win32':
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(proc_obj.pid)])
            else:
                os.killpg(os.getpgid(proc_obj.pid), signal.SIGTERM)
        except Exception:
            pass
    return None

def stop_existing_sdr():
    global sdr_process
    sdr_process = stop_process(sdr_process)

# --- FUNGSI JALANKAN RADIO ---
def run_sdr_script(script_name):
    global sdr_process
    stop_existing_sdr() # Matikan radio lama

    script_path = os.path.join(SDR_FOLDER, script_name)
    python_cmd = "python" if sys.platform == 'win32' else "python3"

    if os.path.exists(SDR_LOG_FILE):
        try: os.remove(SDR_LOG_FILE)
        except: pass

    if not os.path.exists(script_path):
        return False, f"Error: File {script_name} tidak ditemukan!"

    try:
        if sys.platform == 'win32':
            sdr_process = subprocess.Popen([python_cmd, script_path], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            sdr_process = subprocess.Popen([python_cmd, script_path], preexec_fn=os.setsid)
        return True, f"Berhasil menjalankan {script_name}"
    except Exception as e:
        return False, str(e)

# --- FUNGSI JALANKAN GPS (OTOMATIS) ---
def start_gps_service():
    global gps_process
    
    if gps_process is not None:
        if gps_process.poll() is None: 
            return # Sudah jalan, jangan jalankan lagi
    
    script_path = os.path.join(GPS_FOLDER, 'baca_gps.py')
    python_cmd = "python" if sys.platform == 'win32' else "python3"
    
    if os.path.exists(script_path):
        try:
            if sys.platform == 'win32':
                gps_process = subprocess.Popen([python_cmd, script_path], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                gps_process = subprocess.Popen([python_cmd, script_path], preexec_fn=os.setsid)
            print("[INFO] Service GPS dimulai otomatis.")
        except Exception as e:
            print(f"[ERROR] Gagal start GPS: {e}")

# --- FUNGSI BANTUAN: BACA DATA GPS TERBARU ---
def get_latest_gps_data():
    """Mencari file log terbaru (Real vs Simulasi) dan mengambil koordinatnya"""
    target_file = None
    ts_real = 0
    ts_sim = 0
    
    if os.path.exists(GPS_LOG_REAL): ts_real = os.path.getmtime(GPS_LOG_REAL)
    if os.path.exists(GPS_LOG_SIM): ts_sim = os.path.getmtime(GPS_LOG_SIM)
        
    icon_color = "gray"
    
    # Logika pilih file terbaru
    if ts_real > ts_sim:
        target_file = GPS_LOG_REAL
        icon_color = "blue" # Biru = Asli
    elif ts_sim > 0:
        target_file = GPS_LOG_SIM
        icon_color = "red"  # Merah = Simulasi
    
    lat, lon = -2.990934, 104.756554 # Default Polsri
    speed = "0"
    
    if target_file and os.path.exists(target_file):
        try:
            with open(target_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    parts = last_line.split('|')
                    if len(parts) >= 4:
                        lat = float(parts[1])
                        lon = float(parts[2])
                        speed = parts[3]
        except: pass
        
    return lat, lon, speed, icon_color

# --- ROUTE WEBSITE ---

@app.route('/')
def index():
    return render_template('index.html')

# --- UPDATE: DASHBOARD RADIO SEKARANG ADA PETANYA ---
@app.route('/run-gnuradio')
def start_gnuradio():
    # 1. Pastikan GPS nyala di background
    start_gps_service() 
    
    # 2. Ambil data lokasi saat ini
    lat, lon, speed, color = get_latest_gps_data()
    
    # 3. Buat Peta Kecil
    m = folium.Map(location=[lat, lon], zoom_start=15)
    folium.Marker(
        [lat, lon], 
        popup=f"Speed: {speed} km/h",
        icon=folium.Icon(color=color, icon='info-sign')
    ).add_to(m)

    # 4. Kirim peta ke sdr.html
    return render_template('sdr.html', map_html=m._repr_html_())

@app.route('/airband')
def start_airband():
    return render_template('airband.html')

@app.route('/occupancy')
def occupancy_dashboard():
    return render_template('occupancy.html')

# --- ROUTE MENU GPS (LAYAR PENUH) ---
@app.route('/gps')
def gps_page():
    start_gps_service()
    
    lat, lon, speed, color = get_latest_gps_data()
    
    status_msg = "Mode: REAL HARDWARE" if color == "blue" else "Mode: SIMULASI"
    
    m = folium.Map(location=[lat, lon], zoom_start=18)
    folium.Marker(
        [lat, lon], 
        popup=f"Speed: {speed} km/h",
        icon=folium.Icon(color=color, icon='info-sign')
    ).add_to(m)

    return render_template(
        'peta.html',
        lat=lat, lon=lon, speed=speed, 
        status_msg=status_msg, 
        map_html=m._repr_html_()
    )

# --- ROUTE KONTROL RADIO ---
@app.route('/start_scanning')
def start_scanning():
    success, msg = run_sdr_script('gnu_multi.py')
    return msg

@app.route('/start_single_mode')
def start_single_mode():
    success, msg = run_sdr_script('RTL_SDR_rcv.py')
    return msg

@app.route('/run-airband-script')
def run_airband_script():
    success, msg = run_sdr_script('default.py')
    return msg

@app.route('/stop-radio')
def stop_radio():
    stop_existing_sdr()
    return redirect(url_for('index'))

# --- ROUTE DATA LIVE ---
@app.route('/get_live_data')
def get_live_data():
    default_data = {'power': -100, 'freq': '0M', 'timestamp': '--:--'}
    try:
        if not os.path.exists(SDR_LOG_FILE): return jsonify(default_data)
        with open(SDR_LOG_FILE, 'r') as f:
            lines = f.readlines()
            if not lines: return jsonify(default_data)
            ts, freq, power = lines[-1].strip().split(',')[:3]
            return jsonify({'timestamp': ts, 'freq': freq, 'power': float(power)})
    except:
        return jsonify(default_data)

if __name__ == '__main__':
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        stop_existing_sdr()
        stop_process(gps_process)
