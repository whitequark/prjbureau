from util import database, toolchain, bitdiff


with database.transact() as db:
    for device_name, device in db.items():
        package, pinout = next(iter(device["pins"].items()))
        for macrocell_name, macrocell in device["macrocells"].items():
            for other_macrocell_name, other_macrocell in device["macrocells"].items():
                if other_macrocell_name != macrocell_name:
                    break
            else:
                assert False

            def run(code):
                return toolchain.run(
                    f"module top(input CLK1, CLK2, OE1, CLR, I, output Q); "
                    f"{code} "
                    f"endmodule",
                    {
                        "CLK1": pinout[device["clocks"]["1"]["pad"]],
                        "CLK2": pinout[device["clocks"]["2"]["pad"]],
                        "OE1": pinout[device["enables"]["1"]["pad"]],
                        "CLR": pinout[device["clear"]["pad"]],
                        "I": pinout[other_macrocell["pad"]],
                        "Q": pinout[macrocell["pad"]],
                    },
                    f"{device_name}-{package}",
                    strategy={"xor_synthesis": "on"})

            # Took me a long time to find a netlist this pathological.
            f_sum = run(
                f"wire Y1, Y2, Y3, Y4, Y5; "
                f"AND2 a1(CLK1, CLK2, Y1); "
                f"AND2 a2(I, CLR, Y2); "
                f"OR2 o1(Y2, OE1, Y3); "
                f"XOR2 x1(Y1, Y3, Y5); "
                f"DFFAR d(Y1, Y1, Y5, Q); "
            )
            f_as = run(
                f"wire Y1, Y2, Y3, Y4, Y5; "
                f"AND2 a1(CLK1, CLK2, Y1); "
                f"AND2 a2(I, CLR, Y2); "
                f"XOR2 x1(Y1, Y2, Y5); "
                f"DFFARS d(Y1, Y1, OE1, Y5, Q); "
            )

            # PT5 can be either a part of the sum term, or serve as async set/output enable.
            macrocell.update({
                "pt5_mux":
                    bitdiff.describe(1, {"sum": f_sum, "as_oe": f_as}),
            })
