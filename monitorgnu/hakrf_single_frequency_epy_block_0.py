from gnuradio import gr
import pmt
import subprocess

class blk(gr.basic_block):
    def __init__(self):
        gr.basic_block.__init__(
            self,
            name="Run HackRF Sweep",
            in_sig=None,
            out_sig=None
        )
        self.message_port_register_in(pmt.intern("in"))
        self.set_msg_handler(pmt.intern("in"), self.handle_msg)

    def handle_msg(self, msg):
        print("▶ Tombol ditekan. Menjalankan hackrf_sweep...")
        try:
            output_path = "/home/raspi4b/sweep.csv"
            subprocess.run([
                "hackrf_sweep",
                "-f", "88:108",
                "-w", "2500",
                "-1",
                "-r", output_path
            ], check=True)
            print("✅ Sweep selesai. Hasil di:", output_path)
        except Exception as e:
            print("❌ Gagal menjalankan hackrf_sweep:", str(e))
