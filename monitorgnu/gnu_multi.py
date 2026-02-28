#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Monitoring Spektrum (RTL-SDR Version)
# Author: Modified for Alif/Daffa
# GNU Radio version: 3.10.5.1

from packaging.version import Version as StrictVersion

if __name__ == '__main__':
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print("Warning: failed to XInitThreads()")

from PyQt5 import Qt
from PyQt5.QtCore import QObject, pyqtSlot
from gnuradio import qtgui
from gnuradio.filter import firdes
import sip
from gnuradio import analog
from gnuradio import blocks
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import osmosdr
import time

from gnuradio import qtgui

class gnu_multi(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Monitoring Spektrum (RTL-SDR)", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Monitoring Spektrum (RTL-SDR)")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except:
            pass
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "gnu_multi")

        try:
            if StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
                self.restoreGeometry(self.settings.value("geometry").toByteArray())
            else:
                self.restoreGeometry(self.settings.value("geometry"))
        except:
            pass

        ##################################################
        # Variables (DISESUAIKAN UNTUK RTL-SDR)
        ##################################################
        # RTL-SDR Maksimal stabil di 2.4 MHz, kita pakai 2.048 MHz biar aman
        self.samp_rate = samp_rate = 2.048e6 
        self.run_control = run_control = True
        self.rentang_frekuensi = rentang_frekuensi = 97.5e6
        self.center_freq = center_freq = 97.5e6
        
        # Bandwidth visualisasi kita samakan dengan sample rate RTL-SDR
        self.bandwidth = bandwidth = samp_rate 

        ##################################################
        # Blocks
        ##################################################

        self._run_control_choices = {'Pressed': bool(1), 'Released': bool(0)}

        _run_control_toggle_button = qtgui.ToggleButton(self.set_run_control, 'Pause/Resume', self._run_control_choices, True, 'value')
        _run_control_toggle_button.setColors("default", "default", "default", "default")
        self.run_control = _run_control_toggle_button

        self.top_grid_layout.addWidget(_run_control_toggle_button, 1, 0, 1, 1)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
            
        # --- DROPDOWN FREKUENSI ---
        self._rentang_frekuensi_options = [97500000.0, 122500000.0, 155500000.0, 445000000.0, 850000000.0]
        self._rentang_frekuensi_labels = ['FM Radio (97.5)', 'Airband (122.5)', 'VHF (155.5)', 'UHF (445)', 'GSM (850)']
        
        self._rentang_frekuensi_tool_bar = Qt.QToolBar(self)
        self._rentang_frekuensi_tool_bar.addWidget(Qt.QLabel("Frekuensi Center" + ": "))
        self._rentang_frekuensi_combo_box = Qt.QComboBox()
        self._rentang_frekuensi_tool_bar.addWidget(self._rentang_frekuensi_combo_box)
        for _label in self._rentang_frekuensi_labels: self._rentang_frekuensi_combo_box.addItem(_label)
        self._rentang_frekuensi_callback = lambda i: Qt.QMetaObject.invokeMethod(self._rentang_frekuensi_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._rentang_frekuensi_options.index(i)))
        self._rentang_frekuensi_callback(self.rentang_frekuensi)
        self._rentang_frekuensi_combo_box.currentIndexChanged.connect(
            lambda i: self.set_rentang_frekuensi(self._rentang_frekuensi_options[i]))
        
        self.top_layout.addWidget(self._rentang_frekuensi_tool_bar)

        # --- WATERFALL SINK ---
        self.qtgui_waterfall_sink_x_0 = qtgui.waterfall_sink_c(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            rentang_frekuensi, #fc
            samp_rate, #bw (Gunakan Sample Rate asli RTL-SDR)
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_waterfall_sink_x_0.set_update_time(0.10)
        self.qtgui_waterfall_sink_x_0.enable_grid(False)
        self.qtgui_waterfall_sink_x_0.enable_axis_labels(True)
        self.qtgui_waterfall_sink_x_0.set_intensity_range(-100, 0) # Sesuaikan range dB RTL-SDR

        self._qtgui_waterfall_sink_x_0_win = sip.wrapinstance(self.qtgui_waterfall_sink_x_0.qwidget(), Qt.QWidget)

        self.top_grid_layout.addWidget(self._qtgui_waterfall_sink_x_0_win, 0, 0, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
            
        # --- FREQ SINK ---
        self.qtgui_freq_sink_x_1 = qtgui.freq_sink_c(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            rentang_frekuensi, #fc
            samp_rate, #bw (Gunakan Sample Rate asli RTL-SDR)
            'Spectrum Monitor', #name
            1,
            None # parent
        )
        self.qtgui_freq_sink_x_1.set_update_time(0.10)
        self.qtgui_freq_sink_x_1.set_y_axis((-100), 0)
        self.qtgui_freq_sink_x_1.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_x_1.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_x_1.enable_autoscale(False)
        self.qtgui_freq_sink_x_1.enable_grid(True)
        self.qtgui_freq_sink_x_1.set_fft_average(1.0)
        self.qtgui_freq_sink_x_1.enable_axis_labels(True)
        self.qtgui_freq_sink_x_1.enable_control_panel(True)
        self.qtgui_freq_sink_x_1.set_fft_window_normalized(False)

        self._qtgui_freq_sink_x_1_win = sip.wrapinstance(self.qtgui_freq_sink_x_1.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_freq_sink_x_1_win, 0, 1, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
            
        # --- RTL-SDR SOURCE (FIXED) ---
        self.osmosdr_source_0 = osmosdr.source(
            args="numchan=" + str(1) + " " + 'rtl=0' # GANTI JADI RTL=0
        )
        self.osmosdr_source_0.set_time_unknown_pps(osmosdr.time_spec_t())
        self.osmosdr_source_0.set_sample_rate(samp_rate)
        self.osmosdr_source_0.set_center_freq(rentang_frekuensi, 0)
        self.osmosdr_source_0.set_freq_corr(0, 0)
        self.osmosdr_source_0.set_dc_offset_mode(0, 0)
        self.osmosdr_source_0.set_iq_balance_mode(0, 0)
        self.osmosdr_source_0.set_gain_mode(False, 0)
        self.osmosdr_source_0.set_gain(30, 0) # Gain Standar RTL-SDR
        self.osmosdr_source_0.set_if_gain(20, 0)
        self.osmosdr_source_0.set_bb_gain(20, 0)
        self.osmosdr_source_0.set_antenna('', 0)
        self.osmosdr_source_0.set_bandwidth(0, 0)
        
        # --- PAUSE CONTROL BLOCK ---
        self.blocks_multiply_const_vxx_1 = blocks.multiply_const_cc(1.0 if run_control else 0.0)

        ##################################################
        # Connections
        ##################################################
        # Alur Sederhana: SDR -> Pause Switch -> Visualisasi
        self.connect((self.osmosdr_source_0, 0), (self.blocks_multiply_const_vxx_1, 0))
        self.connect((self.blocks_multiply_const_vxx_1, 0), (self.qtgui_waterfall_sink_x_0, 0))
        self.connect((self.blocks_multiply_const_vxx_1, 0), (self.qtgui_freq_sink_x_1, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "gnu_multi")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()
        event.accept()

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.osmosdr_source_0.set_sample_rate(self.samp_rate)
        self.qtgui_waterfall_sink_x_0.set_frequency_range(self.rentang_frekuensi, self.samp_rate)
        self.qtgui_freq_sink_x_1.set_frequency_range(self.rentang_frekuensi, self.samp_rate)

    def get_run_control(self):
        return self.run_control

    def set_run_control(self, run_control):
        self.run_control = run_control
        self.blocks_multiply_const_vxx_1.set_k(1.0 if self.run_control else 0.0)

    def get_rentang_frekuensi(self):
        return self.rentang_frekuensi

    def set_rentang_frekuensi(self, rentang_frekuensi):
        self.rentang_frekuensi = rentang_frekuensi
        self._rentang_frekuensi_callback(self.rentang_frekuensi)
        self.osmosdr_source_0.set_center_freq(self.rentang_frekuensi, 0)
        self.qtgui_freq_sink_x_1.set_frequency_range(self.rentang_frekuensi, self.samp_rate)
        self.qtgui_waterfall_sink_x_0.set_frequency_range(self.rentang_frekuensi, self.samp_rate)

def main(top_block_cls=gnu_multi, options=None):
    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)
    tb = top_block_cls()
    tb.start()
    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()
        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)
    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)
    qapp.exec_()

if __name__ == '__main__':
    main()
