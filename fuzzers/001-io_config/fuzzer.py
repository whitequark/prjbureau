from util import database, toolchain, bitdiff


with database.transact() as db:
    for device_name, device in db.items():
        package, pinout = next(iter(device["pins"].items()))
        for macrocell_name, macrocell in device["macrocells"].items():
            def run(**kwargs):
                return toolchain.run(
                    f"module top(output O); assign O = 1'b0; endmodule",
                    {"O": pinout[macrocell["pad"]]},
                    f"{device_name}-{package}",
                    strategy=kwargs)

            f_out  = run()
            f_fast = run(output_fast="O")
            f_oc   = run(open_collector="O")
            if device_name.endswith("AS"):
                f_lp   = run(MC_power="O")
            if device_name.endswith("BE"):
                f_hyst = run(schmitt_trigger="O")
                f_pu   = run(pull_up="O")
                f_pk   = run(pin_keep="O")

            macrocell.update({
                "fast_output":
                    bitdiff.describe(1, {"on": f_fast, "off": f_out}),
                "open_collector":
                    bitdiff.describe(1, {"off": f_out, "on": f_oc}),
            })
            if device_name.endswith("AS"):
                macrocell.update({
                    "low_power":
                        bitdiff.describe(1, {"off": f_out, "on": f_lp}),
                })
            if device_name.endswith("BE"):
                macrocell.update({
                    "pull_up":
                        bitdiff.describe(1, {"off": f_out, "on": f_pu}),
                    "schmitt_trigger":
                        bitdiff.describe(1, {"off": f_out, "on": f_hyst}),
                    "bus_keeper":
                        bitdiff.describe(1, {"off": f_pu, "on": f_pk}), # pk implies pu
                })
