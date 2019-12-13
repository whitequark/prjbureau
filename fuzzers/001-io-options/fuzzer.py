from util import database, toolchain, bitdiff


with database.transact() as db:
    for device_name, device in db.items():
        package, pinout = next(iter(device["pins"].items()))
        for macrocell_name, macrocell in device["macrocells"].items():
            def run(options):
                return toolchain.run(
                    f"module top(output O); assign O = 1'b0; endmodule",
                    {
                        "O": pinout[macrocell["pad"]]
                    },
                    f"{device_name}-{package}", options)

            f_base = run([])
            f_slow = run(["-strategy", "output_fast", "off"])
            f_oc   = run(["-strategy", "open_collector", "on"])

            macrocell.update({
                "slow_fuse":
                    bitdiff.find_one(f_base, f_slow),
                "open_collector_fuse":
                    bitdiff.find_one(f_base, f_oc),
            })
