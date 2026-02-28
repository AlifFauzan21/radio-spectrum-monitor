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

class fm_radio_gui(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "FM Radio RTL-SDR with Squelch")
        Qt.QWidget.__init__(self)
        self.setWindowTitle("RTL-SDR FM Receiver with Squelch (WFM)")
        self.resize(800, 600)
        
        # 1. Variabel Konfigurasi Dasar
        self.samp_rate = 2000000     
        self.center_freq = 98700000  
        self.audio_rate = 48000      
        self.squelch_level = -60     # Default Squelch Level (dB)

        # Layout GUI
        self.main_layout = Qt.QVBoxLayout()
        self.setLayout(self.main_layout)

        # ----------------------------------------------------------------
        # 2. Blok SDR Source (RTL-SDR)
        # ----------------------------------------------------------------
        self.rtlsdr_source = osmosdr_source(args="rtl=0") 
        self.rtlsdr_source.set_sample_rate(self.samp_rate)
        self.rtlsdr_source.set_center_freq(self.center_freq, 0)
        self.rtlsdr_source.set_gain_mode(False, 0) 
        self.rtlsdr_source.set_gain(20, 0)         
        self.rtlsdr_source.set_if_gain(20, 0)
        self.rtlsdr_source.set_bb_gain(20, 0)

        # ----------------------------------------------------------------
        # 3. GUI Controls (Tambahan Squelch)
        # ----------------------------------------------------------------
        
        # --- Slider Frekuensi ---
        self.freq_label = Qt.QLabel("Frequency (Hz) [WFM]:")
        self.main_layout.addWidget(self.freq_label)
        
        self.freq_scroller = Qt.QScrollBar(Qt.Qt.Horizontal)
        self.freq_scroller.setRange(88000000, 108000000) 
        self.freq_scroller.setValue(self.center_freq)
        self.freq_scroller.setSingleStep(100000) 
        self.freq_scroller.valueChanged.connect(self.set_freq)
        self.main_layout.addWidget(self.freq_scroller)

        self.freq_display = Qt.QLabel(f"{self.center_freq/1e6:.1f} MHz")
        self.freq_display.setAlignment(Qt.Qt.AlignCenter)
        self.freq_display.setStyleSheet("font-weight: bold; font-size: 16px; color: green;")
        self.main_layout.addWidget(self.freq_display)

        # --- Slider Squelch (BARU) ---
        self.sq_label = Qt.QLabel("Squelch Threshold (dB):")
        self.main_layout.addWidget(self.sq_label)
        
        self.sq_slider = Qt.QSlider(Qt.Qt.Horizontal)
        self.sq_slider.setRange(-100, 0) # Range dBm umum
        self.sq_slider.setValue(self.squelch_level)
        self.sq_slider.valueChanged.connect(self.set_squelch)
        self.main_layout.addWidget(self.sq_slider)
        
        self.sq_display = Qt.QLabel(f"{self.squelch_level} dB")
        self.sq_display.setAlignment(Qt.Qt.AlignCenter)
        self.main_layout.addWidget(self.sq_display)
        # -----------------------------

        # --- Slider Volume ---
        self.vol_label = Qt.QLabel("Volume:")
        self.main_layout.addWidget(self.vol_label)
        
        self.vol_slider = Qt.QSlider(Qt.Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(80) 
        self.vol_slider.valueChanged.connect(self.set_volume)
        self.main_layout.addWidget(self.vol_slider)

        # ----------------------------------------------------------------
        # 4. Signal Processing Chain (WFM Demodulation)
        # ----------------------------------------------------------------
        
        # A. Low Pass Filter & Desimasi
        decimation_lpf = 5
        self.low_pass_filter = filter.fir_filter_ccf(
            decimation_lpf,
            firdes.low_pass(
                1, self.samp_rate, 100000, 20000, window.WIN_HAMMING, 6.76))

        # B. Power Squelch (BARU)
        # Squelch di sini untuk membungkam noise ketika tidak ada sinyal kuat
        self.squelch = analog.pwr_squelch_cc(
            self.squelch_level, 
            1e-4, # Alpha
            0,    # Ramp
            False # Gate
        )
        
        # C. WIDE FM Receiver (Demodulasi)
        self.wbfm_rcv = analog.wfm_rcv(
            quad_rate=400000, 
            audio_decimation=1 
        )

        # D. Audio Resampler
        self.audio_resampler = filter.rational_resampler_fff(
            interpolation=6,
            decimation=50,
            taps=[], fractional_bw=0.0)

        # E. Volume & Sink
        self.vol_control = blocks.multiply_const_ff(0.8)
        self.audio_sink = audio.sink(self.audio_rate, "", True)

        # F. Visualisasi QT GUI Sink
        self.qtgui_freq_sink = qtgui.freq_sink_c(
            1024, window.WIN_BLACKMAN_hARRIS, self.center_freq, self.samp_rate,"FM Spectrum",1)
        self.qtgui_freq_sink.set_update_time(0.1)
        self.qtgui_freq_sink.set_y_axis(-140, 10)
        
        self.main_layout.addWidget(
            sip.wrapinstance(self.qtgui_freq_sink.qwidget(), Qt.QWidget))

        # ----------------------------------------------------------------
        # 5. Wiring (Sambungan)
        # ----------------------------------------------------------------
        # Perubahan rantai: LPF -> SQUELCH -> WBFM RCV
        self.connect((self.rtlsdr_source, 0), (self.qtgui_freq_sink, 0))
        self.connect((self.rtlsdr_source, 0), (self.low_pass_filter, 0))
        self.connect((self.low_pass_filter, 0), (self.squelch, 0)) # <--- BLOK BARU
        self.connect((self.squelch, 0), (self.wbfm_rcv, 0))        # <--- SAMBUNGAN BARU
        self.connect((self.wbfm_rcv, 0), (self.audio_resampler, 0))
        self.connect((self.audio_resampler, 0), (self.vol_control, 0))
        self.connect((self.vol_control, 0), (self.audio_sink, 0))

    # --- Callbacks ---
    def set_freq(self, freq):
        self.center_freq = freq
        self.rtlsdr_source.set_center_freq(self.center_freq, 0)
        self.qtgui_freq_sink.set_frequency_range(self.center_freq, self.samp_rate)
        self.freq_display.setText(f"{self.center_freq/1e6:.1f} MHz")
    
    def set_squelch(self, value):
        self.squelch_level = value
        self.squelch.set_threshold(self.squelch_level)
        self.sq_display.setText(f"{self.squelch_level} dB")

    def set_volume(self, value):
        vol = value / 100.0 
        self.vol_control.set_k(vol)

def main():
    qapp = Qt.QApplication(sys.argv)
    tb = fm_radio_gui()
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