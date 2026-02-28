import serial
import time
import re

# Ganti dengan port GPS Anda (contoh: /dev/ttyUSB0 atau /dev/ttyAMA0)
PORT = '/dev/ttyUSB0'
BAUDRATE = 9600

def parse_gpgga(sentence):
    parts = sentence.split(",")
    if len(parts) < 6:
        return None
    try:
        # Latitude
        lat_raw = parts[2]
        lat_dir = parts[3]
        lon_raw = parts[4]
        lon_dir = parts[5]
        time_utc = parts[1]

        if not lat_raw or not lon_raw:
            return None

        lat_deg = float(lat_raw[:2])
        lat_min = float(lat_raw[2:])
        lat = lat_deg + (lat_min / 60.0)
        if lat_dir == "S":
            lat = -lat

        lon_deg = float(lon_raw[:3])
        lon_min = float(lon_raw[3:])
        lon = lon_deg + (lon_min / 60.0)
        if lon_dir == "W":
            lon = -lon

        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

        return (lat, lon, timestamp)
    except:
        return None

ser = serial.Serial(PORT, BAUDRATE, timeout=1)

print("⏱️ Logger GPS aktif...")

while True:
    try:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line.startswith('$GPGGA'):
            result = parse_gpgga(line)
            if result:
                lat, lon, timestamp = result
                with open("gps_data.txt", "w") as f:
                    f.write(f"{lat},{lon},{timestamp}")
                print(f"📍 {lat},{lon} @ {timestamp}")
    except Exception as e:
        print("❌ Error:", e)
        time.sleep(1)

