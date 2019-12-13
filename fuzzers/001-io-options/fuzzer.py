from util import database, toolchain, bitdiff


with database.transact() as db:
    for device_name, device in db.items():
        package, pinout = next(iter(device["pins"].items()))
        for macrocell_name, macrocell in device["macrocells"].items():
            def run(output_fast="off", open_collector="off"):
                return toolchain.run(
                    f"module top(output O); assign O = 1'b0; endmodule",
                    {
                        "O": pinout[macrocell["pad"]]
                    },
                    f"{device_name}-{package}",
                    [
                        "-strategy", "output_fast", output_fast,
                        "-strategy", "open_collector", open_collector,
                    ])

            f_base = run()
            f_fast = run(output_fast="on")
            f_oc   = run(open_collector="on")

            macrocell.update({
                "slew_rate":
                    bitdiff.describe(1, {"fast": f_fast, "slow": f_base}),
                "open_collector":
                    bitdiff.describe(1, {"on": f_oc, "off": f_base}),
            })
