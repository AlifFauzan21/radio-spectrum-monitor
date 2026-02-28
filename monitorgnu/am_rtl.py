#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import signal
from PyQt5 import Qt
from gnuradio import analog
from gnuradio import audio
from gnuradio import blocks
from gnuradio import filter
from gnuradio import gr
from gnuradio import qtgui
from gnuradio.filter import firdes
from gnuradio.fft import window  
from osmosdr import source as osmosdr_source
import sip 

class am_receiver_gui(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "AM Receiver (Medium Wave) - Direct Sampling")
        Qt.QWidget.__init__(self)
        self.setWindowTitle("RTL-SDR AM Receiver (MW) - Direct Sampling")
        self.resize(800, 600)
        
        # 1. Variabel Konfigurasi
        self.samp_rate = 2000000     # Sample Rate
        self.center_freq = 1000000   # Default 1.0 MHz
        self.audio_rate = 48000      # Audio Out
        self.squelch_level = -60     # Tingkat Squelch

        # Layout GUI
        self.main_layout = Qt.QVBoxLayout()
        self.setLayout(self.main_layout)

        # ----------------------------------------------------------------
        # 2. Blok SDR Source (RTL-SDR)
        # ----------------------------------------------------------------
        # PENTING: Menggunakan Direct Sampling Mode (Mode I) untuk frekuensi rendah
        self.rtlsdr_source = osmosdr_source(args="rtl=0,direct_samp=1") 
        self.rtlsdr_source.set_sample_rate(self.samp_rate)
        self.rtlsdr_source.set_center_freq(self.center_freq, 0)
        self.rtlsdr_source.set_gain_mode(False, 0) 
        self.rtlsdr_source.set_gain(49.6, 0) # Gain Maksimum disarankan untuk Direct Sampling
        self.rtlsdr_source.set_if_gain(0, 0)  # IF Gain dinonaktifkan
        self.rtlsdr_source.set_bb_gain(0, 0) # BB Gain dinonaktifkan

        # ----------------------------------------------------------------
        # 3. GUI Controls 
        # ----------------------------------------------------------------
        
        # --- Slider Frekuensi (530 kHz - 1.71 MHz) ---
        self.freq_label = Qt.QLabel("Frequency (Hz) [AM/MW]:")
        self.main_layout.addWidget(self.freq_label)
        
        self.freq_scroller = Qt.QScrollBar(Qt.Qt.Horizontal)
        self.freq_scroller.setRange(530000, 1710000) # Rentang MW
        self.freq_scroller.setValue(self.center_freq)
        self.freq_scroller.setSingleStep(10000)      # Step 10 kHz
        self.freq_scroller.valueChanged.connect(self.set_freq)
        self.main_layout.addWidget(self.freq_scroller)

        self.freq_display = Qt.QLabel(f"{self.center_freq/1e6:.3f} MHz")
        self.freq_display.setAlignment(Qt.Qt.AlignCenter)
        self.freq_display.setStyleSheet("font-weight: bold; font-size: 16px; color: red;")
        self.main_layout.addWidget(self.freq_display)

        # --- Slider Squelch ---
        self.sq_label = Qt.QLabel("Squelch Threshold (dB):")
        self.main_layout.addWidget(self.sq_label)
        
        self.sq_slider = Qt.QSlider(Qt.Qt.Horizontal)
        self.sq_slider.setRange(-100, 0) 
        self.sq_slider.setValue(self.squelch_level)
        self.sq_slider.valueChanged.connect(self.set_squelch)
        self.main_layout.addWidget(self.sq_slider)
        
        self.sq_display = Qt.QLabel(f"{self.squelch_level} dB")
        self.sq_display.setAlignment(Qt.Qt.AlignCenter)
        self.main_layout.addWidget(self.sq_display)

        # --- Slider Volume ---
        self.vol_label = Qt.QLabel("Volume:")
        self.main_layout.addWidget(self.vol_label)
        
        self.vol_slider = Qt.QSlider(Qt.Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(80) 
        self.vol_slider.valueChanged.connect(self.set_volume)
        self.main_layout.addWidget(self.vol_slider)

        # ----------------------------------------------------------------
        # 4. Signal Processing Chain (AM Demodulation)
        # ----------------------------------------------------------------

        # A. Low Pass Filter & Desimasi
        # Input: 2M -> Decimate 25 -> Output: 80k (Channel Rate)
        # AM MW membutuhkan bandwidth 5-10 kHz
        decimation_lpf = 25
        self.channel_filter = filter.fir_filter_ccf(
            decimation_lpf,
            firdes.low_pass(
                1, self.samp_rate, 7000, 2000, window.WIN_HAMMING, 6.76))

        # B. Power Squelch 
        self.squelch = analog.pwr_squelch_cc(
            self.squelch_level, 1e-4, 0, False)
        
        # C. AM Demodulation (Complex to Magnitude / Envelope Detection)
        self.am_demod = blocks.complex_to_mag()

        # D. DC Blocker
        self.dc_blocker = filter.dc_blocker_ff(32, True)

        # E. Audio Resampler
        # Input: 80k -> Output: 48k (80k * 3 / 5 = 48k)
        self.audio_resampler = filter.rational_resampler_fff(
            interpolation=3, decimation=5, taps=[], fractional_bw=0.0)

        # F. Volume & Sink
        self.vol_control = blocks.multiply_const_ff(0.8)
        self.audio_sink = audio.sink(self.audio_rate, "", True)

        # G. Visualisasi QT GUI Sink
        self.qtgui_freq_sink = qtgui.freq_sink_c(
            1024, window.WIN_BLACKMAN_hARRIS, self.center_freq, self.samp_rate,"AM Spectrum",1)
        self.qtgui_freq_sink.set_update_time(0.1)
        self.qtgui_freq_sink.set_y_axis(-140, 10)
        
        # Menambahkan widget ke layout (Fix GR 3.10)
        self.main_layout.addWidget(
            sip.wrapinstance(self.qtgui_freq_sink.qwidget(), Qt.QWidget))

        # ----------------------------------------------------------------
        # 5. Wiring (Sambungan)
        # ----------------------------------------------------------------
        # Source -> Sink Visual
        self.connect((self.rtlsdr_source, 0), (self.qtgui_freq_sink, 0))
        
        # Audio Chain: 
        # Source -> Filter(80k) -> Squelch -> AM Demod -> DC Block -> Resampler(48k) -> Vol -> Speaker
        self.connect((self.rtlsdr_source, 0), (self.channel_filter, 0))
        self.connect((self.channel_filter, 0), (self.squelch, 0))
        self.connect((self.squelch, 0), (self.am_demod, 0))
        self.connect((self.am_demod, 0), (self.dc_blocker, 0))
        self.connect((self.dc_blocker, 0), (self.audio_resampler, 0))
        self.connect((self.audio_resampler, 0), (self.vol_control, 0))
        self.connect((self.vol_control, 0), (self.audio_sink, 0))

    # --- Callbacks ---
    def set_freq(self, freq):
        self.center_freq = freq
        self.rtlsdr_source.set_center_freq(self.center_freq, 0)
        self.qtgui_freq_sink.set_frequency_range(self.center_freq, self.samp_rate)
        self.freq_display.setText(f"{self.center_freq/1e6:.3f} MHz")
    
    def set_squelch(self, value):
        self.squelch_level = value
        self.squelch.set_threshold(self.squelch_level)
        self.sq_display.setText(f"{self.squelch_level} dB")

    def set_volume(self, value):
        vol = value / 100.0 
        self.vol_control.set_k(vol)

def main():
    qapp = Qt.QApplication(sys.argv)
    tb = am_receiver_gui()
    tb.start()
    tb.show()

    def sig_handler(sig=None, frame=None):
        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.show()
    qapp.exec_()
    tb.stop()
    tb.wait()

if __name__ == '__main__':
    main()