import subprocess
import csv
from datetime import datetime
import threading
import pandas as pd
from flask import Flask, render_template, jsonify, request
# from flask_cors import CORS # <- BARIS INI DIHAPUS
import os
from pathlib import Path
import time
import re

app = Flask(__name__)
# CORS(app) # <- BARIS INI DIHAPUS

# --- PERBAIKAN: Menambahkan header CORS secara manual ---
@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response
# ----------------------------------------------------

# --- Variabel Global ---
params = {"frequency": "87:108", "bandwidth": "50000"}
SYSTEM_STATUS = {"status": "initializing", "message": "Sistem sedang dimulai..."}
SWEEP_INTERVAL_SECONDS = 1.0
DATA_POINT_SAMPLING_RATE = 16
LOGGING_ENABLED = False
CURRENT_LOG_FILE = None
LOGGING_END_TIME = None

restart_event = threading.Event()
sweep_lock = threading.Lock()
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)
Path("static/img").mkdir(parents=True, exist_ok=True)

# ------------------ Web Routes ------------------
@app.route("/")
def dashboard():
    return render_template("index.html", params=params)

@app.route("/status")
def status():
    if LOGGING_ENABLED:
        return jsonify({"status": "recording", "message": f"Merekam: {Path(CURRENT_LOG_FILE).name}"})
    return jsonify(SYSTEM_STATUS)

@app.route("/list-logs")
def list_logs():
    try:
        log_files = sorted([f for f in os.listdir(LOGS_DIR) if f.endswith('.csv')], reverse=True)
        return jsonify(log_files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get-log-data/<string:filename>")
def get_log_data(filename):
    try:
        filepath = LOGS_DIR / filename
        if not filepath.exists(): return jsonify({"error": "File tidak ditemukan"}), 404
        df = pd.read_csv(filepath)
        psd_data = df.groupby("frequency")["power"].mean().reset_index()
        return jsonify({"psd": psd_data.to_dict(orient='records')})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/config", methods=["POST"])
def config():
    global SYSTEM_STATUS
    params["frequency"] = request.form.get("frequency", params["frequency"])
    params["bandwidth"] = request.form.get("bandwidth", params["bandwidth"])
    print(f"\n🔧 Parameter diubah: Frekuensi={params['frequency']}, Bandwidth={params['bandwidth']}")
    SYSTEM_STATUS = {"status": "restarting", "message": "Konfigurasi ulang parameter..."}
    restart_event.set()
    return jsonify({"status": "ok", "message": "Konfigurasi berhasil diterapkan"})

@app.route("/data")
def data():
    try:
        df = pd.read_csv("data.csv")
        psd = df.groupby("frequency")["power"].mean().reset_index()
        return jsonify({"psd": psd.to_dict(orient='records')})
    except pd.errors.EmptyDataError:
        return jsonify({"psd": []})
    except Exception as e:
        print(f"Error reading data.csv: {e}")
        return jsonify({"psd": []})

@app.route('/start-timed-monitoring', methods=['POST'])
def start_timed_monitoring():
    global LOGGING_ENABLED, CURRENT_LOG_FILE, LOGGING_END_TIME
    if LOGGING_ENABLED:
        return jsonify({"error": "Proses perekaman lain sedang berjalan."}), 409

    try:
        data = request.get_json()
        duration, unit, band_name = data['duration'], data['unit'], data['bandName']
        total_seconds = duration * 60 if unit == 'minutes' else duration * 3600
        duration_str = f"{duration}_{unit.replace('minutes', 'menit').replace('hours', 'jam')}"
        cleaned_band_name = re.sub(r'[^a-zA-Z0-9_-]', '_', band_name.split('(')[0].strip())
        today_date = datetime.now().strftime('%d-%m-%Y')
        filename = f"{cleaned_band_name}_{today_date}_{duration_str}.csv"
        
        LOGGING_ENABLED = True
        CURRENT_LOG_FILE = LOGS_DIR / filename
        LOGGING_END_TIME = time.time() + total_seconds
        
        print(f"▶️ Memulai perekaman selama {duration} {unit} ke file {filename}")
        return jsonify({'message': f'Mulai merekam ke file: {filename}'})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------ Fungsi Sweep Background ------------------
def start_hackrf_loop():
    global SYSTEM_STATUS, LOGGING_ENABLED, CURRENT_LOG_FILE, LOGGING_END_TIME
    process = None
    while True:
        restart_event.clear()
        with sweep_lock:
            if restart_event.is_set():
                if process: process.terminate()
                continue
            
            cmd = ["hackrf_sweep", "-f", params["frequency"], "-w", params["bandwidth"]]
            print(f"\n🔄 Menjalankan monitoring: {' '.join(cmd)}")
            
            try:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                time.sleep(1)
                if process.poll() is not None:
                    raise RuntimeError(f"Gagal memulai hackrf_sweep. Alat tidak terdeteksi.")
                
                SYSTEM_STATUS = {"status": "ok", "message": "Alat aktif dan siap digunakan."}
                log_file_handle, log_writer = None, None

                with open("data.csv", "w", newline='') as realtime_file:
                    realtime_writer = csv.writer(realtime_file)
                    realtime_writer.writerow(["time", "frequency", "power"])
                    
                    for line in process.stdout:
                        if restart_event.is_set(): break
                        
                        if LOGGING_ENABLED and time.time() > LOGGING_END_TIME:
                            LOGGING_ENABLED = False
                            if log_file_handle:
                                log_file_handle.close()
                                print(f"✅ Perekaman selesai. File disimpan: {Path(CURRENT_LOG_FILE).name}")
                                SYSTEM_STATUS = {"status": "ok", "message": "Alat aktif dan siap digunakan."}
                                log_file_handle, log_writer, CURRENT_LOG_FILE = None, None, None
                        
                        if LOGGING_ENABLED and not log_file_handle:
                            log_file_handle = open(CURRENT_LOG_FILE, "w", newline='')
                            log_writer = csv.writer(log_file_handle)
                            log_writer.writerow(["time", "frequency", "power"])
                        
                        if line.startswith("#") or not line.strip(): continue
                        parts = line.strip().split(",")
                        if len(parts) < 7: continue

                        try:
                            rows_to_write = []
                            timestamp, freq_start, step_width = f"{parts[0]} {parts[1]}", float(parts[2]), float(parts[4])
                            powers = parts[6:]
                            for i, p_str in enumerate(powers):
                                if i % DATA_POINT_SAMPLING_RATE == 0:
                                    rows_to_write.append([timestamp, freq_start + i * step_width, float(p_str)])
                            
                            if rows_to_write:
                                realtime_writer.writerows(rows_to_write)
                                realtime_file.flush()
                                if log_writer:
                                    log_writer.writerows(rows_to_write)
                                    log_file_handle.flush()
                            
                            time.sleep(SWEEP_INTERVAL_SECONDS)
                        except (ValueError, IndexError):
                            continue
                
                if log_file_handle: log_file_handle.close()
                if process: process.terminate()

            except Exception as e:
                SYSTEM_STATUS = {"status": "error", "message": f"{e}"}
                print(f"❌ Error saat menjalankan sweep: {e}")
                if process: process.terminate()
                time.sleep(5)

# ------------------ Start Aplikasi ------------------
if __name__ == "__main__":
    threading.Thread(target=start_hackrf_loop, daemon=True).start()
    print("\n🌐 Server Monitoring berjalan di http://127.0.0.1:5001")
    app.run(host="0.0.0.0", port=5001, debug=False)
