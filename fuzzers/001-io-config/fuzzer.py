from util import database, toolchain, bitdiff


with database.transact() as db:
    for device_name, device in db.items():
        package, pinout = next(iter(device["pins"].items()))
        for macrocell_name, macrocell in device["macrocells"].items():
            pad = macrocell["pad"]
            def run_out(options):
                verilog = "module top(output O); assign O = 1'b0; endmodule"
                return toolchain.run(verilog, {"O": pinout[pad]},
                                     f"{device_name}-{package}", options)

            f0_out = run_out([])
            f_slow = run_out(["-strategy", "output_fast", "off"])
            f_oc   = run_out(["-strategy", "open_collector", "on"])

            macrocell.update({
                "slow_fuse":
                    bitdiff.find_one(f0_out, f_slow),
                "open_collector_fuse":
                    bitdiff.find_one(f0_out, f_oc),
            })
