from util import database, toolchain, bitdiff, progress


with database.transact() as db:
    for device_name, device in db.items():
        if not device_name.endswith('AS'):
            continue # only in AS
        else:
            progress(device_name)

        package, pinout = next(iter(device['pins'].items()))
        for macrocell_idx, (macrocell_name, macrocell) in enumerate(device['macrocells'].items()):
            progress(1)

            def run(code):
                return toolchain.run(
                    f"module top(input CLK1); "
                    f"wire Q, X, Y; OR2 o1(Q, X, Y); BUF b1(Y, X);"
                    f"{code} "
                    f"endmodule",
                    {
                        'CLK1': pinout[device['clocks']['1']['pad']],
                        'ff': str(601 + macrocell_idx),
                    },
                    f"{device_name}-{package}")

            f_off = run("DFF ff(1'b0, 1'b0, Q);")
            f_on  = run("DFF ff(1'b0, CLK1, Q);")

            # Datasheet describes two kinds of power management options: "reduced power" feature
            # (controllable in fitter using the MC_power strategy) and "power down" feature. For
            # the latter it mentions that "Unused product terms are automatically disabled by
            # the compiler to decrease power consumption."
            #
            # When powered down, the PTs output 0 only if all of their fuses are programmed as 0.
            # Otherwise the PTs with non-zero fuses will output fixed 1. It is not clear why.
            macrocell.update({
                'pt_power':
                    bitdiff.describe(1, {'off': f_off, 'on': f_on},
                        scope=range(*device['ranges']['macrocells']))
            })
