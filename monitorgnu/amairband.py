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

class am_airband_gui(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "AM Airband Receiver")
        Qt.QWidget.__init__(self)
        self.setWindowTitle("RTL-SDR AM Airband (Pilot/ATC)")
        self.resize(800, 600)
        
        # 1. Variabel Konfigurasi
        self.samp_rate = 2000000     # 2 MSps (Standar RTL-SDR)
        self.center_freq = 119100000 # Default: 119.1 MHz (Frekuensi umum)
        self.audio_rate = 48000      # Audio Out
        self.squelch_level = -50     # Level threshold (dB)

        # Layout GUI
        self.main_layout = Qt.QVBoxLayout()
        self.setLayout(self.main_layout)

        # ----------------------------------------------------------------
        # 2. Blok SDR Source (RTL-SDR)
        # ----------------------------------------------------------------
        self.rtlsdr_source = osmosdr_source(args="rtl=0") 
        self.rtlsdr_source.set_sample_rate(self.samp_rate)
        self.rtlsdr_source.set_center_freq(self.center_freq, 0)
        self.rtlsdr_source.set_freq_corr(0, 0)
        self.rtlsdr_source.set_dc_offset_mode(0, 0)
        self.rtlsdr_source.set_iq_balance_mode(0, 0)
        self.rtlsdr_source.set_gain_mode(False, 0) # Manual Gain
        self.rtlsdr_source.set_gain(20, 0)         # RF Gain agak tinggi untuk AM
        self.rtlsdr_source.set_if_gain(20, 0)
        self.rtlsdr_source.set_bb_gain(20, 0)

        # ----------------------------------------------------------------
        # 3. GUI Controls (Frequency, Squelch, Volume)
        # ----------------------------------------------------------------
        
        # --- Slider Frekuensi (118 - 137 MHz) ---
        self.freq_label = Qt.QLabel("Frequency (Hz) [AIRBAND]:")
        self.main_layout.addWidget(self.freq_label)
        
        self.freq_scroller = Qt.QScrollBar(Qt.Qt.Horizontal)
        self.freq_scroller.setRange(118000000, 137000000) 
        self.freq_scroller.setValue(self.center_freq)
        self.freq_scroller.setSingleStep(25000) # Step 25kHz (Standar Airband)
        self.freq_scroller.valueChanged.connect(self.set_freq)
        self.main_layout.addWidget(self.freq_scroller)

        self.freq_display = Qt.QLabel(f"{self.center_freq/1e6:.3f} MHz")
        self.freq_display.setAlignment(Qt.Qt.AlignCenter)
        self.freq_display.setStyleSheet("font-weight: bold; font-size: 20px; color: blue;")
        self.main_layout.addWidget(self.freq_display)

        # --- Slider Squelch (Peredam Noise) ---
        self.sq_label = Qt.QLabel("Squelch Threshold (Geser ke kanan sampai noise hilang):")
        self.main_layout.addWidget(self.sq_label)
        
        self.sq_slider = Qt.QSlider(Qt.Qt.Horizontal)
        self.sq_slider.setRange(-100, 0) # Range dB
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

        # A. Low Pass Filter (Seleksi Channel & Desimasi)
        # Input: 2M -> Decimate 25 -> Output: 80k
        # AM Airband bandwidth sempit (sekitar 5-6 kHz untuk suara)
        decimation_lpf = 25
        self.channel_filter = filter.fir_filter_ccf(
            decimation_lpf,
            firdes.low_pass(
                1,
                self.samp_rate,
                6000,  # Cutoff 6 kHz (Cukup untuk suara pilot)
                2000,  # Transition width
                window.WIN_HAMMING, 
                6.76))

        # B. Power Squelch (Membungkam jika sinyal lemah)
        self.squelch = analog.pwr_squelch_cc(
            self.squelch_level, # Threshold dB
            1e-4, # Alpha
            0,    # Ramp
            False # Gate
        )

        # C. AM Demodulation (Complex to Magnitude)
        # Cara termudah demodulasi AM adalah mengambil "Magnitude" dari sinyal kompleks
        self.am_demod = blocks.complex_to_mag()

        # D. DC Blocker (High Pass Filter)
        # Menghapus komponen DC offset setelah demodulasi magnitude
        self.dc_blocker = filter.dc_blocker_ff(32, True)

        # E. Audio Resampler
        # Input: 80k (dari LPF) -> Output: 48k (Soundcard)
        # 80k * 3 / 5 = 48k
        self.audio_resampler = filter.rational_resampler_fff(
            interpolation=3,
            decimation=5,
            taps=[],            
            fractional_bw=0.0   
        )

        # F. Volume & Sink
        self.vol_control = blocks.multiply_const_ff(0.8)
        self.audio_sink = audio.sink(self.audio_rate, "", True)

        # G. Visualisasi Spektrum
        self.qtgui_freq_sink = qtgui.freq_sink_c(
            1024, 
            window.WIN_BLACKMAN_hARRIS, 
            self.center_freq,
            self.samp_rate,
            "Airband Spectrum",
            1
        )
        self.qtgui_freq_sink.set_update_time(0.1)
        self.qtgui_freq_sink.set_y_axis(-140, 10)
        
        # Bungkus widget dengan SIP (PENTING untuk GR 3.10)
        self.main_layout.addWidget(
            sip.wrapinstance(self.qtgui_freq_sink.qwidget(), Qt.QWidget)
        )

        # ----------------------------------------------------------------
        # 5. Wiring (Sambungan)
        # ----------------------------------------------------------------
        # Visualisasi: Source -> Sink
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
    tb = am_airband_gui()
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