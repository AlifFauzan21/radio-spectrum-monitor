#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Monitoring Spektrum Frekuensi dengah Hack RF
# Author: raspi4b
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
from gnuradio import eng_notation
from gnuradio import qtgui
from gnuradio.filter import firdes
import sip
from gnuradio import analog
from gnuradio import audio
from gnuradio import blocks
from gnuradio import filter
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio.qtgui import Range, RangeWidget
from PyQt5 import QtCore
import osmosdr
import time



from gnuradio import qtgui

class hakrf_multi_frequency(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Monitoring Spektrum Frekuensi dengah Hack RF", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Monitoring Spektrum Frekuensi dengah Hack RF")
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

        self.settings = Qt.QSettings("GNU Radio", "hakrf_multi_frequency")

        try:
            if StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
                self.restoreGeometry(self.settings.value("geometry").toByteArray())
            else:
                self.restoreGeometry(self.settings.value("geometry"))
        except:
            pass

        ##################################################
        # Variables
        ##################################################
        self.stop_frek = stop_frek = 108e6
        self.start_frek = start_frek = 87e6
        self.samp_rate = samp_rate = 8e6
        self.run_control = run_control = True
        self.channel_width = channel_width = 2e5
        self.channel_freq = channel_freq = 96.5e6
        self.center_freq = center_freq = 97.9e6
        self.audio_gain = audio_gain = 1
        self.Bandwidth = Bandwidth = (stop_frek-start_frek)

        ##################################################
        # Blocks
        ##################################################

        self._stop_frek_tool_bar = Qt.QToolBar(self)
        self._stop_frek_tool_bar.addWidget(Qt.QLabel("STop Frekuensi" + ": "))
        self._stop_frek_line_edit = Qt.QLineEdit(str(self.stop_frek))
        self._stop_frek_tool_bar.addWidget(self._stop_frek_line_edit)
        self._stop_frek_line_edit.returnPressed.connect(
            lambda: self.set_stop_frek(eng_notation.str_to_num(str(self._stop_frek_line_edit.text()))))
        self.top_layout.addWidget(self._stop_frek_tool_bar)
        self._start_frek_tool_bar = Qt.QToolBar(self)
        self._start_frek_tool_bar.addWidget(Qt.QLabel("Start Frekuensi" + ": "))
        self._start_frek_line_edit = Qt.QLineEdit(str(self.start_frek))
        self._start_frek_tool_bar.addWidget(self._start_frek_line_edit)
        self._start_frek_line_edit.returnPressed.connect(
            lambda: self.set_start_frek(eng_notation.str_to_num(str(self._start_frek_line_edit.text()))))
        self.top_grid_layout.addWidget(self._start_frek_tool_bar, 1, 1, 1, 1)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._run_control_choices = {'Pressed': bool(1), 'Released': bool(0)}

        _run_control_toggle_button = qtgui.ToggleButton(self.set_run_control, 'Pause/Resume', self._run_control_choices, True, 'value')
        _run_control_toggle_button.setColors("default", "default", "default", "default")
        self.run_control = _run_control_toggle_button

        self.top_grid_layout.addWidget(_run_control_toggle_button, 1, 0, 1, 1)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._audio_gain_range = Range(0, 10, 0.1, 1, 200)
        self._audio_gain_win = RangeWidget(self._audio_gain_range, self.set_audio_gain, "Volume", "dial", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._audio_gain_win, 2, 0, 1, 2)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.rational_resampler_xxx_0 = filter.rational_resampler_ccc(
                interpolation=12,
                decimation=5,
                taps=[],
                fractional_bw=0)
        self.qtgui_waterfall_sink_x_0 = qtgui.waterfall_sink_c(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            ((start_frek+stop_frek)/2), #fc
            (stop_frek-start_frek), #bw
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_waterfall_sink_x_0.set_update_time(0.10)
        self.qtgui_waterfall_sink_x_0.enable_grid(False)
        self.qtgui_waterfall_sink_x_0.enable_axis_labels(True)



        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        colors = [0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_waterfall_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_waterfall_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_waterfall_sink_x_0.set_color_map(i, colors[i])
            self.qtgui_waterfall_sink_x_0.set_line_alpha(i, alphas[i])

        self.qtgui_waterfall_sink_x_0.set_intensity_range(-140, 10)

        self._qtgui_waterfall_sink_x_0_win = sip.wrapinstance(self.qtgui_waterfall_sink_x_0.qwidget(), Qt.QWidget)

        self.top_grid_layout.addWidget(self._qtgui_waterfall_sink_x_0_win, 0, 1, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.qtgui_freq_sink_x_1 = qtgui.freq_sink_c(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            ((start_frek+stop_frek)/2), #fc
            (stop_frek-start_frek), #bw
            'Sinyal Setelah Mixing (Monitoring hasil translasi ke baseband)', #name
            1,
            None # parent
        )
        self.qtgui_freq_sink_x_1.set_update_time(0.10)
        self.qtgui_freq_sink_x_1.set_y_axis((-140), 10)
        self.qtgui_freq_sink_x_1.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_x_1.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_x_1.enable_autoscale(False)
        self.qtgui_freq_sink_x_1.enable_grid(True)
        self.qtgui_freq_sink_x_1.set_fft_average(1.0)
        self.qtgui_freq_sink_x_1.enable_axis_labels(True)
        self.qtgui_freq_sink_x_1.enable_control_panel(True)
        self.qtgui_freq_sink_x_1.set_fft_window_normalized(False)



        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["red", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_x_1.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_x_1.set_line_label(i, labels[i])
            self.qtgui_freq_sink_x_1.set_line_width(i, widths[i])
            self.qtgui_freq_sink_x_1.set_line_color(i, colors[i])
            self.qtgui_freq_sink_x_1.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_x_1_win = sip.wrapinstance(self.qtgui_freq_sink_x_1.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_freq_sink_x_1_win, 0, 0, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.osmosdr_source_0 = osmosdr.source(
            args="numchan=" + str(1) + " " + 'hackrf=0'
        )
        self.osmosdr_source_0.set_time_unknown_pps(osmosdr.time_spec_t())
        self.osmosdr_source_0.set_sample_rate(8e6)
        self.osmosdr_source_0.set_center_freq(((start_frek+stop_frek)/2), 0)
        self.osmosdr_source_0.set_freq_corr(0, 0)
        self.osmosdr_source_0.set_dc_offset_mode(0, 0)
        self.osmosdr_source_0.set_iq_balance_mode(0, 0)
        self.osmosdr_source_0.set_gain_mode(False, 0)
        self.osmosdr_source_0.set_gain(10, 0)
        self.osmosdr_source_0.set_if_gain(32, 0)
        self.osmosdr_source_0.set_bb_gain(40, 0)
        self.osmosdr_source_0.set_antenna('', 0)
        self.osmosdr_source_0.set_bandwidth(0, 0)
        self.low_pass_filter_0 = filter.fir_filter_ccf(
            40,
            firdes.low_pass(
                1,
                samp_rate,
                75e3,
                25e3,
                window.WIN_HAMMING,
                6.76))
        self.blocks_multiply_xx_0 = blocks.multiply_vcc(1)
        self.blocks_multiply_const_vxx_3 = blocks.multiply_const_ff(1.0 if run_control else 0.0)
        self.blocks_multiply_const_vxx_2 = blocks.multiply_const_cc(1.0 if run_control else 0.0)
        self.blocks_multiply_const_vxx_1 = blocks.multiply_const_cc(1.0 if run_control else 0.0)
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_ff(audio_gain)
        self.audio_sink_0 = audio.sink(48000, '', True)
        self.analog_wfm_rcv_0 = analog.wfm_rcv(
        	quad_rate=48e4,
        	audio_decimation=10,
        )
        self.analog_sig_source_x_0 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, 1.4e6, 1, 0, 0)
        self._Bandwidth_tool_bar = Qt.QToolBar(self)
        self._Bandwidth_tool_bar.addWidget(Qt.QLabel("'Bandwidth'" + ": "))
        self._Bandwidth_line_edit = Qt.QLineEdit(str(self.Bandwidth))
        self._Bandwidth_tool_bar.addWidget(self._Bandwidth_line_edit)
        self._Bandwidth_line_edit.returnPressed.connect(
            lambda: self.set_Bandwidth(eng_notation.str_to_num(str(self._Bandwidth_line_edit.text()))))
        self.top_layout.addWidget(self._Bandwidth_tool_bar)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_multiply_xx_0, 1))
        self.connect((self.analog_wfm_rcv_0, 0), (self.blocks_multiply_const_vxx_3, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.audio_sink_0, 0))
        self.connect((self.blocks_multiply_const_vxx_1, 0), (self.qtgui_waterfall_sink_x_0, 0))
        self.connect((self.blocks_multiply_const_vxx_2, 0), (self.qtgui_freq_sink_x_1, 0))
        self.connect((self.blocks_multiply_const_vxx_3, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.blocks_multiply_xx_0, 0), (self.blocks_multiply_const_vxx_2, 0))
        self.connect((self.blocks_multiply_xx_0, 0), (self.low_pass_filter_0, 0))
        self.connect((self.low_pass_filter_0, 0), (self.rational_resampler_xxx_0, 0))
        self.connect((self.osmosdr_source_0, 0), (self.blocks_multiply_const_vxx_1, 0))
        self.connect((self.osmosdr_source_0, 0), (self.blocks_multiply_xx_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.analog_wfm_rcv_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "hakrf_multi_frequency")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_stop_frek(self):
        return self.stop_frek

    def set_stop_frek(self, stop_frek):
        self.stop_frek = stop_frek
        self.set_Bandwidth((self.stop_frek-self.start_frek))
        Qt.QMetaObject.invokeMethod(self._stop_frek_line_edit, "setText", Qt.Q_ARG("QString", eng_notation.num_to_str(self.stop_frek)))
        self.osmosdr_source_0.set_center_freq(((self.start_frek+self.stop_frek)/2), 0)
        self.qtgui_freq_sink_x_1.set_frequency_range(((self.start_frek+self.stop_frek)/2), (self.stop_frek-self.start_frek))
        self.qtgui_waterfall_sink_x_0.set_frequency_range(((self.start_frek+self.stop_frek)/2), (self.stop_frek-self.start_frek))

    def get_start_frek(self):
        return self.start_frek

    def set_start_frek(self, start_frek):
        self.start_frek = start_frek
        self.set_Bandwidth((self.stop_frek-self.start_frek))
        Qt.QMetaObject.invokeMethod(self._start_frek_line_edit, "setText", Qt.Q_ARG("QString", eng_notation.num_to_str(self.start_frek)))
        self.osmosdr_source_0.set_center_freq(((self.start_frek+self.stop_frek)/2), 0)
        self.qtgui_freq_sink_x_1.set_frequency_range(((self.start_frek+self.stop_frek)/2), (self.stop_frek-self.start_frek))
        self.qtgui_waterfall_sink_x_0.set_frequency_range(((self.start_frek+self.stop_frek)/2), (self.stop_frek-self.start_frek))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.analog_sig_source_x_0.set_sampling_freq(self.samp_rate)
        self.low_pass_filter_0.set_taps(firdes.low_pass(1, self.samp_rate, 75e3, 25e3, window.WIN_HAMMING, 6.76))

    def get_run_control(self):
        return self.run_control

    def set_run_control(self, run_control):
        self.run_control = run_control
        self.blocks_multiply_const_vxx_1.set_k(1.0 if self.run_control else 0.0)
        self.blocks_multiply_const_vxx_2.set_k(1.0 if self.run_control else 0.0)
        self.blocks_multiply_const_vxx_3.set_k(1.0 if self.run_control else 0.0)

    def get_channel_width(self):
        return self.channel_width

    def set_channel_width(self, channel_width):
        self.channel_width = channel_width

    def get_channel_freq(self):
        return self.channel_freq

    def set_channel_freq(self, channel_freq):
        self.channel_freq = channel_freq

    def get_center_freq(self):
        return self.center_freq

    def set_center_freq(self, center_freq):
        self.center_freq = center_freq

    def get_audio_gain(self):
        return self.audio_gain

    def set_audio_gain(self, audio_gain):
        self.audio_gain = audio_gain
        self.blocks_multiply_const_vxx_0.set_k(self.audio_gain)

    def get_Bandwidth(self):
        return self.Bandwidth

    def set_Bandwidth(self, Bandwidth):
        self.Bandwidth = Bandwidth
        Qt.QMetaObject.invokeMethod(self._Bandwidth_line_edit, "setText", Qt.Q_ARG("QString", eng_notation.num_to_str(self.Bandwidth)))




def main(top_block_cls=hakrf_multi_frequency, options=None):

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
