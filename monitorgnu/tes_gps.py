import serial
import pynmea2

# Konfigurasi port serial
port = "/dev/ttyAMA0"  # Perhatikan: angka nol bukan huruf 'O'
baudrate = 9600
timeout = 0.5

# Membuka koneksi serial
ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)

try:
    while True:
        newdata = ser.readline().decode('ascii', errors='replace').strip()
        print("Mencari Sinyal...")

        if newdata.startswith("$GPRMC"):
            try:
                newmsg = pynmea2.parse(newdata)
                lat = newmsg.latitude
                lng = newmsg.longitude
                gps = f"Latitude = {lat} and Longitude = {lng}"
                print(gps)
            except pynmea2.ParseError as e:
                print(f"Parse error: {e}")
except KeyboardInterrupt:
    print("Program dihentikan.")
finally:
    ser.close()
