from util import database, toolchain, bitdiff


with database.transact() as db:
    for device_name, device in db.items():
        package, pinout = next(iter(device["pins"].items()))
        for macrocell_name, macrocell in device["macrocells"].items():
            def run(code):
                return toolchain.run(
                    f"module top(input CLK2, OE1, output Q); {code}; endmodule",
                    {
                        "CLK2": pinout[device["clocks"]["2"]["pad"]],
                        "OE1": pinout[device["enables"]["1"]["pad"]],
                        "Q": pinout[macrocell["pad"]],
                    },
                    f"{device_name}-{package}")

            f_mux_1   = run("DFF x(.CLK(1'b1), .D(1'b0), .Q(Q))")
            f_mux_pt4 = run("DFF x(.CLK(1'b0), .D(1'b0), .Q(Q))")

            # PT4 can be either a part of the sum term, or serve as clock/clock enable.
            macrocell.update({
                "pt4_mux":
                    bitdiff.describe(1, {"clk_ce": f_mux_pt4, "sum": f_mux_1}),
            })
