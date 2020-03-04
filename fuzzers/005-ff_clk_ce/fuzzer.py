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

            # Use CLK2 because it has the same bit pattern as the global clock mux default.
            f_pt4_clk = run("DFFE x(.CLK(OE1),  .CE(1'b1), .D(1'b0), .Q(Q))")
            f_pt4_ce  = run("DFFE x(.CLK(CLK2), .CE(OE1),  .D(1'b0), .Q(Q))")

            # If PT4 is not used in the sum term it can be routed to exactly one of clock or
            # clock enable. If it is routed to clock, clock enable is fixed at 1. If it is routed
            # to clock enable, clock is selected according to the global clock mux.

            # http://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-3614-CPLD-ATF15-Overview.pdf
            macrocell.update({
                "pt4_func":
                    bitdiff.describe(1, {"clk": f_pt4_clk, "ce": f_pt4_ce}),
            })