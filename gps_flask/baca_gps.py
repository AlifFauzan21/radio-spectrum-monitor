import os
import time
import random
import subprocess
import glob
from datetime import datetime

# --- KONFIGURASI NAMA FILE (DIPISAH) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FILE_REAL = os.path.join(BASE_DIR, 'gps_log_REAL.txt')       # Khusus Data Asli
FILE_SIMULASI = os.path.join(BASE_DIR, 'gps_log_SIMULASI.txt') # Khusus Data Palsu

# Lokasi Default (Polsri)
DEFAULT_LAT = -2.990934
DEFAULT_LON = 104.756554

print(f"[*] GPS Service Berjalan...")

# --- FUNGSI AUTO CONNECT (SAMA SEPERTI SEBELUMNYA) ---
def auto_connect_hardware():
    print("[INIT] Mencari Hardware GPS...")
    ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    
    if not ports:
        print("[WARN] Tidak ada perangkat GPS. Masuk Mode SIMULASI.")
        return False, None

    selected_port = ports[0]
    print(f"[INFO] Perangkat ditemukan di: {selected_port}")

    try:
        subprocess.run(['sudo', 'killall', 'gpsd'], stderr=subprocess.DEVNULL)
        time.sleep(1)
    except: pass

    try:
        subprocess.run(['sudo', 'gpsd', selected_port, '-F', '/var/run/gpsd.sock'])
        print(f"[SUCCESS] Driver GPS aktif pada {selected_port}")
        time.sleep(2)
        return True, selected_port
    except Exception as e:
        print(f"[ERROR] Gagal start driver: {e}")
        return False, None

# --- CEK LIBRARY GPS ---
try:
    from gps import *
    HAS_GPS_LIBRARY = True
except ImportError:
    HAS_GPS_LIBRARY = False

# --- FUNGSI TULIS LOG (DINAMIS) ---
def save_log(target_file, lat, lon, speed):
    try:
        with open(target_file, "a") as f:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            line = f"{now}|{lat}|{lon}|{speed}\n"
            f.write(line)
            # print(f"[SAVED ke {os.path.basename(target_file)}] {line.strip()}")
    except Exception as e:
        print(f"Error tulis file: {e}")

# --- FUNGSI SIMULASI ---
def get_simulated_data():
    lat = DEFAULT_LAT + random.uniform(-0.0005, 0.0005)
    lon = DEFAULT_LON + random.uniform(-0.0005, 0.0005)
    speed = round(random.uniform(10, 60), 2)
    return lat, lon, speed

# --- MAIN LOOP ---
def main():
    # 1. Tentukan Mode Awal
    hardware_ready = False
    active_file = FILE_SIMULASI # Default ke simulasi dulu

    if HAS_GPS_LIBRARY:
        hardware_ready, port = auto_connect_hardware()
    
    # 2. Jika Hardware Ready -> Ubah target ke FILE_REAL
    if hardware_ready:
        active_file = FILE_REAL
        print(f"[MODE] REAL HARDWARE DETECTED. Menyimpan ke: gps_log_REAL.txt")
    else:
        print(f"[MODE] SIMULASI. Menyimpan ke: gps_log_SIMULASI.txt")

    session = None
    if hardware_ready:
        try:
            session = gps(mode=WATCH_ENABLE)
        except:
            session = None

    while True:
        try:
            lat, lon, speed = None, None, 0
            
            # A. BACA HARDWARE
            if session:
                try:
                    report = session.next()
                    if report['class'] == 'TPV':
                        if hasattr(report, 'lat') and hasattr(report, 'lon'):
                            lat = float(report.lat)
                            lon = float(report.lon)
                            if hasattr(report, 'speed'):
                                speed = round(float(report.speed) * 3.6, 2)
                            else: speed = 0
                except StopIteration:
                    session = None

            # B. FAILOVER KE SIMULASI (Jika Lat kosong)
            if lat is None:
                # Jika seharusnya Real tapi datanya kosong, tetap tulis ke Real (sebagai data kosong/tunggu)
                # ATAU kita paksa simulasi masuk ke file simulasi?
                # Sesuai request: Pisahkan file.
                
                if hardware_ready and session is not None:
                     # Alat connect tapi belum dpt sinyal (No Fix)
                     # Kita jangan tulis apa-apa dulu ke Real, atau tulis 0
                     pass 
                else:
                    # Benar-benar tidak ada alat / error
                    lat, lon, speed = get_simulated_data()
                    active_file = FILE_SIMULASI # Pastikan masuk ke file simulasi

            # C. SIMPAN (Hanya jika ada data lat)
            if lat is not None:
                save_log(active_file, lat, lon, speed)
            
            time.sleep(1)

        except KeyError: pass
        except KeyboardInterrupt: break
        except Exception as e: time.sleep(1)

if __name__ == '__main__':
    main()
