from flask import Flask, render_template, send_file, jsonify, request
import subprocess
import threading
import time
import gps

app = Flask(__name__)

# Variabel global untuk menyimpan data GPS terbaru
gps_data = {
    'lat': 0.0,
    'lon': 0.0,
    'time': ''
}

# Fungsi background untuk membaca data GPS secara terus-menerus
def gps_reader():
    session = gps.gps(mode=gps.WATCH_ENABLE)
    while True:
        try:
            report = session.next()
            if report['class'] == 'TPV':
                gps_data['lat'] = getattr(report, 'lat', 0.0)
                gps_data['lon'] = getattr(report, 'lon', 0.0)
                gps_data['time'] = getattr(report, 'time', '')
        except Exception as e:
            print("GPS error:", e)
        time.sleep(1)

# Jalankan thread pembaca GPS saat aplikasi Flask dimulai
threading.Thread(target=gps_reader, daemon=True).start()

@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/gps_map')
def map_page():
    return send_file('map.html')

@app.route('/gps_data')
def gps_data_api():
    return jsonify(gps_data)

@app.route('/run/<script_name>')
def run_script(script_name):
    subprocess.Popen(["python3", f"{script_name}.py"])
    return f"Running {script_name}.py"

@app.route('/gnumulti', methods=['POST'])
def gnumulti():
    try:
        subprocess.Popen(["python3", f"gnu_multi.py"])
        return jsonify({'status': 'ok', 'message': 'Monitoring 1 Frequency is running'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
        

@app.route('/hackrftest', methods=['POST'])
def hackrftest():
    try:
        subprocess.Popen(["python3", f"hackrf_test.py"])
        return jsonify({'status': 'ok', 'message': 'Monitoring multi Frequency is running'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)

