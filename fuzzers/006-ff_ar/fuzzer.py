from util import database, toolchain, bitdiff


with database.transact() as db:
    for device_name, device in db.items():
        package, pinout = next(iter(device["pins"].items()))
        for macrocell_name, macrocell in device["macrocells"].items():
            def run(code):
                return toolchain.run(
                    f"module top(input CLK, AR, output Q); {code}; endmodule",
                    {
                        "CLK": pinout[device["clocks"]["1"]["pad"]],
                        "AR": pinout[device["clear"]["pad"]],
                        "Q": pinout[macrocell["pad"]],
                    },
                    f"{device_name}-{package}")

            f_dff   = run("DFF   x(.CLK(CLK), .D(1'b0), .Q(Q))")
            f_dffar = run("DFFAR x(.CLK(CLK), .AR(AR), .D(1'b0), .Q(Q))")

            macrocell.update({
                "async_reset":
                    bitdiff.describe(1, {"gclr": f_dffar, "pt3": f_dff})
            })
