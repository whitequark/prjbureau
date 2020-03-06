from util import database, toolchain, bitdiff


with database.transact() as db:
    for device_name, device in db.items():
        package, pinout = next(iter(device["pins"].items()))
        for macrocell_name, macrocell in device["macrocells"].items():
            def run(code):
                return toolchain.run(
                    f"module top(input CLK1, CLK2, OE1, CLR, output Q); "
                    f"wire Y1, Y2, Y3; "
                    f"AND2 a1(CLK1, CLK2, Y1); "
                    f"AND2 a2(CLK2, OE1, Y2); "
                    f"AND2 a3(OE1, CLR, Y3); "
                    f"{code} "
                    f"endmodule",
                    {
                        "CLK1": pinout[device["clocks"]["1"]["pad"]],
                        "CLK2": pinout[device["clocks"]["2"]["pad"]],
                        "OE1": pinout[device["enables"]["1"]["pad"]],
                        "CLR": pinout[device["clear"]["pad"]],
                        "Q": pinout[macrocell["pad"]],
                    },
                    f"{device_name}-{package}",
                    strategy={"xor_synthesis": "on"})

            f_sum = run("wire Y4; OR3 o1(Y2, Y1, Y3, Y4); DFF d(1'b0, Y4, Q);")
            f_ar  = run("wire Y4; OR2 o1(Y1, Y2, Y4); DFFAR d(1'b0, Y3, Y4, Q);")

            # PT3 can be either a part of the sum term, or serve as async reset.
            macrocell.update({
                "pt3_mux":
                    bitdiff.describe(1, {"ar": f_ar, "sum": f_sum}),
            })
