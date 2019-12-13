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
                "slew_rate":
                    bitdiff.describe(1, {"fast": f_fast, "slow": f_out}),
                "open_collector":
                    bitdiff.describe(1, {"on": f_oc, "off": f_out}),
            })
            if device_name.endswith("AS"):
                macrocell.update({
                    "low_power":
                        bitdiff.describe(1, {"on": f_lp, "off": f_out}),
                })
            if device_name.endswith("BE"):
                macrocell.update({
                    "pull_up":
                        bitdiff.describe(1, {"on": f_pu, "off": f_out}),
                    "schmitt_trigger":
                        bitdiff.describe(1, {"on": f_hyst, "off": f_out}),
                    "bus_keeper":
                        bitdiff.describe(1, {"on": f_pk, "off": f_pu}), # pk implies pu
                })
