#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: am_transmitter
# GNU Radio version: 3.10.11.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from gnuradio import audio
from gnuradio import blocks
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import sip
import threading



class am_transmitter(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "am_transmitter", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("am_transmitter")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "am_transmitter")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.audio_samp_rate = audio_samp_rate = 44100
        self.volume = volume = 1
        self.upsample_factor = upsample_factor = 10
        self.samp_rate = samp_rate = 500e3
        self.low_pass_cutoff = low_pass_cutoff = audio_samp_rate/2
        self.intermediate_freq = intermediate_freq = 100e3
        self.carrier_freq = carrier_freq = 900e6
        self.audio_gain = audio_gain = 1
        self.antenna_gain = antenna_gain = 25

        ##################################################
        # Blocks
        ##################################################

        self._volume_range = qtgui.Range(0, 10, 0.05, 1, 200)
        self._volume_win = qtgui.RangeWidget(self._volume_range, self.set_volume, "volume", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._volume_win)
        self.tab = Qt.QTabWidget()
        self.tab_widget_0 = Qt.QWidget()
        self.tab_layout_0 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tab_widget_0)
        self.tab_grid_layout_0 = Qt.QGridLayout()
        self.tab_layout_0.addLayout(self.tab_grid_layout_0)
        self.tab.addTab(self.tab_widget_0, 'Audio')
        self.tab_widget_1 = Qt.QWidget()
        self.tab_layout_1 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tab_widget_1)
        self.tab_grid_layout_1 = Qt.QGridLayout()
        self.tab_layout_1.addLayout(self.tab_grid_layout_1)
        self.tab.addTab(self.tab_widget_1, 'Upsampled audio')
        self.tab_widget_2 = Qt.QWidget()
        self.tab_layout_2 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tab_widget_2)
        self.tab_grid_layout_2 = Qt.QGridLayout()
        self.tab_layout_2.addLayout(self.tab_grid_layout_2)
        self.tab.addTab(self.tab_widget_2, 'upsampled filtered audio')
        self.tab_widget_3 = Qt.QWidget()
        self.tab_layout_3 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.tab_widget_3)
        self.tab_grid_layout_3 = Qt.QGridLayout()
        self.tab_layout_3.addLayout(self.tab_grid_layout_3)
        self.tab.addTab(self.tab_widget_3, 'AM After Downsampling')
        self.top_layout.addWidget(self.tab)
        self._audio_gain_range = qtgui.Range(0.5, 1, 0.1, 1, 200)
        self._audio_gain_win = qtgui.RangeWidget(self._audio_gain_range, self.set_audio_gain, "audio_gain", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._audio_gain_win)
        self.rational_resampler_xxx_0_0 = filter.rational_resampler_fff(
                interpolation=44100,
                decimation=500000,
                taps=[],
                fractional_bw=0.4)
        self.rational_resampler_xxx_0 = filter.rational_resampler_fff(
                interpolation=500000,
                decimation=44100,
                taps=[],
                fractional_bw=0.4)
        self.qtgui_sink_x_0_0_0 = qtgui.sink_f(
            1024, #fftsize
            window.WIN_BLACKMAN_hARRIS, #wintype
            123e6, #fc
            500000, #bw
            "Upsampled Filtered Audio FFT (Hz)", #name
            True, #plotfreq
            True, #plotwaterfall
            True, #plottime
            True, #plotconst
            None # parent
        )
        self.qtgui_sink_x_0_0_0.set_update_time(1.0/10)
        self._qtgui_sink_x_0_0_0_win = sip.wrapinstance(self.qtgui_sink_x_0_0_0.qwidget(), Qt.QWidget)

        self.qtgui_sink_x_0_0_0.enable_rf_freq(False)

        self.tab_layout_2.addWidget(self._qtgui_sink_x_0_0_0_win)
        self.qtgui_sink_x_0_0_0.set_block_alias("upsampled_filtered_audio")
        self.qtgui_sink_x_0_0 = qtgui.sink_f(
            1024, #fftsize
            window.WIN_BLACKMAN_hARRIS, #wintype
            123e6, #fc
            samp_rate, #bw
            "Upsampled Audio FFT (Hz)", #name
            True, #plotfreq
            True, #plotwaterfall
            True, #plottime
            True, #plotconst
            None # parent
        )
        self.qtgui_sink_x_0_0.set_update_time(1.0/1)
        self._qtgui_sink_x_0_0_win = sip.wrapinstance(self.qtgui_sink_x_0_0.qwidget(), Qt.QWidget)

        self.qtgui_sink_x_0_0.enable_rf_freq(False)

        self.tab_layout_1.addWidget(self._qtgui_sink_x_0_0_win)
        self.qtgui_sink_x_0_0.set_block_alias("upsampled_audio")
        self.qtgui_sink_x_0 = qtgui.sink_f(
            1024, #fftsize
            window.WIN_BLACKMAN_hARRIS, #wintype
            123e6, #fc
            samp_rate, #bw
            "Audio FFT (Hz)", #name
            True, #plotfreq
            True, #plotwaterfall
            True, #plottime
            True, #plotconst
            None # parent
        )
        self.qtgui_sink_x_0.set_update_time(1.0/1)
        self._qtgui_sink_x_0_win = sip.wrapinstance(self.qtgui_sink_x_0.qwidget(), Qt.QWidget)

        self.qtgui_sink_x_0.enable_rf_freq(False)

        self.tab_layout_0.addWidget(self._qtgui_sink_x_0_win)
        self.qtgui_sink_x_0.set_block_alias("audio")
        self.low_pass_filter_0_0 = filter.interp_fir_filter_fff(
            1,
            firdes.low_pass(
                1,
                samp_rate,
                20e3,
                5000,
                window.WIN_HAMMING,
                6.76))
        self.low_pass_filter_0 = filter.interp_fir_filter_fff(
            1,
            firdes.low_pass(
                1,
                44100,
                18e3,
                2000,
                window.WIN_HAMMING,
                6.76))
        self.blocks_wavfile_source_0 = blocks.wavfile_source('C:\\Users\\User\\Downloads\\wwd.mp3juice.blog - Ricky Montgomery - Mr Loverman (Official Lyric Video) (320 KBps).wav', True)
        self.blocks_multiply_const_vxx_0_0 = blocks.multiply_const_ff(volume)
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_ff(audio_gain)
        self.audio_sink_1 = audio.sink(44100, '', True)
        self._antenna_gain_range = qtgui.Range(0, 50, 1, 25, 200)
        self._antenna_gain_win = qtgui.RangeWidget(self._antenna_gain_range, self.set_antenna_gain, "antenna_gain", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._antenna_gain_win)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.low_pass_filter_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.qtgui_sink_x_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.qtgui_sink_x_0_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0_0, 0), (self.audio_sink_1, 0))
        self.connect((self.blocks_wavfile_source_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.low_pass_filter_0, 0), (self.rational_resampler_xxx_0, 0))
        self.connect((self.low_pass_filter_0_0, 0), (self.qtgui_sink_x_0_0_0, 0))
        self.connect((self.low_pass_filter_0_0, 0), (self.rational_resampler_xxx_0_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.low_pass_filter_0_0, 0))
        self.connect((self.rational_resampler_xxx_0_0, 0), (self.blocks_multiply_const_vxx_0_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "am_transmitter")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_audio_samp_rate(self):
        return self.audio_samp_rate

    def set_audio_samp_rate(self, audio_samp_rate):
        self.audio_samp_rate = audio_samp_rate
        self.set_low_pass_cutoff(self.audio_samp_rate/2)

    def get_volume(self):
        return self.volume

    def set_volume(self, volume):
        self.volume = volume
        self.blocks_multiply_const_vxx_0_0.set_k(self.volume)

    def get_upsample_factor(self):
        return self.upsample_factor

    def set_upsample_factor(self, upsample_factor):
        self.upsample_factor = upsample_factor

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.low_pass_filter_0_0.set_taps(firdes.low_pass(1, self.samp_rate, 20e3, 5000, window.WIN_HAMMING, 6.76))
        self.qtgui_sink_x_0.set_frequency_range(123e6, self.samp_rate)
        self.qtgui_sink_x_0_0.set_frequency_range(123e6, self.samp_rate)

    def get_low_pass_cutoff(self):
        return self.low_pass_cutoff

    def set_low_pass_cutoff(self, low_pass_cutoff):
        self.low_pass_cutoff = low_pass_cutoff

    def get_intermediate_freq(self):
        return self.intermediate_freq

    def set_intermediate_freq(self, intermediate_freq):
        self.intermediate_freq = intermediate_freq

    def get_carrier_freq(self):
        return self.carrier_freq

    def set_carrier_freq(self, carrier_freq):
        self.carrier_freq = carrier_freq

    def get_audio_gain(self):
        return self.audio_gain

    def set_audio_gain(self, audio_gain):
        self.audio_gain = audio_gain
        self.blocks_multiply_const_vxx_0.set_k(self.audio_gain)

    def get_antenna_gain(self):
        return self.antenna_gain

    def set_antenna_gain(self, antenna_gain):
        self.antenna_gain = antenna_gain




def main(top_block_cls=am_transmitter, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()
    tb.flowgraph_started.set()

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
