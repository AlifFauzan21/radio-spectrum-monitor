import gps
from datetime import datetime
import time
import sys

print("Memulai script penangkap data GPS...")
print("Pastikan layanan gpsd sudah berjalan di sistem Anda.")

try:
    session = gps.gps(mode=gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
    print("Sesi GPS berhasil dibuat. Menunggu sinyal...")
except Exception as e:
    print(f"KRITIS: Gagal memulai sesi GPS: {e}")
    print("Mohon pastikan perangkat GPS terhubung dan layanan gpsd telah dikonfigurasi dengan benar.")
    sys.exit(1)

last_lat, last_lon = None, None

while True:
    try:
        report = session.next()

        if report['class'] == 'TPV':
            if hasattr(report, 'lat') and hasattr(report, 'lon'):
                lat = report.lat
                lon = report.lon
                waktu_utc_iso = datetime.utcnow().isoformat() + "Z"

                if lat != last_lat or lon != last_lon:
                    # Simpan ke gps_data.txt (terbaru)
                    with open("gps_data.txt", "w") as f:
                        f.write(f"{lat},{lon},{waktu_utc_iso}")

                    # Simpan juga ke gps_data_full.txt (log lengkap)
                    with open("gps_data_full.txt", "a") as f_full:
                        f_full.write(f"{lat},{lon},{waktu_utc_iso}\n")

                    print(f"\r[DATA BARU] Lat: {lat:.6f}, Lon: {lon:.6f}, Waktu: {waktu_utc_iso}  ", end="")
                    sys.stdout.flush()

                    last_lat, last_lon = lat, lon
            else:
                print("\rMenunggu sinyal GPS yang valid (belum mendapatkan 'fix')...", end="")
                sys.stdout.flush()

    except KeyError:
        pass
    except KeyboardInterrupt:
        print("\nProses dihentikan oleh pengguna. Selamat tinggal!")
        break
    except StopIteration:
        print("\nKoneksi ke layanan gpsd terputus. Menghentikan script.")
        session = None
        break
    except Exception as e:
        print(f"\nTerjadi error tak terduga: {e}")
        time.sleep(2)

    time.sleep(1)

