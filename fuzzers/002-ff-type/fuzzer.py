from util import database, toolchain, bitdiff


with database.transact() as db:
    for device_name, device in db.items():
        package, pinout = next(iter(device["pins"].items()))
        for macrocell_name, macrocell in device["macrocells"].items():
            def run(code):
                return toolchain.run(
                    f"module top(input CLK, output Q); {code}; endmodule",
                    {
                        "CLK": pinout[device["clocks"]["1"]["pad"]],
                        "Q": pinout[macrocell["pad"]],
                    },
                    f"{device_name}-{package}")

            f_dff   = run("DFF   x(.CLK(CLK), .D(1'b0), .Q(Q))")
            f_tff   = run("TFF   x(.CLK(CLK), .T(1'b0), .Q(Q))")
            f_latch = run("LATCH x(.EN(CLK),  .D(1'b0), .Q(Q))")

            macrocell.update({
                "ff_type": bitdiff.describe(2, {"dff": f_dff, "tff": f_tff, "latch": f_latch})
            })
