#!/usr/bin/env python3
import subprocess
import time
import sys
import os

# --- KONFIGURASI FREKUENSI ---
# 119.1 MHz adalah frekuensi umum Jakarta Approach (contoh)
# 118.1 MHz, 118.6 MHz (Menara Soekarno-Hatta)
# Silakan ganti sesuai bandara terdekatmu
FREQ = "119.1M" 

def main():
    print(f"[*] Memulai Sistem Monitoring Airband pada {FREQ}...")
    print("[*] Mode: AM (Amplitude Modulation)")
    
    # Cek apakah device terpasang (HackRF atau RTL-SDR)
    # Kita coba jalankan perintah 'rtl_test' atau 'hackrf_info' sekilas
    # Ini opsional, hanya untuk memastikan hardware ada
    
    try:
        # PERINTAH UTAMA (CORE COMMAND)
        # rtl_fm: Tool untuk menangkap sinyal radio
        # -M am : Mode AM (Wajib untuk penerbangan)
        # -f : Frekuensi
        # -s : Sample rate (12k cukup untuk suara manusia)
        # -g : Gain (50 atau '0' untuk auto)
        
        # Command ini akan menangkap sinyal dan membuangnya ke /dev/null 
        # (karena kita mendengarkannya lewat streaming web, bukan speaker server)
        # Script ini hanya bertugas menjaga agar hardware 'LOCK' pada frekuensi tersebut.
        
        cmd = ["rtl_fm", "-M", "am", "-f", FREQ, "-s", "12k", "-g", "50"]
        
        # Jika kamu ingin mendengarkan langsung di speaker server/laptop (bukan web),
        # gunakan command di bawah ini (hilangkan tanda #):
        # cmd = "rtl_fm -M am -f 119.1M -s 12k -g 50 | play -t raw -r 12k -e s16 -b 16 -c 1 -"
        
        print(f"[*] Menjalankan command hardware: {' '.join(cmd)}")
        
        # Menjalankan proses radio
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.DEVNULL, # Output suara dibuang (karena streaming via web beda jalur)
            stderr=subprocess.PIPE     # Tangkap error jika ada
        )

        # Loop monitoring agar script tidak mati (tetap 'Running' di Flask)
        while True:
            # Cek apakah proses SDR mati tiba-tiba?
            if process.poll() is not None:
                print("[!] Error: Perangkat SDR terputus atau driver belum terinstall.")
                print(process.stderr.read().decode())
                break
            
            # Simulasi log sinyal (agar terlihat aktif di console Flask)
            # Nanti bisa diganti dengan pembacaan RSSI asli jika butuh advanced
            sys.stdout.write(f"\r[Active] Monitoring {FREQ} - Hardware Locked - {time.strftime('%H:%M:%S')}")
            sys.stdout.flush()
            time.sleep(1)

    except FileNotFoundError:
        print("\n[CRITICAL ERROR] Driver RTL-SDR tidak ditemukan!")
        print("Solusi: Install dulu dengan mengetik di terminal:")
        print("sudo apt-get install rtl-sdr sox")
        
    except KeyboardInterrupt:
        print("\n[*] Stopping Airband Receiver...")
        if 'process' in locals():
            process.terminate()

if __name__ == "__main__":
    main()
